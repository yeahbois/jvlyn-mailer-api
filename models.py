from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, Integer, Enum, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    buyer_name = Column(String(255), nullable=False)
    buyer_email = Column(String(255), nullable=False)
    buyer_phone = Column(String(50), nullable=False)
    payment_proof = Column(String(255), nullable=True)
    total_tickets = Column(Integer, default=1)
    order_status = Column(String(50), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MailboxCounter(Base):
    __tablename__ = "mailbox_counters"

    mailbox_email = Column(String(255), primary_key=True)
    current_usage = Column(Integer, default=0)
    last_reset = Column(Date, default=func.current_date())

class Ticket(Base):
    __tablename__ = "jvlyn_tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    ticket_type = Column(String(100))
    ticket_status = Column(Enum('pending_delivery', 'sent', 'failed'), default='pending_delivery', nullable=False)
    is_scanned = Column(Boolean, default=False)
    referral_code = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ticket_id = Column(String(100), unique=True)
