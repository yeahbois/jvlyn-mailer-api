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

    if not order:
        return {"ok": False, "reason": "order_not_found"}
    if order.order_status != 'paid':
        return {"ok": False, "reason": f"order_status_is_{order.order_status}"}

    tickets_result = await session.execute(
        select(Ticket).where(Ticket.order_id == order_id, Ticket.ticket_status == 'pending_delivery')
    )
    tickets = tickets_result.scalars().all()

    if not tickets:
        return {"ok": False, "reason": "no_pending_tickets"}

    ticket_paths = []
    try:
        # Generate ticket images
        for t in tickets:
            path = create_ticket(
                order.buyer_name,
                order.buyer_email,
                order.id,
                t.ticket_id,
                t.ticket_type
            )
            ticket_paths.append(path)

        # Select available mailbox
        mailbox = await get_available_mailbox()
        if not mailbox:
            return {"ok": False, "reason": "no_available_mailbox"}

        success = await send_ticket_email(
            mailbox,
            order.buyer_email,
            ticket_paths,
            order.buyer_name,
            order.id
        )
        if success:
            for t in tickets:
                t.ticket_status = 'sent'
            await session.commit()
            return {"ok": True, "reason": "sent", "mailbox": mailbox, "tickets_sent": len(tickets)}
        else:
            return {"ok": False, "reason": "smtp_send_failed", "mailbox": mailbox}

    except Exception as e:
        return {"ok": False, "reason": f"exception: {str(e)}"}
    finally:
        for path in ticket_paths:
            if os.path.exists(path):
                os.remove(path)

@app.get("/api/cron/process-tickets", dependencies=[Depends(verify_cron_auth)])
async def cron_process_tickets():
    async with AsyncSessionLocal() as session:
        query = (
            select(distinct(Ticket.order_id))
            .join(Order, Ticket.order_id == Order.id)
            .where(Ticket.ticket_status == 'pending_delivery', Order.order_status == 'paid')
            .limit(10)
        )
        result = await session.execute(query)
        order_ids = result.scalars().all()

        results = []
        for oid in order_ids:
            outcome = await process_single_order(session, oid)
            results.append({"order_id": oid, **outcome})

        processed_count = sum(1 for r in results if r.get("ok"))

    return {
        "status": "success",
        "found_orders": len(order_ids),
        "processed_orders": processed_count,
        "details": results
    }

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
