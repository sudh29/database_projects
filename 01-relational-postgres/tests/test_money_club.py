"""
Unit and Integration Tests for Money Club Solution
Supports both `pytest` and standard library `python3 -m unittest`.
Tests age calculation, business logic math, date parsing, and DB error handling.
"""

from datetime import datetime, timezone
from decimal import Decimal
import unittest
from unittest.mock import MagicMock, patch

from src.money_club_sol import calculate_age, calculate_savings


class TestMoneyClubSolution(unittest.TestCase):
    # ========================================================================
    # Age Calculation Tests
    # ========================================================================
    def test_calculate_age_exact(self):
        dob = datetime(2000, 1, 15, tzinfo=timezone.utc)
        ref = datetime(2023, 1, 15, tzinfo=timezone.utc)
        self.assertEqual(calculate_age(dob, ref), 23)

    def test_calculate_age_rounding_up(self):
        # Born Jan 15, 2000. On Dec 20, 2022 (approx 22.93 years old), should round up to 23
        dob = datetime(2000, 1, 15)
        ref = datetime(2022, 12, 20)
        self.assertEqual(calculate_age(dob, ref), 23)

    def test_calculate_age_rounding_down(self):
        # Born Jan 15, 2000. On Feb 1, 2022 (approx 22.04 years old), should round down to 22
        dob = datetime(2000, 1, 15)
        ref = datetime(2022, 2, 1)
        self.assertEqual(calculate_age(dob, ref), 22)

    def test_calculate_age_timezone_awareness_mix(self):
        # Mixing timezone-aware and naive datetimes should not raise TypeError
        dob = datetime(2000, 1, 15, tzinfo=timezone.utc)
        ref = datetime(2023, 1, 15)
        self.assertEqual(calculate_age(dob, ref), 23)

    # ========================================================================
    # Savings Business Logic & Customer Averaging Tests
    # ========================================================================
    @patch("src.money_club_sol.psycopg2.connect")
    def test_calculate_savings_averages_customers_not_transactions(self, mock_connect):
        """
        Critical Test:
        Ensures that when 2 customers of the same age transact, the average is calculated
        over the 2 customers, NOT over the count of transactions.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Scenario: Target date 2023-01-15
        # Customer 4 (Born 1998-07-12 -> Age 24): 1 transaction of $250 CREDIT => net 250
        # Customer 5 (Born 1998-11-28 -> Age 24): 3 transactions:
        #   $100 CREDIT, $100 CREDIT, $50 DEBIT => net 150 across 3 transactions
        # Total age group savings = 250 + 150 = 400
        # True customer average: 400 / 2 customers = 200
        # (The original bugged code divided 400 by 4 transactions = 100!)
        mock_cursor.fetchall.return_value = [
            (4, "CREDIT", Decimal("250.00"), datetime(1998, 10, 1, tzinfo=timezone.utc)),
            (5, "CREDIT", Decimal("100.00"), datetime(1998, 11, 28, tzinfo=timezone.utc)),
            (5, "CREDIT", Decimal("100.00"), datetime(1998, 11, 28, tzinfo=timezone.utc)),
            (5, "DEBIT", Decimal("50.00"), datetime(1998, 11, 28, tzinfo=timezone.utc)),
        ]

        event = {
            "database": "postgres",
            "username": "postgres",
            "password": "password",
            "host": "localhost",
            "port": 5432,
            "date": "15/01/2023",
        }

        response = calculate_savings(event)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn(24, response["data"])
        self.assertEqual(response["data"][24], 200)

    @patch("src.money_club_sol.psycopg2.connect")
    def test_calculate_savings_supports_json_string_input(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            (1, "CREDIT", Decimal("500.00"), datetime(2000, 1, 15, tzinfo=timezone.utc)),
        ]

        json_str = """{
            "database": "postgres",
            "username": "postgres",
            "password": "password",
            "host": "localhost",
            "port": 5432,
            "date": "15/01/2023"
        }"""

        response = calculate_savings(json_str)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["data"][23], 500)

    def test_calculate_savings_handles_invalid_date(self):
        event = {
            "database": "postgres",
            "username": "postgres",
            "password": "password",
            "host": "localhost",
            "date": "invalid-date",
        }
        response = calculate_savings(event)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid date format", response["message"])


if __name__ == "__main__":
    unittest.main()
