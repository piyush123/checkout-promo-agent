from google.adk.runners import Runner
from saf_sdk.adk import LangsmithSessionService, wrap
from app.agent import root_agent

agent = wrap(
    Runner(
        agent=root_agent,
        app_name="checkout-promo-agent",
        session_service=LangsmithSessionService(),
    )
)
