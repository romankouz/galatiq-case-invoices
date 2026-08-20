import argparse
import os
import sys
import json
from typing import Literal

from IPython.display import Image, display

from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, ToolMessage

from data.inventory import create_inventory_table, reset_inventory_table
from data.table_utils import table_exists, print_all_rows
from data.invoices import create_invoices_table, insert_invoice_to_db, reset_invoices_table


from src.agents.approver import approve_invoice
from src.agents.auditor import audit_invoice
from src.agents.data_consolidator import consolidate_data
from src.agents.data_ingestor import ingest_unstructured_file
from src.model_schemas.input import InputState
from src.model_schemas.invoice import InvoiceState
from src.model_schemas.output import OutputState
from src.model_schemas.overall import OverallState

from src.evals.golden_dataset_verification import evaluate_golden_dataset, get_golden_dataset_results

from src.tools.ingest_file import ingest_file
from src.tools.query_inventory import query_inventory
from src.constants.constants import INVOICES_DIR, RESULTS_DIR

AVAILABLE_TOOLS = [query_inventory]
TOOLS_BY_NAME = {tool.name: tool for tool in AVAILABLE_TOOLS}

def tool_node(state: OverallState) -> dict:
    """Performs the tool call"""

    result = []
    for tool_call in state.messages[-1].tool_calls:
        observation = TOOLS_BY_NAME[tool_call["name"]].invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}

def build_agent_graph():
    # Build workflow
    agent_builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)

    # Add nodes
    agent_builder.add_node("ingest_file", ingest_file)
    agent_builder.add_node("ingestor", ingest_unstructured_file)
    agent_builder.add_node("consolidator", consolidate_data)
    agent_builder.add_node("auditor", audit_invoice)
    agent_builder.add_node("tool_node", tool_node)
    agent_builder.add_node("approver", approve_invoice)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "ingest_file")
    agent_builder.add_conditional_edges(
        "ingest_file",
        router_after_ingest,
        {
            "structured": "consolidator",
            "unstructured": "ingestor",
            "none": "auditor"
        }
    )
    agent_builder.add_edge("ingestor", "consolidator")
    agent_builder.add_edge("consolidator", "auditor")
    agent_builder.add_conditional_edges(
        "auditor",
        router_after_audit,
        ["tool_node", "approver"]
    )
    agent_builder.add_edge("tool_node", "auditor")
    agent_builder.add_edge("approver", END)

    # Compile the agent
    agent = agent_builder.compile()
    return agent

def router_after_ingest(state: OverallState) -> Literal["structured", "unstructured", "none"]:
    return state.invoice_data_router()

def router_after_audit(state: OverallState) -> Literal["tool_node", "approver"]:
    if state.messages[-1].tool_calls:
        return "tool_node"
    else:
        return "approver"

def argument_parser(argv: list[str]) -> argparse.Namespace:
    """Defines the CLI interface and parses arguments."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Acme Corp Invoice Processing Solution",
    )
    parser.add_argument("--reset-invoices", action="store_true", default=False, help="Reset the invoices table")
    parser.add_argument("--reset-inventory", action="store_true", default=False, help="Reset the inventory table")
    parser.add_argument("--test-only", action="store_true", default=False, help="Only run the test suite")
    parser.add_argument("--invoice_path", type=str, default=None, help="Path to a single invoice file")
    return parser.parse_args(argv)

def mock_payment(vendor, amount):
    print(f"Paid {amount} to {vendor}")
    return {"status": "success"}

def mock_rejection(vendor, amount):
    print(f"Rejected {amount} from {vendor}")
    return {"status": "failure"}

def main():
    args = argument_parser(sys.argv[1:])

    if args.reset_inventory or not table_exists("inventory"):
        print("Resetting inventory table...")
        reset_inventory_table()
        print("Creating inventory table...")
        create_inventory_table()
        print("Inventory table created successfully.")

    # Always make sure the invoices table exists
    if args.reset_invoices or not table_exists("invoices"):
        print("Resetting invoices table...")
        reset_invoices_table()
        print("Creating invoices table...")
        create_invoices_table()
        print("Invoices table created successfully.")

    predictions = []

    if not args.test_only:
        # Build the agent graph
        agent = build_agent_graph()

        # ---------- Single Invoice Path Handling ----------
        if args.invoice_path:
            # Ensure the file exists
            invoice_path = args.invoice_path
            if not os.path.isfile(invoice_path):
                raise FileNotFoundError(
                    f"Invoice file '{invoice_path}' does not exist. Please provide a valid --invoice_path argument."
                )

            print(f"Processing invoice: {os.path.basename(invoice_path)}")
            processed_invoice = agent.invoke({"file_path": invoice_path})
            try:
                inv = OutputState(**processed_invoice)
                # DB insert here
                try:
                    insert_invoice_to_db(inv)
                except ValueError as ve:
                    print(ve)
                predictions.append(inv)
            except Exception as e:
                print(f"Failed to convert processed invoice to OutputState: {e}")
            print(processed_invoice)
            print("=" * 100)
        else:
            invoice_paths = [
                os.path.relpath(os.path.join(INVOICES_DIR, f), start=os.path.dirname(__file__))
                for f in os.listdir(INVOICES_DIR)
            ]
            for invoice_path in invoice_paths:
                print(f"Processing invoice: {os.path.basename(invoice_path)}")
                processed_invoice = agent.invoke({"file_path": invoice_path})
                try:
                    inv = OutputState(**processed_invoice)
                    # DB insert here
                    try:
                        insert_invoice_to_db(inv)
                    except ValueError as ve:
                        print(ve)
                        continue
                    predictions.append(inv)
                except Exception as e:
                    print(f"Failed to convert processed invoice to OutputState: {e}")
                print(processed_invoice)
                print("=" * 100)

        os.makedirs(RESULTS_DIR, exist_ok=True)
        predictions_path = os.path.join(RESULTS_DIR, "predictions.json")
        with open(predictions_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in predictions], f, indent=4)

    else:
        predictions_path = os.path.join(RESULTS_DIR, "predictions.json")
        if os.path.exists(predictions_path):
            with open(predictions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    try:
                        predictions.append(OutputState(**item))
                    except Exception as e:
                        print(f"Failed to parse prediction entry: {e}")

    for prediction in predictions:
        if prediction.processing_result == "SUCCESS":
            mock_payment(prediction.vendor_name, prediction.amount)
        else:
            mock_rejection(prediction.vendor_name, prediction.amount)

    # Golden Dataset Evaluation
    if not args.invoice_path:
        results = evaluate_golden_dataset(predictions)
        results_summary = get_golden_dataset_results(results)
        print(results_summary)
    else:
        print("Skipping golden dataset evaluation for single invoice path.")

if __name__ == "__main__":
    main()
