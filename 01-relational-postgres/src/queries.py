"""
Advanced PostgreSQL Queries Showcase
Demonstrating ACID transactions, Common Table Expressions (CTEs),
Window Functions, and Query Execution Planning (EXPLAIN ANALYZE).
"""

import logging
import psycopg2
from psycopg2 import extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def demo_acid_transaction(connection):
    """
    Demonstrates Atomicity & Isolation using PostgreSQL transactions.
    Transfers money between two accounts. If any step fails, the entire transaction rolls back.
    """
    logging.info("--- Demonstrating ACID Transaction (Money Transfer) ---")
    try:
        with connection:
            with connection.cursor() as cursor:
                # Debit Customer 1
                cursor.execute(
                    """
                    INSERT INTO transactions (customer_id, txn_type, txn_amount, transaction_date)
                    VALUES (%s, 'DEBIT', %s, CURRENT_TIMESTAMP);
                    """,
                    (1, 50.00),
                )

                # Credit Customer 2
                cursor.execute(
                    """
                    INSERT INTO transactions (customer_id, txn_type, txn_amount, transaction_date)
                    VALUES (%s, 'CREDIT', %s, CURRENT_TIMESTAMP);
                    """,
                    (2, 50.00),
                )
        logging.info("ACID transaction successfully committed.")
    except Exception as e:
        connection.rollback()
        logging.error(f"Transaction failed and was safely rolled back: {e}")


def demo_window_functions(connection):
    """
    Demonstrates Window Functions:
    - Running cumulative customer spending: SUM() OVER (PARTITION BY customer_id ORDER BY transaction_date)
    - Customer transaction rank by amount: DENSE_RANK() OVER (ORDER BY txn_amount DESC)
    """
    logging.info("--- Demonstrating Window Functions ---")
    query = """
    SELECT 
        txn_id,
        customer_id,
        txn_type,
        txn_amount,
        transaction_date,
        SUM(CASE WHEN UPPER(txn_type) = 'CREDIT' THEN txn_amount ELSE -txn_amount END) 
            OVER (PARTITION BY customer_id ORDER BY transaction_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_balance,
        DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY txn_amount DESC) as amount_rank
    FROM transactions
    ORDER BY customer_id, transaction_date;
    """
    with connection.cursor(cursor_factory=extras.DictCursor) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows[:6]:
            logging.info(
                f"Txn #{r['txn_id']} | Cust #{r['customer_id']} | Type: {r['txn_type']} | "
                f"Amt: ${r['txn_amount']} | Running Balance: ${r['running_balance']} | Rank: #{r['amount_rank']}"
            )


def demo_explain_plan(connection):
    """
    Demonstrates Query Optimization and Execution Plan inspection via EXPLAIN ANALYZE.
    Shows index scans vs sequential scans.
    """
    logging.info("--- Demonstrating EXPLAIN ANALYZE ---")
    query = """
    EXPLAIN ANALYZE
    SELECT c.first_name, c.last_name, COUNT(t.txn_id) AS total_txns
    FROM customer c
    JOIN transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= '2023-01-01'
    GROUP BY c.customer_id, c.first_name, c.last_name;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        plan_lines = cursor.fetchall()
        for line in plan_lines:
            logging.info(f"PLAN: {line[0]}")
