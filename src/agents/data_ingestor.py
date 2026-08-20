from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_xai import ChatXAI
from dotenv import load_dotenv

from src.model_schemas.invoice import InvoiceState
from src.model_schemas.overall import OverallState
from src.constants.system_prompts import UNSTRUCTURED_INGESTOR_PROMPT

load_dotenv()

def setup_unstructured_ingestor_agent() -> ChatXAI:

    unstructured_ingestor_agent = init_chat_model(
        "grok-4.20-0309-non-reasoning",
        model_provider="xai",
        temperature=0.0
    )
    unstructured_ingestor_agent = unstructured_ingestor_agent.with_structured_output(InvoiceState)
    return unstructured_ingestor_agent

def ingest_unstructured_file(file: OverallState) -> InvoiceState:
    print("UNSTRUCTURED INGESTOR AGENT ACTIVATED")
    unstructured_ingestor_agent = setup_unstructured_ingestor_agent()
    return unstructured_ingestor_agent.invoke(
        [SystemMessage(content=UNSTRUCTURED_INGESTOR_PROMPT), HumanMessage(content=file.temp_unstructured_text)]
    )
