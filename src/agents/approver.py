from deepagents import create_deep_agent

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_xai import ChatXAI
from dotenv import load_dotenv

from src.model_schemas.overall import OverallState
from src.model_schemas.output import OutputState
from src.constants.system_prompts import APPROVER_PROMPT
from src.tools.query_inventory import query_inventory

load_dotenv()

def setup_approver_agent() -> ChatXAI:

    approver_agent = init_chat_model(
        "grok-4.20-0309-non-reasoning",
        model_provider="xai",
        temperature=0.0
    )
    approver_agent = approver_agent.with_structured_output(OutputState)
    return approver_agent

def approve_invoice(invoice: OverallState) -> OutputState:
    print("APPROVING AGENT ACTIVATED")
    approver_agent = setup_approver_agent()
    return approver_agent.invoke(
        [
            SystemMessage(content=APPROVER_PROMPT), 
            HumanMessage(
            content=f"""
                Invoice:
                {invoice.model_dump_json()}

                Auditor findings:
                {invoice.audit_summary}
                """
            )
        ]
    )
