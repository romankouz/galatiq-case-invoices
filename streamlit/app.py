"""
Acme Corp invoice dashboard.

Run from the project root (so the rest of the app can be imported):

    streamlit run streamlit/app.py
"""

from __future__ import annotations

import html
import os
import sys
import tempfile
import time
from pathlib import Path

# This folder is named "streamlit", which would hide the real Streamlit library.
# Remove it from the import path first, load Streamlit, then add local modules back.
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent
sys.path[:] = [p for p in sys.path if Path(p).resolve() != _SCRIPT_DIR]

import streamlit as st

st.set_page_config(
    page_title="Acme Corp · Invoice Processing",
    page_icon="📄",
    layout="centered",
)

sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_SCRIPT_DIR))

from errors import UserFacingError, humanize_error
from processor import ProcessResult, get_agent, process_invoice_file, save_result_to_database
from src.tools.ingest_file import ALLOWED_EXTENSIONS
from styles import CSS

# Short labels for processing_result_sublabel
SUBLABEL_COPY = {
    "SUCCESS": "Ready For Payment",
    "STOCK MISMATCH": "Quantity Exceeds Stock",
    "ITEM OUT OF STOCK": "Item Out Of Stock",
    "NONEXISTENT ITEM": "Unknown Item",
    "INVALID QUANTITY": "Invalid Quantity",
}

UPLOAD_TYPES = sorted({ext.lstrip(".") for ext in ALLOWED_EXTENSIONS})


def inject_html(markup: str) -> None:
    """Put HTML on the page. Skip blank lines so Markdown does not break the layout."""
    compact = "\n".join(line for line in markup.splitlines() if line.strip())
    st.markdown(compact, unsafe_allow_html=True)


def confidence_text_color(pct: int) -> str:
    """Blend from red (low confidence) to blue (high confidence)."""
    t = max(0.0, min(1.0, pct / 100.0))
    start = (198, 40, 40)
    end = (29, 78, 216)
    r = int(start[0] + (end[0] - start[0]) * t)
    g = int(start[1] + (end[1] - start[1]) * t)
    b = int(start[2] + (end[2] - start[2]) * t)
    return f"rgb({r}, {g}, {b})"


