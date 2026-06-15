import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import date
from sqlalchemy import select, update
from models import MailboxCounter
from database import AsyncSessionLocal
from dotenv import load_dotenv

load_dotenv()

MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
MAIL_SERVER = os.getenv("MAIL_SERVER")

async def get_available_mailbox(count=1):
    async with AsyncSessionLocal() as session:
        today = date.today()

        # Reset counters for the new day
        await session.execute(
            update(MailboxCounter)
            .where(MailboxCounter.last_reset < today)
            .values(current_usage=0, last_reset=today)
        )
        await session.commit()

        # Select available mailbox with locking
        # Find mailbox that has enough quota left (current_usage + count <= 100)
        query = select(MailboxCounter).where(MailboxCounter.current_usage + count <= 100).order_by(MailboxCounter.current_usage.asc()).limit(1).with_for_update()
        result = await session.execute(query)
        mailbox = result.scalar_one_or_none()

        if not mailbox:
            return None

        email = mailbox.mailbox_email

        # Increment usage by the number of tickets sent
        mailbox.current_usage += count
        await session.commit()

        return email

async def send_ticket_email(sender_email, recipient_email, ticket_paths, buyer_name, order_id):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"Tiket JVLYN Anda - Pesanan #{order_id}"

    body = f"Halo {buyer_name},\n\nTerima kasih telah melakukan pembelian tiket. Berikut kami lampirkan tiket Anda dalam bentuk file gambar.\n\nSimpan tiket ini untuk scan di venue.\n\nSalam,\nTim JVLYN"
    msg.attach(MIMEText(body, 'plain'))

    for path in ticket_paths:
        if os.path.exists(path):
            with open(path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(path)}",
                )
                msg.attach(part)

    try:
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
            server.login(sender_email, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
