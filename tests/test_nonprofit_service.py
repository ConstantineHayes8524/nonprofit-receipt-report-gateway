from decimal import Decimal

from nonprofit_service import DonationRequest, process_donation


class RecordingGateway:
    def __init__(self) -> None:
        self.report_entry = ""

    def draft_receipt(self, donation: DonationRequest) -> str:
        return f"Receipt {donation.receipt_number} confirms USD {donation.amount_usd:.2f}."

    def embed_report_entry(self, entry: str) -> list[float]:
        self.report_entry = entry
        return [0.25, -0.5, 0.75]


def test_high_value_opted_in_donation_hands_receipt_to_campaign_report() -> None:
    gateway = RecordingGateway()
    donation = DonationRequest(
        donor_name="Ada Rivera",
        amount_usd=Decimal("750.00"),
        campaign_name="Library Access",
        receipt_number="R-2048",
        volunteer_follow_up_allowed=True,
    )

    result = process_donation(donation, gateway)

    assert result.volunteer_reminder == (
        "Thank Ada Rivera for receipt R-2048 and record the contact in Library Access."
    )
    assert result.receipt_text in gateway.report_entry
    assert "volunteer_reminder=Thank Ada Rivera" in gateway.report_entry
    assert result.campaign_report_ref.startswith("Library Access:")


def test_follow_up_requires_consent_and_threshold() -> None:
    gateway = RecordingGateway()
    donation = DonationRequest(
        donor_name="Sam Lee",
        amount_usd=Decimal("75.00"),
        campaign_name="Meal Fund",
        receipt_number="R-2049",
        volunteer_follow_up_allowed=True,
    )

    result = process_donation(donation, gateway)

    assert result.volunteer_reminder is None
    assert "volunteer_reminder=none" in gateway.report_entry
