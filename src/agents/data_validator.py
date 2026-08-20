from langchain.agents import create_agent
from langchain_xai import ChatXAI

from data.model_schemas.invoice import Invoice

# add arguments later
DATA_INGESTOR_AGENT = create_agent(
    model=ChatXAI(model="grok-beta"),
    response_format=Invoice,
    tools=[],
)

