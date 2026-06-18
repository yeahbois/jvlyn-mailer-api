import os
import aiosmtplib
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

async def get_available_mailbox():
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
        # Increment usage by 1 since we are sending 1 email (per order)
        query = select(MailboxCounter).where(MailboxCounter.current_usage < 100).order_by(MailboxCounter.current_usage.asc()).limit(1).with_for_update()
        result = await session.execute(query)
        mailbox = result.scalar_one_or_none()

        if not mailbox:
            return None

        email = mailbox.mailbox_email

        # Increment usage by 1 for the email about to be sent
        mailbox.current_usage += 1
        await session.commit()

        return email

async def send_ticket_email(sender_email, recipient_email, ticket_paths, buyer_name, order_id):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Bcc'] = sender_email  # Copy to sender's inbox for Thunderbird visibility
    msg['Subject'] = f"Tiket JVLYN Anda - Pesanan #{order_id}"

    body = f'''
💌 𝘿𝙚𝙖𝙧 {buyer_name},

Your tickets for 𝐉𝐕𝐋𝐘𝐍 𝐗 have been successfully reserved. Here are the details :

🎠 𝐄𝐕𝐄𝐍𝐓 𝐃𝐄𝐓𝐀𝐈𝐋𝐒
𝐉𝐕𝐋𝐘𝐍 𝐗
📅 Saturday, 18 July 2026
🕰️ 15.10 – 22.30 WIB

𝙎𝙚𝙩𝙞𝙖𝙥 𝙣𝙤𝙢𝙤𝙧 𝙩𝙞𝙠𝙚𝙩 𝙗𝙚𝙧𝙡𝙖𝙠𝙪 𝙪𝙣𝙩𝙪𝙠 𝙨𝙖𝙩𝙪 𝙥𝙚𝙣𝙜𝙪𝙣𝙟𝙪𝙣𝙜 𝙙𝙖𝙣 𝙗𝙚𝙧𝙨𝙞𝙛𝙖𝙩 𝙪𝙣𝙞𝙠.

🎫 𝐁𝐄𝐅𝐎𝐑𝐄 𝐘𝐎𝐔 𝐄𝐍𝐓𝐄𝐑
Please present this email at the 𝘄𝗿𝗶𝘀𝘁𝗯𝗮𝗻𝗱 𝗿𝗲𝗱𝗲𝗺𝗽𝘁𝗶𝗼𝗻 𝗯𝗼𝗼𝘁𝗵 upon arrival. Our crew will assist you with the check-in process.

📞 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐏𝐄𝐑𝐒𝐎𝐍
( 082123289829 - Arka )
( 081586297119 - Balqis)

Thank you for being part of 𝐉𝐕𝐋𝐘𝐍 𝐗. We truly appreciate your support and look forward to welcoming you on 18 July. We hope you enjoy the performances and have a memorable experience throughout the event.✨

— 𝐉𝐚𝐤𝐚𝐫𝐭𝐚 𝐅𝐞𝐬𝐭𝐢𝐯𝐚𝐥 𝐛𝐲 𝐓𝐡𝐚𝐦𝐫𝐢𝐧 𝐗
'''
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
        # Using aiosmtplib for non-blocking SMTP
        # Pass recipients explicitly so BCC to sender is actually delivered
        # Remove Bcc header from message so buyer can't see it
        del msg['Bcc']
        await aiosmtplib.send(
            msg,
            hostname=MAIL_SERVER,
            port=MAIL_PORT,
            username=sender_email,
            password=MAIL_PASSWORD,
            use_tls=(MAIL_PORT == 465),
            start_tls=(MAIL_PORT == 587),
            recipients=[recipient_email, sender_email],
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
