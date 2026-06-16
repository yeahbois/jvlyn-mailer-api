import os
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import update, select, distinct
from database import AsyncSessionLocal
from models import Ticket, Order
from image_utils import create_ticket
from email_utils import get_available_mailbox, send_ticket_email

load_dotenv()

app = FastAPI(title="JVLYN Ticketing API")

API_KEY = os.getenv("API_KEY")
CRON_SECRET = os.getenv("CRON_SECRET")

async def verify_cron_auth(request: Request):
    # Vercel Cron sends a specific header, but we should also verify a secret
    # to prevent spoofing
    auth_header = request.headers.get("Authorization")

    # Check for Bearer token (preferred for Vercel Cron with secret)
    # or the shared secret in Authorization header
    if auth_header and (auth_header == f"Bearer {CRON_SECRET}" or auth_header == f"Bearer {API_KEY}"):
        return

    # Fallback for manual testing via X-API-KEY
    api_key_header = request.headers.get("X-API-KEY")
    if api_key_header and api_key_header == API_KEY:
        return

    raise HTTPException(status_code=401, detail="Unauthorized")

async def process_single_order(session, order_id):
    # Fetch Order dan Tiket
    order_result = await session.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()

    # Validasi Ganda: Pastikan order ada DAN status pembayarannya wajib 'paid'
    if not order or order.order_status != 'paid':
        return False

    tickets_result = await session.execute(
        select(Ticket).where(Ticket.order_id == order_id, Ticket.ticket_status == 'pending_delivery')
    )
    tickets = tickets_result.scalars().all()

    # end

    if not tickets:
        return False

    ticket_paths = []
    try:
        # 2. Generate images
        for t in tickets:
            path = create_ticket(
                order.buyer_name,
                order.buyer_email,
                order.id,
                t.ticket_id,
                t.ticket_type
            )
            ticket_paths.append(path)

        # 3. Select Mailbox (1 email per order)
        # We find a mailbox with enough quota but don't increment yet
        # to ensure it's only counted if sending succeeds.
        mailbox = await get_available_mailbox()
        if mailbox:
            success = await send_ticket_email(
                mailbox,
                order.buyer_email,
                ticket_paths,
                order.buyer_name,
                order.id
            )
            if success:
                # 4. Update Database to 'sent'
                for t in tickets:
                    t.ticket_status = 'sent'
                await session.commit()
                return True
            else:
                # If send failed, we might want to decrement mailbox usage
                # but get_available_mailbox already committed the increment for safety
                # to prevent over-limit during parallel execution.
                # However, since Vercel Cron Hobby is serial, we can adjust.
                print(f"Failed to send email for order {order_id}")
        else:
            print(f"No available mailbox for order {order_id}")

    except Exception as e:
        print(f"Exception processing order {order_id}: {e}")
    finally:
        # 5. Cleanup temporary files
        for path in ticket_paths:
            if os.path.exists(path):
                os.remove(path)

    return False

@app.get("/api/cron/process-tickets", dependencies=[Depends(verify_cron_auth)])
async def cron_process_tickets():
    async with AsyncSessionLocal() as session:
        # Modifikasi query untuk menyaring berdasarkan status pembayaran order
        query = (
            select(distinct(Ticket.order_id))
            .join(Order, Ticket.order_id == Order.id)
            .where(Ticket.ticket_status == 'pending_delivery', Order.order_status == 'paid')
            .limit(2)
        )
        result = await session.execute(query)
        order_ids = result.scalars().all()
        # end salin

        processed_count = 0
        for oid in order_ids:
            if await process_single_order(session, oid):
                processed_count += 1

    return {"status": "success", "processed_orders": processed_count}

@app.get("/")
async def root():
    return {"message": "JVLYN Ticketing API is running"}

@app.get("/api/debug/env-check")
async def debug_env(request: Request):
    """Temporary debug: verify env vars are loaded in Vercel. Remove after confirming."""
    provided_key = request.headers.get("X-API-KEY") or ""
    if provided_key != API_KEY or not API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "API_KEY_set": API_KEY is not None,
        "API_KEY_length": len(API_KEY) if API_KEY else 0,
        "CRON_SECRET_set": CRON_SECRET is not None,
        "CRON_SECRET_length": len(CRON_SECRET) if CRON_SECRET else 0,
    }
