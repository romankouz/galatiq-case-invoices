import json

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_xai import ChatXAI
from dotenv import load_dotenv

from src.model_schemas.invoice import InvoiceState
from src.model_schemas.overall import OverallState
from src.constants.system_prompts import CONSOLIDATOR_PROMPT

load_dotenv()

def setup_consolidator_agent() -> ChatXAI:

    consolidator_agent = init_chat_model(
        "grok-4.20-0309-non-reasoning",
        model_provider="xai",
        temperature=0.0
    )
    consolidator_agent = consolidator_agent.with_structured_output(InvoiceState)
    return consolidator_agent

def consolidate_data(file: OverallState) -> InvoiceState:
    print("CONSOLIDATOR AGENT ACTIVATED")
    consolidator_agent = setup_consolidator_agent()
    return consolidator_agent.invoke(
        [
            SystemMessage(content=CONSOLIDATOR_PROMPT),
            HumanMessage(
                content=json.dumps(
                    file.temp_structured_output,
                    indent=4,
                    default=str
                ),
                encoding="utf-8"
            )
        ]
    )
