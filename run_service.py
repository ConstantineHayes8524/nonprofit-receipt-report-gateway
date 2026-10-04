"""Run the nonprofit workflow as a small JSON service."""

from fastapi import FastAPI

from nonprofit_service import DonationRequest, DonationResult, InfraiOpenAI, process_donation


app = FastAPI(title="Nonprofit receipt service")


@app.post("/donations/process", response_model=DonationResult)
def process(request: DonationRequest) -> DonationResult:
    return process_donation(request, InfraiOpenAI.from_environment())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
