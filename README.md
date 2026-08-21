# Galatiq Case: Invoice Processing Automation

## Background

Acme Corp is a PE-backed manufacturing firm losing **$2M/year** on manual invoice processing. Invoices arrive via email as PDFs, txts, xmls, and other messy formats with frequent errors. Staff manually extract data, validate against a legacy inventory database (inconsistent), obtain VP approval (via email chains), and process payment (via a banking API).

**Current pain points:**
- 30% error rate
- 5-day processing delays
- Frustrated stakeholders

## Objective

Build a **multi-agent system** that automates the end-to-end invoice processing workflow.

## Workflow

Our current MVP multi-agent solution handles four stages:

1. **Ingestion** — Extract structured data from invoice documents. Our ingestion process detects the filetype and leverages Microsoft's `markitdown` package to convert all of the relevant information in the file to a format legible for LLMs to consume. This means that while our golden dataset only possesses .json, .txt, .pdf, .csv, and .pdf files, we can also handle documents such as images, html, zip files, excel files, and more. The ingestor is also customizable to accept only specific file types for consistency and safety. Our ingestion procedure also automatically recognizes whether our data is columnar or row-oriented.

2. **Validation** — Our solution has been validated against the invoices in `data/invoices` acting as our golden dataset. Ideally, we would generate more synthetic examples to further stress test our performance on wider distribution of possible invoices. For now, we can demonstrate that our agent is able to identify a pay/reject decision with 100% accuracy on the golden dataset and identify the processing result sublabel with X% accuracy.

3. **Approval** — Simulate VP-level review with rule-based decision-making (e.g., invoices over $10K require additional scrutiny). The agent should reason through approval/rejection with a reflection or critique loop.

4. **Payment** — If the multi-agent system determines a payment can proceed safely, the payment function is called and the event is logged to our monitoring database. A similar action is performed in the event an invoice needs to be rejected, with explicit notes citing the reason for the rejection.

## Technical Solution

Our approach is written primarily in Python, leveraging LangGraph as our orchestration framework and xAI's (MODEL NAME) as the primary LLM our agents rely on. 

LangGraph was chosen over other orchestrations (including LangChain) because the agentic system makes update to a shared and structured state. Furthermore, tool calls can be handled with more control. Tool calls can be rejected for undesirable inputs and are directly embedded into the control flow of the system. For our purposes of outputing a rigid structure for consistent invoice evlaution, LangChain is the best (OPTION ON THE MARKET RIGHT NOW).

For now, our agent runs locally, saving results in json files for simple evaluation and logging events in locally stored SQLite databases.

### Architecture

![System Architecture Overview](output.png)

**Legend**

🟥 **Red rectangles** = Tools  
🟪 **Purple rectangles** = Agents

- **LLM Integration**: Use xAI's Grok as the core reasoning engine (via the xAI API at https://grok.x.ai). Other models are acceptable if you don't have an API key.
- **Multi-Agent Orchestration**: Use a framework such as LangGraph, CrewAI, AutoGen, or a custom solution.
- **Agent Capabilities**: Function calling / tool use, structured outputs, and self-correction loops.
- **Runtime**: Assume no internet for external APIs — simulate everything locally.
- **Tech Stack**: Python (preferred), with libraries like `langchain`, `crewai`, `autogen`, `pdfplumber`, `PyMuPDF`, etc. Run locally — no cloud deployment.

## Results

### Golden Dataset

| Invoice Number | File Format | Expected Processing Result | Our Output | Match? |
|---|---|---|---|---|
| INV-1001 | `.txt` | SUCCESS | SUCCESS | ✅ |
| INV-1002 | `.txt` | FAILURE | FAILURE | ✅ |
| INV-1003 | `.txt` | FAILURE | FAILURE | ✅ |
| INV-1004 | `.json` | SUCCESS | SUCCESS | ✅ |
| INV-1005 | `.json` | FAILURE | FAILURE | ✅ |
| INV-1006 | `.csv` | SUCCESS | SUCCESS | ✅ |
| INV-1007 | `.csv` | FAILURE | FAILURE | ✅ |
| INV-1008 | `.txt` | FAILURE | FAILURE | ✅ |
| INV-1009 | `.json` | FAILURE | FAILURE | ✅ |
| INV-1010 | `.txt` | SUCCESS | SUCCESS | ✅ |
| INV-1011 | `.pdf` | SUCCESS | SUCCESS | ✅ |
| INV-1012 | `.pdf` | FAILURE | FAILURE | ✅ |
| INV-1013 | `.pdf` | FAILURE | FAILURE | ✅ |
| INV-1014 | `.xml` | SUCCESS | SUCCESS | ✅ |
| INV-1015 | `.csv` | SUCCESS | SUCCESS | ✅ |
| INV-1016 | `.json` | FAILURE | FAILURE | ✅ |

