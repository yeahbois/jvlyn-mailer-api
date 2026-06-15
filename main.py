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

async def verify_cron_auth(request: Request):
    # Vercel Cron sends a specific header
    auth_header = request.headers.get("Authorization")
    cron_header = request.headers.get("X-Vercel-Cron")

    # Also allow API_KEY for manual testing
    api_key_header = request.headers.get("X-API-KEY")

    if not (cron_header or api_key_header == API_KEY or (auth_header and auth_header == f"Bearer {API_KEY}")):
        raise HTTPException(status_code=401, detail="Unauthorized")

async def process_single_order(session, order_id):
    # 1. Fetch Order and Tickets
    order_result = await session.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        return False

    tickets_result = await session.execute(select(Ticket).where(Ticket.order_id == order_id, Ticket.ticket_status == 'pending_delivery'))
    tickets = tickets_result.scalars().all()

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

        # 3. Select Mailbox and Send Email
        mailbox = await get_available_mailbox(count=len(tickets))
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
            else:
                # Mark as failed or leave for retry
                print(f"Failed to send email for order {order_id}")
                # Optional: update to 'failed' if retry limit exceeded
        else:
            print(f"No available mailbox for order {order_id}")

    finally:
        # 5. Cleanup temporary files
        for path in ticket_paths:
            if os.path.exists(path):
                os.remove(path)

    return True

@app.get("/api/cron/process-tickets", dependencies=[Depends(verify_cron_auth)])
async def cron_process_tickets():
    async with AsyncSessionLocal() as session:
        # 1. Get unique order_ids with pending tickets
        query = select(distinct(Ticket.order_id)).where(Ticket.ticket_status == 'pending_delivery').limit(2)
        result = await session.execute(query)
        order_ids = result.scalars().all()

        processed_count = 0
        for oid in order_ids:
            if await process_single_order(session, oid):
                processed_count += 1

    return {"status": "success", "processed_orders": processed_count}

@app.get("/")
async def root():
    return {"message": "JVLYN Ticketing API is running"}
