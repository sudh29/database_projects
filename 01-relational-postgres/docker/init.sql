-- ============================================================================
-- PostgreSQL Module: Schema Initialization & Seed Data
-- ============================================================================

-- Create tables if not exists
CREATE TABLE IF NOT EXISTS customer (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    txn_type VARCHAR(10) NOT NULL CHECK (UPPER(txn_type) IN ('CREDIT', 'DEBIT')),
    txn_amount NUMERIC(12, 2) NOT NULL CHECK (txn_amount > 0),
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_date_trunc ON transactions(DATE(transaction_date));

-- Insert sample customers
INSERT INTO customer (customer_id, first_name, last_name, date_of_birth) VALUES
    (1, 'John', 'Doe', '2000-01-15 00:00:00+00'),      -- Age ~23 in Jan 2023
    (2, 'Alice', 'Smith', '2002-04-22 00:00:00+00'),    -- Age ~21 in Jan 2023
    (3, 'Bob', 'Johnson', '2002-09-05 00:00:00+00'),    -- Age ~20 in Jan 2023
    (4, 'Eva', 'Williams', '1998-07-12 00:00:00+00'),   -- Age ~24 in Jan 2023
    (5, 'Charlie', 'Brown', '1998-11-28 00:00:00+00'),  -- Age ~24 in Jan 2023
    (6, 'David', 'Miller', '1985-03-10 00:00:00+00')    -- Age ~38 in Jan 2023
ON CONFLICT (customer_id) DO NOTHING;

-- Reset identity sequence
SELECT setval('customer_customer_id_seq', (SELECT MAX(customer_id) FROM customer));

-- Insert sample transactions for 2023-01-15 (target test date)
INSERT INTO transactions (customer_id, txn_type, txn_amount, transaction_date) VALUES
    -- Customer 1: 500.50 credit, 300 debit => Net +200.50 (Age 23)
    (1, 'CREDIT', 500.50, '2023-01-15 09:30:00+00'),
    (1, 'DEBIT', 300.00, '2023-01-15 14:15:00+00'),

    -- Customer 2: 200.75 debit, 150.50 credit => Net -50.25 (Age 21)
    (2, 'DEBIT', 200.75, '2023-01-15 10:00:00+00'),
    (2, 'CREDIT', 150.50, '2023-01-15 16:45:00+00'),

    -- Customer 3: 100.25 credit => Net +100.25 (Age 20)
    (3, 'CREDIT', 100.25, '2023-01-15 11:20:00+00'),

    -- Customer 4: 250.00 credit => Net +250.00 (Age 24)
    (4, 'CREDIT', 250.00, '2023-01-15 12:00:00+00'),

    -- Customer 5: 150.00 credit => Net +150.00 (Age 24)
    -- Both Customer 4 & 5 are Age 24. Combined: 250 + 150 = 400. Avg customer saving = 400 / 2 = 200
    (5, 'CREDIT', 150.00, '2023-01-15 15:30:00+00'),

    -- Transactions on other dates (should NOT be included when filtering for 2023-01-15)
    (1, 'CREDIT', 1000.00, '2023-01-16 08:00:00+00'),
    (6, 'CREDIT', 750.00, '2023-01-14 18:00:00+00');