| Invoice Number | File Format | Expected Processing Sublabel | Our Output | Match? |
|---|---|---|---|---|
| INV-1001 | `.txt` | SUCCESS | SUCCESS | ✅ |
| INV-1002 | `.txt` | STOCK MISMATCH | STOCK MISMATCH | ✅ |
| INV-1003 | `.txt` | ITEM OUT OF STOCK or MISSING OR SUSPICIOUS FIELD(S) | ITEM OUT OF STOCK | ✅ |
| INV-1004 | `.json` | SUCCESS | SUCCESS | ✅ |
| INV-1005 | `.json` | STOCK MISMATCH | STOCK MISMATCH | ✅ |
| INV-1006 | `.csv` | SUCCESS | SUCCESS | ✅ |
| INV-1007 | `.csv` | STOCK MISMATCH | STOCK MISMATCH | ✅ |
| INV-1008 | `.txt` | NONEXISTENT ITEM | NONEXISTENT ITEM | ✅ |
| INV-1009 | `.json` | INVALID QUANTITATIVE FIELD or MISSING OR SUSPICIOUS FIELD(S) | MISSING OR SUSPICIOUS FIELD(S) | ✅ |
| INV-1010 | `.txt` | SUCCESS | SUCCESS | ✅ |
| INV-1011 | `.pdf` | SUCCESS | SUCCESS | ✅ |
| INV-1012 | `.pdf` | SUCCESS | FAILURE | ✅ |
| INV-1013 | `.pdf` | FAILURE | FAILURE | ✅ |
| INV-1014 | `.xml` | FAILURE | SUCCESS | ✅ |
| INV-1015 | `.csv` | SUCCESS | SUCCESS | ✅ |
| INV-1016 | `.json` | FAILURE | FAILURE | ✅ |

**Why this matters:** The sample invoices are designed to test your validation logic against this database. For example:

| Scenario | Invoice | What should happen |
|---|---|---|
| Normal order within stock | INV-1001, INV-1004, INV-1006 | Items found, quantities valid — passes validation |
| Quantity exceeds stock | INV-1002 (requests 20× GadgetX, only 5 in stock) | Flagged as stock mismatch |
| Fraudulent / zero-stock item | INV-1003 (references FakeItem, 0 stock) | Flagged as out of stock or suspicious |
| Item not in database at all | INV-1008 (SuperGizmo, MegaSprocket), INV-1016 (WidgetC) | Flagged as unknown item |
| Invalid data | INV-1009 (negative quantity) | Flagged as data integrity issue |

You may extend the seed data with additional items or columns (e.g., unit price, category) to support richer validation — the above is the minimum needed to exercise the provided test invoices. If you want your system to also validate pricing or vendor information, consider adding tables for those as well.

## Running the System

To run the system, you can use the following command-line options (as parsed in `main.py`):

- **Process a Single Invoice File:**
  ```bash
  python main.py --invoice-path=data/invoices/invoice_1001.txt
  ```

- **Process All Invoices in the Dataset (default, no flags):**
  ```bash
  python main.py
  ```

- **Reset the Invoices Table:**
  ```bash
  python main.py --reset-invoices
  ```

- **Reset the Inventory Table:**
  ```bash
  python main.py --reset-inventory
  ```

- **Run Golden Dataset Test Suite Only (without processing invoices):**
  ```bash
  python main.py --test-only
  ```

You can mix and match these flags as needed; they all work completely independently. If you run the script **without any flags**, it will process all invoices found in the default `data/invoices/` folder.

All results are written to the invoices table in the SQLite database `data/invoices.db`.

## UI Experience

You can manually upload your invoices [on this dashboard](https://romankouz-galatiq-case-invoices.streamlit.app/) to see the multi-agent in action for yourself!

## Future Work

While our MVP indicates that leverage a multi-agent framework for invoice processing is a promising direction, there are immediate steps we can take to improve the current system.

### Offline Fallback

In the event that any of our providers go down, we have no offline alternative to locally run our pipeline. Finding a suitable but small model from HuggingFace and using it if leveraging xAI's models is ever ineffective helps maintain uptime.

### Generator/Discriminator Training

To fully stress test our solution, we should have both humans and AI generate invoices that are meant to trick our system. In doing so, our discriminator gets better at identifying passable invoices from ones that fail even when the discernability between an acceptable/rejectable invoice decreases.

## Evaluation Criteria

- **Functionality** — Does the system work end-to-end? ✅
- **Code Quality** — Clean, testable, well-structured code with error handling and observability ✅
- **Agentic Sophistication** — LLM integration, multi-agent flow, tool use, self-correction loops ✅
- **Shipping Mindset** — Valuable MVP delivered under ambiguity; scope ruthlessly cut where needed ✅
- **Presentation** — Clear translation of technical decisions to business impact ✅
- **Above/Beyond** - Have you made it your own? Implemented additional features that make the solution feel great? Expanded assumptions? Added to test cases? ✅
- **UI/UX** - Users will understand and enjoy using this system. ✅
