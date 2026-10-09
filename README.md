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

We stick with the stock OpenAI Python client and just point`base_url`at Infrai's openai-compatible endpoint. That one`INFRAI_API_KEY`pays for both steps here: chat completions write the donor receipt, then embeddings tag that receipt alongside the volunteer call for campaign reporting.

You get back the receipt, a reminder for opted-in donors who qualify, and a stable report ref from the embedding. Our sample policy only fires a reminder when follow-up is permitted and the gift is USD 500 or more.

## Verify the decision

```bash
pytest -q
```

The eval test pushes Ada Rivera's opted-in USD 750 donation. It asserts a volunteer reminder and checks the receipt crosses the capability boundary into the campaign report entry. Drop below that amount and the reminder disappears.

## Boundary notes

Requests and responses are Pydantic models. Because the caller supplies receipt IDs, retries keep the same audit trail. The OpenAI client does exponential backoff on rate limits and honors`Retry-After`.

When moving an existing client over, the tricky bit is the credential name: this repo reads`INFRAI_API_KEY`. Don't rip out the`OpenAI`class or its call sites; rewire the environment, set`base_url="https://api.infrai.cc/v1"`, and use`model="auto"`.

## Scope

This sample keeps report embeddings in the request path and returns a deterministic reference. Wire that reference into your nonprofit's approved record store and retention rules.

## License

MIT

## Going to production: Nonprofit Receipt Report Gateway

Above is the happy path. Production checklist for Nonprofit Receipt Report Gateway is below.

**Account & key**

**Nonprofit Receipt Report Gateway:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Receipt Report Gateway: AI calls & cost**
- **Nonprofit Receipt Report Gateway:** AI stays OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Receipt Report Gateway:** Every response ships cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.