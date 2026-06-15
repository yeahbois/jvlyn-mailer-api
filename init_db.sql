CREATE TABLE IF NOT EXISTS mailbox_counters (
    mailbox_email VARCHAR(255) PRIMARY KEY,
    current_usage INT DEFAULT 0,
    last_reset DATE DEFAULT (CURRENT_DATE)
);

CREATE TABLE IF NOT EXISTS jvlyn_tickets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    ticket_type VARCHAR(100),
    ticket_status VARCHAR(50) DEFAULT 'inactive',
    is_scanned BOOLEAN DEFAULT FALSE,
    referral_code VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ticket_id VARCHAR(100) UNIQUE
);

-- Insert initial mailboxes if they don't exist
INSERT IGNORE INTO mailbox_counters (mailbox_email, current_usage, last_reset) VALUES
('jvlynxticketing01@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing02@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing03@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing04@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing05@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing06@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing07@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing08@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing09@ospkmhthamrin.com', 0, CURRENT_DATE),
('jvlynxticketing10@ospkmhthamrin.com', 0, CURRENT_DATE);
