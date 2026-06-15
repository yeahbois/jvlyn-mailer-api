from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, Integer
from sqlalchemy.sql import func
from database import Base

class MailboxCounter(Base):
    __tablename__ = "mailbox_counters"

    mailbox_email = Column(String(255), primary_key=True)
    current_usage = Column(Integer, default=0)
    last_reset = Column(Date, default=func.current_date())

class Ticket(Base):
    __tablename__ = "jvlyn_tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, nullable=False)
    ticket_type = Column(String(100))
    ticket_status = Column(String(50), default='inactive')
    is_scanned = Column(Boolean, default=False)
    referral_code = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ticket_id = Column(String(100), unique=True) # Assuming ticket_id from JSON is the unique identifier like JVLYNVIPXXXXX
