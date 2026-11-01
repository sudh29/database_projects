"""
Unit Tests for Advanced PostgreSQL Queries & Connection Pool
Tests ACID transaction commit/rollback, window function queries,
query execution planning, and connection pooling without live database dependencies.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.queries import demo_acid_transaction, demo_window_functions, demo_explain_plan
from src.money_club_sol import get_connection_pool, get_db_connection


class TestPostgresQueriesAndPool(unittest.TestCase):
    def test_demo_acid_transaction_success(self):
        """Verify debit and credit execution and safe commit on success."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        demo_acid_transaction(mock_conn)

        # Should execute debit and credit inserts
        self.assertEqual(mock_cursor.execute.call_count, 2)
        debit_call = mock_cursor.execute.call_args_list[0]
        self.assertIn("DEBIT", debit_call[0][0])
        credit_call = mock_cursor.execute.call_args_list[1]
        self.assertIn("CREDIT", credit_call[0][0])
        mock_conn.rollback.assert_not_called()

    def test_demo_acid_transaction_rollback_on_error(self):
        """Verify transaction safely rolls back when query raises exception."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = RuntimeError("Database connection lost during debit")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        demo_acid_transaction(mock_conn)

        mock_conn.rollback.assert_called_once()

    def test_demo_window_functions_execution(self):
        """Verify window functions query runs and formats results."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "txn_id": 1,
                "customer_id": 101,
                "txn_type": "CREDIT",
                "txn_amount": 100.0,
                "running_balance": 100.0,
                "amount_rank": 1,
            }
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        demo_window_functions(mock_conn)

        mock_cursor.execute.assert_called_once()
        query_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("OVER (PARTITION BY customer_id", query_sql)
        self.assertIn("DENSE_RANK()", query_sql)

    def test_demo_explain_plan_execution(self):
        """Verify EXPLAIN ANALYZE query is submitted and parsed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Hash Aggregate  (cost=15.20..16.40 rows=10 width=40)",),
            ("  ->  Seq Scan on transactions  (cost=0.00..12.50 rows=100 width=16)",),
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        demo_explain_plan(mock_conn)

        mock_cursor.execute.assert_called_once()
        query_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("EXPLAIN ANALYZE", query_sql)

    def test_get_db_connection_context_manager_fallback(self):
        """Verify get_db_connection safely yields and closes direct connection if pool unavailable."""
        db_params = {
            "database": "test_db",
            "username": "user",
            "password": "pwd",
            "host": "localhost",
            "port": 5432,
        }
        with patch("src.money_club_sol.get_connection_pool", return_value=None):
            with patch("src.money_club_sol.connect_db") as mock_connect:
                mock_conn = MagicMock()
                mock_conn.closed = False
                mock_connect.return_value = mock_conn

                with get_db_connection(db_params) as conn:
                    self.assertEqual(conn, mock_conn)

                mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

