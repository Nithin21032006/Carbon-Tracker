import os
import pytest
from unittest.mock import MagicMock, patch

import receipt_scanner
import report

def test_dynamic_mock_items():
    # Test that different filenames yield deterministic, varying results
    items_a = receipt_scanner._get_mock_items("receipt_a.jpg")
    items_b = receipt_scanner._get_mock_items("receipt_b.jpg")
    
    # Assert they are deterministic
    assert items_a == receipt_scanner._get_mock_items("receipt_a.jpg")
    assert items_b == receipt_scanner._get_mock_items("receipt_b.jpg")
    
    # Assert they are dynamic (different receipts should usually return different items/counts)
    # With a pool of 12 items, different hashes will yield different lengths or names.
    assert (len(items_a) != len(items_b)) or (items_a[0]["name"] != items_b[0]["name"])


def test_receipt_scanner_missing_file():
    # Test that an invalid file path raises RuntimeError in extract_items_from_receipt
    with pytest.raises(RuntimeError) as exc_info:
        receipt_scanner.extract_items_from_receipt("non_existent_file.jpg")
    assert "Could not read uploaded file" in str(exc_info.value)


def test_report_rendering():
    # Test HTML rendering output structure
    mock_data = {
        "week_start": "Jun 14",
        "week_end": "Jun 20, 2026",
        "total_co2_kg": 15.5,
        "scans_count": 3,
        "category_totals": {"Produce": 5.0, "Meat & Fish": 10.5},
        "current_streak": 2,
        "longest_streak": 5,
        "challenges_completed_count": 1,
        "co2_saved_this_week": 2.0,
        "total_co2_saved_alltime": 10.0,
        "badges": [{"title": "First Receipt"}],
        "daily_totals": [{"date": "Mon", "co2": 5.0}, {"date": "Tue", "co2": 10.5}]
    }
    
    html = report.render_report_html(mock_data)
    assert "15.5" in html
    assert "Produce" in html
    assert "Meat & Fish" in html
    assert "🏅 First Receipt" in html


@patch("smtplib.SMTP")
def test_send_weekly_email_success(mock_smtp_class):
    # Setup mock SMTP server
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    # Setup temporary credentials in environment
    os.environ["EMAIL_HOST"] = "smtp.example.com"
    os.environ["EMAIL_PORT"] = "587"
    os.environ["EMAIL_USER"] = "test@example.com"
    os.environ["EMAIL_PASSWORD"] = "password123"
    
    try:
        # Trigger sending
        res = report.send_weekly_email("recipient@example.com")
        assert res["sent_to"] == "recipient@example.com"
        assert "weekly carbon report" in res["subject"]
        
        # Verify SMTP actions were triggered
        mock_smtp_class.assert_called_with("smtp.example.com", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_with("test@example.com", "password123")
        mock_smtp_instance.send_message.assert_called_once()
    finally:
        # Cleanup env
        del os.environ["EMAIL_HOST"]
        del os.environ["EMAIL_PORT"]
        del os.environ["EMAIL_USER"]
        del os.environ["EMAIL_PASSWORD"]


def test_send_weekly_email_missing_credentials():
    # Verify raises exception when credentials are not configured
    if "EMAIL_HOST" in os.environ:
        del os.environ["EMAIL_HOST"]
        
    with pytest.raises(RuntimeError) as exc_info:
        report.send_weekly_email("recipient@example.com")
    assert "Email sending isn't configured yet" in str(exc_info.value)
