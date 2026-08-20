from deepagents import create_deep_agent

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_xai import ChatXAI
from dotenv import load_dotenv

from src.model_schemas.invoice import InvoiceState
from src.model_schemas.output import OutputState
from src.model_schemas.overall import OverallState
from src.constants.system_prompts import AUDITOR_PROMPT
from src.tools.query_inventory import query_inventory

load_dotenv()

def setup_auditor_agent() -> ChatXAI:

    auditor_agent = init_chat_model(
        "grok-4.20-0309-non-reasoning",
        model_provider="xai",
        temperature=0.0
    )
    auditor_agent = auditor_agent.bind_tools([query_inventory])
    return auditor_agent

def audit_invoice(state: OverallState) -> dict:
    print("AUDITING AGENT ACTIVATED")
    auditor_agent = setup_auditor_agent()

    if not state.messages:
        messages = [
            SystemMessage(content=AUDITOR_PROMPT),
            HumanMessage(content=state.model_dump_json())
        ]
    else:
        messages = [
            SystemMessage(content=AUDITOR_PROMPT),
            HumanMessage(content=state.model_dump_json()),
            *state.messages
        ]

    response = auditor_agent.invoke(messages)

    if response.tool_calls:
        return {"messages": [response]}

    return {
        "messages": [response],
        "audit_summary": response.content
    }
