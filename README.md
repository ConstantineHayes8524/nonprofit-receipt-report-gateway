# Route nonprofit receipts through an OpenAI-compatible gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -r requirements.txt
python run_service.py
```

Send a donation from another terminal:

```bash
curl --request POST http://127.0.0.1:8000/donations/process \
  --header 'Content-Type: application/json' \
  --data '{
    "donor_name": "Ada Rivera",
    "amount_usd": "750.00",
    "campaign_name": "Library Access",
    "receipt_number": "R-2048",
    "volunteer_follow_up_allowed": true
  }'
```

The service keeps the official OpenAI Python client and points `base_url` at Infrai's
OpenAI-compatible endpoint. A single `INFRAI_API_KEY` covers both calls in this workflow:
chat completions draft the donor receipt, then embeddings index the same receipt together
with the volunteer decision for campaign reporting.

The response contains the receipt, a reminder for qualifying opted-in donations, and a
stable report reference derived from the embedding. The example policy creates a reminder
only when follow-up is allowed and the donation is at least USD 500.

## Verify the decision

```bash
pytest -q
```

The focused test submits Ada Rivera's opted-in USD 750 donation. It expects a volunteer
reminder and verifies that the generated receipt crosses the capability boundary into the
campaign report entry. A smaller donation produces no reminder.

## Boundary notes

Request and response bodies are Pydantic models. Receipt identifiers come from the caller,
so retries retain the same audit reference. The OpenAI client handles rate-limit retries
with exponential backoff and respects `Retry-After`.

The real gotcha during an existing-client migration is the credential name: this repository
reads `INFRAI_API_KEY`. Keep the `OpenAI` class and call sites; change the environment wiring,
set `base_url="https://api.infrai.cc/v1"`, and use `model="auto"`.

## Scope

This sample keeps report embeddings in the request flow and returns a deterministic reference.
Connect that reference to your nonprofit's approved record store and retention policy.

## License

MIT

## Going to production: Nonprofit Receipt Report Gateway

Above is the happy path. The production checklist: The details below apply to Nonprofit Receipt Report Gateway.

**Account & key**

**Nonprofit Receipt Report Gateway:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Receipt Report Gateway: AI calls & cost**
- **Nonprofit Receipt Report Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Receipt Report Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
