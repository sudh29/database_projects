"""
Money Club Assessment Solution
Calculates daily average savings per customer grouped by age from PostgreSQL.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
try:
    import psycopg2
    from psycopg2 import extras
except ImportError:
    import types
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.connect = None
    extras = types.ModuleType("extras")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def connect_db(db_params: dict):
    """Establishes connection to PostgreSQL using provided credentials."""
    return psycopg2.connect(
        dbname=db_params["database"],
        user=db_params["username"],
        password=db_params["password"],
        host=db_params["host"],
        port=db_params.get("port", 5432),
    )


def close_connection(connection):
    """Safely closes connection if open."""
    if connection and not connection.closed:
        connection.close()
        logging.info("Connection closed.")


def calculate_age(date_of_birth, reference_date) -> int:
    """
    Calculates age from date_of_birth to reference_date and rounds to nearest integer.
    Handles timezone-aware and naive datetimes.
    """
    if isinstance(date_of_birth, str):
        date_of_birth = datetime.fromisoformat(date_of_birth.replace("Z", "+00:00"))
    if isinstance(reference_date, str):
        reference_date = datetime.fromisoformat(reference_date.replace("Z", "+00:00"))

    # Normalize timezones to prevent naive vs aware subtraction errors
    if date_of_birth.tzinfo is not None and reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=timezone.utc)
    elif date_of_birth.tzinfo is None and reference_date.tzinfo is not None:
        date_of_birth = date_of_birth.replace(tzinfo=timezone.utc)

    # Days in Gregorian year accounting for leap years
    delta_days = (reference_date - date_of_birth).total_seconds() / 86400.0
    age = delta_days / 365.2425
    return int(round(age))


def calculate_savings(events, context=None):
    """
    Candidate test specification function.
    Reads date from events payload, queries PostgreSQL for transactions on that date,
    calculates net customer savings (credit - debit), and groups by customer age.

    Returns:
        JSON string or dict:
        {
            "statusCode": 200,
            "data": { age: avg_saving }
        }
        or in case of error:
        {
            "statusCode": 400,
            "message": error_message
        }
    """
    connection = None
    try:
        # Step 1: Parse input payload (handles dict or JSON string)
        payload = json.loads(events) if isinstance(events, str) else events

        # Parse date supporting both spec format ('dd/mm/yyyy') and fallback ('yyyy-mm-dd')
        date_str = payload.get("date") or payload.get("target_date")
        if not date_str:
            raise ValueError("Missing 'date' or 'target_date' in payload")

        target_date = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                target_date = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue

        if not target_date:
            raise ValueError(f"Invalid date format for '{date_str}'. Expected 'dd/mm/yyyy' or 'YYYY-MM-DD'")

        # Step 2: Connect to PostgreSQL
        connection = psycopg2.connect(
            dbname=payload["database"],
            user=payload["username"],
            password=payload["password"],
            host=payload["host"],
            port=payload.get("port", 5432),
        )

        with connection.cursor() as cursor:
            # Query transactions on the target date (using date truncation to match timestamps)
            target_date_only = target_date.date()
            cursor.execute(
                """
                SELECT t.customer_id, t.txn_type, t.txn_amount, c.date_of_birth
                FROM transactions t
                JOIN customer c ON t.customer_id = c.customer_id
                WHERE t.transaction_date::date = %s
                """,
                (target_date_only,),
            )
            rows = cursor.fetchall()

        # Step 3: Compute net savings per customer (credit - debit)
        # Structure: customer_id -> {"net_savings": Decimal, "date_of_birth": datetime}
        customer_savings = {}
        for customer_id, txn_type, txn_amount, dob in rows:
            amount = Decimal(str(txn_amount))
            is_credit = str(txn_type).strip().upper() == "CREDIT"
            net = amount if is_credit else -amount

            if customer_id not in customer_savings:
                customer_savings[customer_id] = {
                    "net_savings": Decimal(0),
                    "date_of_birth": dob,
                }
            customer_savings[customer_id]["net_savings"] += net

        # Step 4: Group customer net savings by rounded age
        # Structure: age -> list of customer net savings
        age_groups = {}
        for customer_id, data in customer_savings.items():
            age = calculate_age(data["date_of_birth"], target_date)
            if age not in age_groups:
                age_groups[age] = []
            age_groups[age].append(data["net_savings"])

        # Step 5: Calculate average savings per age group (average over customers, rounded to nearest integer)
        response_data = {}
        for age in sorted(age_groups.keys()):
            savings_list = age_groups[age]
            avg_saving = sum(savings_list) / len(savings_list) if savings_list else Decimal(0)
            response_data[int(age)] = int(round(avg_saving))

        response_payload = {"statusCode": 200, "data": response_data}
        return response_payload

    except Exception as e:
        logging.error(f"Error executing calculate_savings: {e}")
        return {"statusCode": 400, "message": str(e)}
    finally:
        close_connection(connection)


def calculate_savings_sql_optimized(events, context=None):
    """
    High-performance alternative: Computes age and customer averages
    directly inside PostgreSQL via a Common Table Expression (CTE).
    """
    connection = None
    try:
        payload = json.loads(events) if isinstance(events, str) else events
        date_str = payload.get("date") or payload.get("target_date")

        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                target_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue

        connection = psycopg2.connect(
            dbname=payload["database"],
            user=payload["username"],
            password=payload["password"],
            host=payload["host"],
            port=payload.get("port", 5432),
        )

        query = """
        WITH customer_daily_savings AS (
            SELECT 
                t.customer_id,
                c.date_of_birth,
                SUM(CASE WHEN UPPER(t.txn_type) = 'CREDIT' THEN t.txn_amount ELSE -t.txn_amount END) AS net_savings
            FROM transactions t
            JOIN customer c ON t.customer_id = c.customer_id
            WHERE t.transaction_date::date = %s
            GROUP BY t.customer_id, c.date_of_birth
        )
        SELECT 
            ROUND(EXTRACT(YEAR FROM AGE(%s, date_of_birth)))::INT AS age,
            ROUND(AVG(net_savings))::INT AS avg_saving
        FROM customer_daily_savings
        GROUP BY age
        ORDER BY age;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (target_date, target_date))
            results = {row[0]: row[1] for row in cursor.fetchall()}

        return {"statusCode": 200, "data": results}
    except Exception as e:
        return {"statusCode": 400, "message": str(e)}
    finally:
        close_connection(connection)


def main():
    """Local demonstration runner."""
    sample_event = {
        "database": "postgres",
        "username": "postgres",
        "password": "password",
        "host": "localhost",
        "port": 5432,
        "date": "15/01/2023",
    }
    result = calculate_savings(sample_event)
    logging.info(f"Result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
