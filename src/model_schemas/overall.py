from typing import Annotated,Literal

from langgraph.graph.message import add_messages
from langchain.messages import AnyMessage

from src.model_schemas.input import InputState
from src.model_schemas.invoice import InvoiceState

class OverallState(InputState, InvoiceState):
    audit_summary: str | None = None
    messages: Annotated[list[AnyMessage], add_messages] = []
    temp_unstructured_text: str | None = None
    temp_structured_output: dict | None = None

    def invoice_data_router(self) -> Literal["structured", "unstructured", "none"]:
        if self.temp_structured_output is not None:
            return "structured"
        elif self.temp_unstructured_text is not None:
            return "unstructured"
        else:
            return "none"
