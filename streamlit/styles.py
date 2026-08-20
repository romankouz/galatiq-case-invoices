"""Visual styles for the Acme invoice dashboard."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');

/* --- Page --- */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #EFE6D6 !important;
    background-image:
        radial-gradient(ellipse at top left, rgba(45, 156, 219, 0.14) 0%, transparent 42%),
        radial-gradient(ellipse at top right, rgba(232, 93, 4, 0.10) 0%, transparent 38%),
        radial-gradient(ellipse at bottom, rgba(42, 157, 143, 0.10) 0%, #E9DCC8 70%) !important;
    color: #3D3226;
    font-family: "Source Sans 3", "Segoe UI", sans-serif;
}

.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    z-index: 1000;
    background: linear-gradient(90deg, #C62828 0%, #E9C46A 32%, #2A9D8F 66%, #1D4ED8 100%);
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"],
#MainMenu, footer, header [data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stSpinner, [data-testid="stSpinner"] {
    visibility: hidden;
    height: 0;
}

/* --- Spacing scale: 8 / 16 / 24 --- */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 720px !important;
}

/* One gap between every major block in the page column */
.block-container > [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] {
    gap: 24px !important;
}

/* Buttons sitting side by side should be closer than page sections */
[data-testid="stHorizontalBlock"] {
    gap: 12px !important;
    margin: 0 !important;
}

[data-testid="stHorizontalBlock"] > div {
    padding: 0 !important;
}

[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

div[data-testid="stElementContainer"],
div[data-testid="element-container"] {
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stMarkdownContainer"] {
    padding: 0 !important;
}

[data-testid="stMarkdownContainer"] p {
    margin: 0;
}

/* The injected stylesheet should not take up a slot in the page stack */
div[data-testid="stElementContainer"]:has(> div > [data-testid="stMarkdownContainer"] > style),
div[data-testid="stElementContainer"]:has(style) {
    display: none !important;
}

[data-testid="stWidgetLabel"] {
    margin-bottom: 8px !important;
    padding: 0 !important;
}

[data-testid="stWidgetLabel"] p {
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    color: #1F3A5F !important;
}

/* --- Type --- */
h1, h2, h3, .brand-title {
    font-family: "Libre Baskerville", Georgia, serif !important;
    color: #1F3A5F !important;
}

/* --- Upload --- */
[data-testid="stFileUploader"] {
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stFileUploader"] section {
    background: #FBF7F0 !important;
    border: 1.5px dashed #3D8BDB !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}

[data-testid="stFileUploader"] section:hover {
    border-color: #2A9D8F !important;
    background: #F4FBFA !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
}

/* --- Buttons: full-width, same height, one primary --- */
div[data-testid="stButton"] {
    margin: 0 !important;
    width: 100%;
}

.stButton > button {
    width: 100% !important;
    height: 44px !important;
    background: #1F3A5F !important;
    color: #F7FBFF !important;
    border: 1.5px solid #1F3A5F !important;
    border-radius: 10px !important;
    padding: 0 1rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: #163056 !important;
    color: #fff !important;
}

.stButton > button[kind="secondary"] {
    background: #FBF7F0 !important;
    color: #1F3A5F !important;
    border: 1.5px solid #1F3A5F !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #EAF0F8 !important;
    color: #1F3A5F !important;
}

/* --- Header: company lockup, then page name --- */
.hero {
    margin: 0;
}

.company-header {
    display: flex;
    align-items: center;
    gap: 16px;
}

.mark {
    width: 56px;
    height: 56px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1F3A5F;
    color: #FBF7F0;
    font-family: "Libre Baskerville", Georgia, serif;
    font-size: 1.85rem;
    font-weight: 700;
    border-radius: 8px;
    box-shadow: inset 0 0 0 2px #C4A574;
}

.wordmark-name {
    font-family: "Libre Baskerville", Georgia, serif;
    font-size: 2.15rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #1F3A5F;
    line-height: 1;
}

.wordmark-entity {
    margin-top: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #8B6F45;
}

.header-rule {
    height: 1px;
    margin: 16px 0;
    background: linear-gradient(90deg, #C4A574 0%, #1F3A5F 45%, transparent 100%);
}

.brand-title {
    font-size: 1.35rem;
    margin: 0 0 8px 0;
    font-weight: 700;
    line-height: 1.2;
}

.subtitle {
    color: #4A5568;
    font-size: 1rem;
    line-height: 1.55;
    margin: 0;
    max-width: 36rem;
}

/* --- Cards share one size and padding --- */
.load-card,
.result-shell,
.note-banner {
    background: #FBF7F0;
    border: 1px solid #C9D6EA;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(31, 58, 95, 0.08);
    margin: 0;
}

.load-card,
.result-shell {
    padding: 24px;
    position: relative;
    overflow: hidden;
}

.load-card {
    text-align: center;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    border-top: 4px solid #1D4ED8;
}

.load-card h3 {
    margin: 0;
    font-size: 1.2rem;
    color: #1F3A5F !important;
}

.load-card p {
    margin: 0;
    color: #4A5568;
    max-width: 28rem;
}

.spinner {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    border: 4px solid #D7E4F5;
    border-top-color: #C62828;
    border-right-color: #1D4ED8;
    animation: spin 0.85s linear infinite;
}

.pulse-dots {
    display: flex;
    gap: 8px;
}

.pulse-dots span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #1D4ED8;
    animation: pulse 1.1s ease-in-out infinite;
}

.pulse-dots span:nth-child(2) {
    background: #2A9D8F;
    animation-delay: 0.15s;
}
.pulse-dots span:nth-child(3) {
    background: #C62828;
    animation-delay: 0.3s;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

@keyframes pulse {
    0%, 100% { opacity: 0.35; transform: scale(0.85); }
    50% { opacity: 1; transform: scale(1); }
}

@keyframes fadeOut {
    to { opacity: 0; visibility: hidden; }
}

@keyframes riseIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

.reveal-stage {
    position: relative;
}

.loading-ghost {
    position: absolute;
    inset: 0;
    background: #FBF7F0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 3;
    animation: fadeOut 0.45s ease 0.12s forwards;
    border-radius: 16px;
}

.result-card {
    animation: riseIn 0.55s ease 0.28s both;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.result-top {
    display: flex;
    align-items: center;
    gap: 16px;
}

.status-oval {
    width: 52px;
    height: 36px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1.15rem;
    font-weight: 700;
}

.status-oval.success {
    background: #0F9F6E;
    color: #F4FFF8;
}

.status-oval.failure {
    background: #C62828;
    color: #FFF6F6;
}

.result-heading .kicker {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #1D4ED8;
    font-weight: 700;
}

.result-heading .invoice-id {
    font-family: "Libre Baskerville", Georgia, serif;
    font-size: 1.35rem;
    color: #1F3A5F;
    margin-top: 4px;
}

.outcome-label {
    margin-left: auto;
    font-weight: 700;
    color: #1F3A5F;
}

.field-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.field {
    border-radius: 12px;
    padding: 16px;
    border-left: 4px solid #1F3A5F;
}

.field.vendor { border-left-color: #2A9D8F; background: #E8F6F3; }
.field.amount { border-left-color: #E9C46A; background: #FBF4E3; }
.field.decision { border-left-color: #1F3A5F; background: #EAF0F8; }
.field.confidence { border-left-color: #1D4ED8; background: #EAF2FB; }

.field .label {
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #5B6B82;
    font-weight: 700;
    margin: 0 0 4px 0;
}

.field .value {
    font-size: 1.05rem;
    color: #1F3A5F;
    font-weight: 600;
}

.confidence-track {
    height: 8px;
    background: rgba(31, 58, 95, 0.1);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 8px;
}

.confidence-clip {
    height: 100%;
    overflow: hidden;
    border-radius: 999px;
}

.confidence-gradient {
    height: 100%;
    background: linear-gradient(
        90deg,
        #C62828 0%,
        #E85D04 28%,
        #E9C46A 52%,
        #3D8BDB 78%,
        #1D4ED8 100%
    );
}

.reason-box {
    border-top: 1px solid #C9D6EA;
    padding-top: 24px;
}

.reason-box .label {
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #1D4ED8;
    font-weight: 700;
    margin: 0 0 8px 0;
}

.reason-box p {
    margin: 0;
    color: #334155;
    line-height: 1.55;
}

.action-banner {
    border-radius: 12px;
    padding: 16px;
    font-weight: 600;
    margin: 0;
}

.action-banner.paid {
    background: #D1FAE5;
    color: #065F46;
}

.action-banner.rejected {
    background: #FECACA;
    color: #991B1B;
}

.note-banner {
    padding: 16px 20px;
    font-size: 0.95rem;
    line-height: 1.5;
    font-weight: 600;
    box-shadow: none;
}

.note-banner.saved {
    background: #D1FAE5;
    color: #065F46;
    border-color: #6EE7B7;
}

.note-banner.duplicate {
    background: #FFFFFF;
    color: #9A3412;
    border-color: #FDBA74;
}

.note-banner.error {
    background: #FFFFFF;
    color: #991B1B;
    border-color: #FECACA;
}

.error-modal p {
    color: #4A3F32;
    line-height: 1.55;
    margin: 0 0 8px 0;
}

div[data-testid="stDialog"] div[role="dialog"] {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    box-shadow: 0 16px 40px rgba(31, 58, 95, 0.18) !important;
}

@media (max-width: 640px) {
    .field-grid { grid-template-columns: 1fr; }
    .result-top { flex-wrap: wrap; }
    .outcome-label { margin-left: 0; }
}
</style>
"""
