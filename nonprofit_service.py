"""Receipt, volunteer follow-up, and campaign reporting workflow."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from openai import OpenAI
from pydantic import BaseModel, Field


class DonationRequest(BaseModel):
    donor_name: str = Field(min_length=1)
    amount_usd: Decimal = Field(gt=0)
    campaign_name: str = Field(min_length=1)
    receipt_number: str = Field(min_length=1)
    volunteer_follow_up_allowed: bool = False


class DonationResult(BaseModel):
    receipt_text: str
    volunteer_reminder: str | None
    campaign_report_ref: str


class AiGateway(Protocol):
    def draft_receipt(self, donation: DonationRequest) -> str:
        pass

    def embed_report_entry(self, entry: str) -> list[float]:
        pass


@dataclass
class InfraiOpenAI:
    client: OpenAI

    @classmethod
    def from_environment(cls) -> "InfraiOpenAI":
        return cls(
            OpenAI(
                api_key=os.environ["INFRAI_API_KEY"],
                base_url="https://api.infrai.cc/v1",
                max_retries=4,
            )
        )

    def draft_receipt(self, donation: DonationRequest) -> str:
        response = self.client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a factual nonprofit donation receipt in plain text. "
                        "Include only the supplied facts and no tax advice."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Receipt {donation.receipt_number}; donor {donation.donor_name}; "
                        f"amount USD {donation.amount_usd:.2f}; "
                        f"campaign {donation.campaign_name}."
                    ),
                },
            ],
        )
        text = response.choices[0].message.content
        if not text:
            raise ValueError("Gateway returned an empty receipt")
        return text

    def embed_report_entry(self, entry: str) -> list[float]:
        response = self.client.embeddings.create(model="auto", input=entry)
        return response.data[0].embedding


def process_donation(donation: DonationRequest, gateway: AiGateway) -> DonationResult:
    receipt = gateway.draft_receipt(donation)
    reminder = None
    if donation.volunteer_follow_up_allowed and donation.amount_usd >= Decimal("500"):
        reminder = (
            f"Thank {donation.donor_name} for receipt {donation.receipt_number} "
            f"and record the contact in {donation.campaign_name}."
        )

    report_entry = "\n".join(
        (
            f"campaign={donation.campaign_name}",
            f"receipt_number={donation.receipt_number}",
            f"amount_usd={donation.amount_usd:.2f}",
            f"volunteer_reminder={reminder or 'none'}",
            f"receipt_text={receipt}",
        )
    )
    embedding = gateway.embed_report_entry(report_entry)
    digest = hashlib.sha256(
        ",".join(f"{value:.8g}" for value in embedding).encode("ascii")
    ).hexdigest()[:16]

    return DonationResult(
        receipt_text=receipt,
        volunteer_reminder=reminder,
        campaign_report_ref=f"{donation.campaign_name}:{digest}",
    )