def init_state() -> None:
    """Remember dashboard status between button clicks."""
    defaults = {
        "phase": "idle",  # idle | loading | done | error
        "temp_path": None,
        "file_name": None,
        "result": None,
        "error_message": None,
        "db_status": None,  # None | saved | duplicate | error
        "db_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def cached_agent():
    """Build the agent once so later uploads are faster."""
    return get_agent()


def reset_dashboard() -> None:
    """Clear the last file and result so someone can start a new Acme review."""
    temp_path = st.session_state.get("temp_path")
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    st.session_state.phase = "idle"
    st.session_state.temp_path = None
    st.session_state.file_name = None
    st.session_state.result = None
    st.session_state.error_message = None
    st.session_state.db_status = None
    st.session_state.db_message = None


def save_upload(uploaded_file) -> str:
    """Write the browser upload to a temp file so Acme's pipeline can open it by path."""
    suffix = Path(uploaded_file.name).suffix
    handle, path = tempfile.mkstemp(prefix="invoice_", suffix=suffix)
    os.close(handle)
    with open(path, "wb") as out:
        out.write(uploaded_file.getvalue())
    return path


def render_header() -> None:
    inject_html(
        """
        <div class="hero">
            <div class="eyebrow">Acme Corp</div>
            <h1 class="brand-title">Invoice Processing</h1>
            <p class="subtitle">
                Acme matches each vendor invoice to plant inventory and issues a pay-or-reject
                decision before payment is released.
            </p>
        </div>
        """
    )


def render_spinner() -> None:
    inject_html(
        """
        <div class="load-card">
            <div class="spinner"></div>
            <h3>Running Acme Review</h3>
            <p>Acme is reading this invoice, checking plant stock, and preparing a pay-or-reject decision.</p>
            <div class="pulse-dots"><span></span><span></span><span></span></div>
        </div>
        """
    )


def render_results(result: ProcessResult) -> None:
    """Show OutputState fields in a layout people can scan quickly."""
    is_success = result.processing_result == "SUCCESS"
    oval_class = "success" if is_success else "failure"
    mark = "✓" if is_success else "✕"
    outcome = "Approved" if is_success else "Rejected"
    sublabel = SUBLABEL_COPY.get(
        result.processing_result_sublabel,
        result.processing_result_sublabel.replace("_", " ").title(),
    )
    amount = f"${result.amount:,.2f}"
    confidence_pct = int(round(max(0.0, min(1.0, result.confidence)) * 100))
    conf_color = confidence_text_color(confidence_pct)
    gradient_width = f"calc(10000% / {max(confidence_pct, 1)})"
    vendor = html.escape(result.vendor_name or "—")
    invoice_number = html.escape(result.invoice_number or "—")
    reason = html.escape(result.reason or "No additional explanation was provided.")
    sublabel_safe = html.escape(sublabel)

    if result.payment_action == "paid":
        banner_class = "paid"
        banner_text = f"Acme can release {amount} to {vendor}."
    else:
        banner_class = "rejected"
        banner_text = f"Acme is holding payment of {amount} to {vendor}."

    inject_html(
        f"""
        <div class="result-shell reveal-stage">
            <div class="loading-ghost">
                <div class="spinner"></div>
            </div>
            <div class="result-card">
                <div class="result-top">
                    <div class="status-oval {oval_class}" title="{outcome}">{mark}</div>
                    <div class="result-heading">
                        <div class="kicker">Acme Decision</div>
                        <div class="invoice-id">{invoice_number}</div>
                    </div>
                    <div class="outcome-label">{outcome}</div>
                </div>
                <div class="field-grid">
                    <div class="field vendor">
                        <div class="label">Vendor</div>
                        <div class="value">{vendor}</div>
                    </div>
                    <div class="field amount">
                        <div class="label">Amount</div>
                        <div class="value">{amount}</div>
                    </div>
                    <div class="field decision">
                        <div class="label">Decision</div>
                        <div class="value">{sublabel_safe}</div>
                    </div>
                    <div class="field confidence">
                        <div class="label">Confidence</div>
                        <div class="value" style="color:{conf_color}">{confidence_pct}%</div>
                        <div class="confidence-track">
                            <div class="confidence-clip" style="width:{confidence_pct}%">
                                <div class="confidence-gradient" style="width:{gradient_width}"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="reason-box">
                    <div class="label">Reasoning</div>
                    <p>{reason}</p>
                </div>
                <div class="action-banner {banner_class}">{banner_text}</div>
            </div>
        </div>
        """
    )


def try_save_to_database(result: ProcessResult) -> None:
    """Save the Acme review when the user asks."""
    try:
        save_result_to_database(result)
        st.session_state.db_status = "saved"
        st.session_state.db_message = None
    except UserFacingError as exc:
        message = str(exc)
        if "different id" in message.lower() or "already in" in message.lower():
            st.session_state.db_status = "duplicate"
        else:
            st.session_state.db_status = "error"
        st.session_state.db_message = message
    except Exception as exc:
        st.session_state.db_status = "error"
        st.session_state.db_message = humanize_error(exc)
    st.rerun()


def render_actions(result: ProcessResult) -> None:
    """
    Keep actions in one bar under the result.

    Primary: save to Acme's database, when that is still possible.
    Secondary: start another invoice.
    """
    status = st.session_state.db_status

    if status == "saved":
        inject_html(
            '<div class="note-banner saved">This invoice is now in Acme\'s database.</div>'
        )
        if st.button("Process Another Invoice", use_container_width=True):
            reset_dashboard()
            st.rerun()
        return

    if status == "duplicate":
        inject_html(
            f'<div class="note-banner duplicate">{html.escape(st.session_state.db_message)}</div>'
        )
        if st.button("Process Another Invoice", use_container_width=True):
            reset_dashboard()
            st.rerun()
        return

    if status == "error":
        inject_html(
            f'<div class="note-banner error">{html.escape(st.session_state.db_message)}</div>'
        )

    save_col, next_col = st.columns(2, gap="small")
    with save_col:
        if st.button("Upload To Database", type="primary", use_container_width=True):
            try_save_to_database(result)
    with next_col:
        if st.button("Process Another Invoice", type="secondary", use_container_width=True):
            reset_dashboard()
            st.rerun()


@st.dialog("Acme could not process this invoice")
def error_popup(message: str) -> None:
    """White modal with a plain-language explanation — no technical jargon."""
    st.markdown(
        f"""
        <div class="error-modal">
            <p>{html.escape(message)}</p>
            <p>Nothing was saved to Acme's records. You can close this window and try another file.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Got It", use_container_width=True):
        st.session_state.error_message = None
        st.session_state.phase = "idle"
        st.rerun()


def run_pipeline() -> None:
    """Process the saved upload. Called only while the spinner is on screen."""
    try:
        time.sleep(0.15)
        result = process_invoice_file(st.session_state.temp_path, agent=cached_agent())
        st.session_state.result = result
        st.session_state.phase = "done"
        st.session_state.error_message = None
        st.session_state.db_status = None
        st.session_state.db_message = None
    except Exception as exc:
        st.session_state.result = None
        st.session_state.phase = "error"
        st.session_state.error_message = humanize_error(exc)


def main() -> None:
    init_state()
    inject_html(CSS)
    render_header()

    if st.session_state.phase == "error" and st.session_state.error_message:
        error_popup(st.session_state.error_message)

    if st.session_state.phase == "loading":
        render_spinner()
        with st.spinner(""):
            run_pipeline()
        st.rerun()

    if st.session_state.phase == "done" and st.session_state.result:
        render_results(st.session_state.result)
        render_actions(st.session_state.result)
        return

    uploaded = st.file_uploader(
        "Upload An Invoice",
        type=UPLOAD_TYPES,
        help="PDF, Word, Excel, CSV, JSON, XML, Text, Markdown, Or ZIP",
    )

    process_clicked = st.button(
        "Process Invoice",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None,
    )

    if process_clicked and uploaded is not None:
        try:
            if uploaded.size == 0:
                raise UserFacingError(
                    "This file is empty. Acme needs a complete invoice to continue."
                )
            st.session_state.temp_path = save_upload(uploaded)
            st.session_state.file_name = uploaded.name
            st.session_state.phase = "loading"
            st.session_state.result = None
            st.session_state.error_message = None
            st.session_state.db_status = None
            st.session_state.db_message = None
            st.rerun()
        except Exception as exc:
            st.session_state.phase = "error"
            st.session_state.error_message = humanize_error(exc)
            st.rerun()


if __name__ == "__main__":
    main()
