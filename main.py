import os
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import update
from database import AsyncSessionLocal
from models import Ticket
from image_utils import create_ticket
from email_utils import get_available_mailbox, send_ticket_email

load_dotenv()

app = FastAPI(title="JVLYN Ticketing API")

API_KEY = os.getenv("API_KEY")

class TicketItem(BaseModel):
    ticket_id: str
    ticket_type: str
    referral_code: Optional[str] = None

class OrderRequest(BaseModel):
    order_id: int
    buyer_name: str
    notelp: str
    buyer_email: str
    tickets: List[TicketItem]

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

async def process_tickets(order: OrderRequest):
    ticket_paths = []

    # 1. Generate images
    for t in order.tickets:
        path = create_ticket(
            order.buyer_name,
            order.buyer_email,
            order.order_id,
            t.ticket_id,
            t.ticket_type
        )
        ticket_paths.append(path)

    # 2. Update Database
    async with AsyncSessionLocal() as session:
        for t in order.tickets:
            await session.execute(
                update(Ticket)
                .where(Ticket.ticket_id == t.ticket_id)
                .values(ticket_status='active')
            )
        await session.commit()

    # 3. Select Mailbox and Send Email
    mailbox = await get_available_mailbox()
    if mailbox:
        success = await send_ticket_email(
            mailbox,
            order.buyer_email,
            ticket_paths,
            order.buyer_name,
            order.order_id
        )
        if not success:
             print(f"Failed to send email for order {order.order_id}")
    else:
        print(f"No available mailbox for order {order.order_id}")

    # 4. Cleanup temporary files
    for path in ticket_paths:
        if os.path.exists(path):
            os.remove(path)

    return True

@app.post("/api/tickets/generate", dependencies=[Depends(verify_api_key)])
async def generate_tickets(order: OrderRequest):
    # Strategy A: One Request, One Ticket (or small batches)
    # Process synchronously to prevent Vercel from freezing the background task
    await process_tickets(order)
    return {"status": "success", "message": "Tiket berhasil diproses dan dikirim"}

@app.get("/")
async def root():
    return {"message": "JVLYN Ticketing API is running"}
