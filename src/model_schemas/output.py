from typing import Literal

from pydantic import BaseModel, Field

class OutputState(BaseModel):
    """
        The final output of our agentic system.

        invoice_number: str
        processing_result: "SUCCESS" | "FAILURE", the binary decision of whether the invoice was processed successfully or not.
        processing_result_sublabel: "SUCCESS" | "STOCK MISMATCH OR ITEM OUT OF STOCK" | "NONEXISTENT ITEM" | "INVALID QUANTITATIVE FIELD" | "MISSING OR SUSPICIOUS FIELD(S)", the sublabel of the processing result.
        reason: str, the reason for the processing result.
        confidence: float, the confidence score of the processing result.
    """
    invoice_number: str
    vendor_name: str
    amount: float
    processing_result: Literal["SUCCESS", "FAILURE"]
    processing_result_sublabel: Literal["SUCCESS", "STOCK MISMATCH OR ITEM OUT OF STOCK", "NONEXISTENT ITEM", "INVALID QUANTITATIVE FIELD", "MISSING OR SUSPICIOUS FIELD(S)"]
    reason: str
    confidence: float = Field(..., ge=0, le=1)

class OutputStateGoldenDataset(OutputState):
    processing_result_sublabel: list[Literal["SUCCESS", "STOCK MISMATCH OR ITEM OUT OF STOCK", "STOCK MISMATCH OR ITEM OUT OF STOCK", "NONEXISTENT ITEM", "INVALID QUANTITATIVE FIELD", "MISSING OR SUSPICIOUS FIELD(S)"]] | Literal["SUCCESS", "STOCK MISMATCH OR ITEM OUT OF STOCK", "STOCK MISMATCH OR ITEM OUT OF STOCK", "NONEXISTENT ITEM", "INVALID QUANTITATIVE FIELD", "MISSING OR SUSPICIOUS FIELD(S)"]