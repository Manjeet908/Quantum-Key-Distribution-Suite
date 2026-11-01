"""
Quantum-themed custom CSS styles, tokens, and UI layout components.
"""
import re

QUANTUM_CSS = """
<style>
    /* Global Typography & Font Setup */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre, [class*="stCode"], .monospace-font {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main Container Polish */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        max-width: 1400px;
    }

    /* Custom Header Hero Banner */
    .quantum-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(10, 15, 30, 0.96) 100%);
        border: 1px solid rgba(0, 245, 212, 0.3);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 245, 212, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .quantum-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }

    .quantum-title .gradient-text {
        background: linear-gradient(90deg, #00f5d4 0%, #a78bfa 50%, #f43f5e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .quantum-subtitle {
        color: #94a3b8;
        font-size: 1.0rem;
        margin-bottom: 0;
    }

    /* Native Streamlit Metric Overrides: Prevent Ellipsis & Fix Sizes */
    [data-testid="stMetric"] {
        background: rgba(18, 24, 41, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(0, 245, 212, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        white-space: normal !important;
        word-break: break-word !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #94a3b8 !important;
        white-space: normal !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricDelta"] {
        white-space: normal !important;
        word-break: break-word !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
    }

    /* Status Badges */
    .badge-secure {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 9999px;
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }
    .badge-warning {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 9999px;
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }
    .badge-compromised {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 9999px;
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }

    /* Pipeline Step Box */
    .pipeline-step {
        background: rgba(15, 23, 42, 0.7);
        border-left: 3px solid #00f5d4;
        border-radius: 0 10px 10px 0;
        padding: 12px 18px;
        margin-bottom: 12px;
        color: #e2e8f0;
    }

    /* Expander Polish */
    .streamlit-expanderHeader {
        background: rgba(18, 24, 41, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        padding: 12px 18px !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: rgba(0, 245, 212, 0.4) !important;
        color: #00f5d4 !important;
    }
    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 16px 20px !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 0.95rem;
        background: rgba(18, 24, 41, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: none;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #00f5d4 !important;
        border-color: rgba(0, 245, 212, 0.4) !important;
    }

    /* ==========================================================================
       MITM RESULTS DEDICATED STYLING
       ========================================================================== */

    /* MITM Status Alert Banner */
    .mitm-banner {
        border-radius: 14px;
        padding: 22px 26px;
        margin: 16px 0 22px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
    }
    .mitm-banner-compromised {
        background: linear-gradient(135deg, rgba(45, 15, 22, 0.98) 0%, rgba(18, 24, 41, 0.98) 100%) !important;
        border: 1px solid rgba(239, 68, 68, 0.55) !important;
        border-left: 6px solid #ef4444 !important;
    }
    .mitm-banner-thwarted {
        background: linear-gradient(135deg, rgba(12, 38, 28, 0.98) 0%, rgba(18, 24, 41, 0.98) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.55) !important;
        border-left: 6px solid #10b981 !important;
    }
    .mitm-banner-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .mitm-banner-title {
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .mitm-banner-compromised .mitm-banner-title {
        color: #fca5a5 !important;
    }
    .mitm-banner-thwarted .mitm-banner-title {
        color: #6ee7b7 !important;
    }
    .mitm-banner-meta {
        font-size: 0.85rem !important;
        color: #cbd5e1 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        background: rgba(0, 0, 0, 0.35);
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .mitm-banner-desc {
        color: #f1f5f9 !important;
        font-size: 0.98rem !important;
        line-height: 1.65 !important;
        margin-bottom: 16px !important;
        font-weight: 400 !important;
    }
    .mitm-banner-desc b {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    .mitm-banner-desc code {
        background: rgba(0, 0, 0, 0.4) !important;
        color: #00f5d4 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .mitm-points-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
    }
    .mitm-point-card {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        font-size: 0.90rem !important;
        line-height: 1.5 !important;
        color: #e2e8f0 !important;
    }
    .mitm-point-card code {
        background: rgba(0, 0, 0, 0.4) !important;
        color: #00f5d4 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .mitm-point-title {
        font-weight: 700 !important;
        margin-bottom: 6px !important;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.95rem !important;
    }
    .point-danger .mitm-point-title {
        color: #f87171 !important;
    }
    .point-success .mitm-point-title {
        color: #34d399 !important;
    }

    /* MITM Metric Cards Grid */
    .mitm-stat-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin: 18px 0 24px 0;
    }
    @media (max-width: 1080px) {
        .mitm-stat-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    @media (max-width: 680px) {
        .mitm-stat-grid {
            grid-template-columns: 1fr;
        }
    }
    .mitm-stat-card {
        background: rgba(18, 24, 41, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 105px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .mitm-stat-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 245, 212, 0.4);
    }
    .mitm-stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .mitm-stat-val {
        font-size: 1.45rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        color: #f8fafc;
        line-height: 1.25;
        margin-bottom: 6px;
    }
    .mitm-stat-sub {
        font-size: 0.76rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 6px;
        width: fit-content;
    }
    .sub-red {
        background: rgba(239, 68, 68, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .sub-green {
        background: rgba(16, 185, 129, 0.18);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .sub-amber {
        background: rgba(245, 158, 11, 0.18);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .sub-cyan {
        background: rgba(6, 182, 212, 0.18);
        color: #38bdf8;
        border: 1px solid rgba(6, 182, 212, 0.35);
    }

    /* MITM Network Architecture & Topology Visualization */
    .topology-container {
        background: rgba(15, 23, 42, 0.96) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        padding: 22px !important;
        margin: 12px 0 20px 0 !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
        color: #f8fafc !important;
    }
    .topology-status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        padding-bottom: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .topology-status-pill {
        font-size: 0.85rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .status-pill-compromised {
        background: rgba(239, 68, 68, 0.25) !important;
        color: #fca5a5 !important;
        border: 1px solid rgba(239, 68, 68, 0.5) !important;
    }
    .status-pill-thwarted {
        background: rgba(16, 185, 129, 0.25) !important;
        color: #6ee7b7 !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }
    .topology-flow-grid {
        display: grid;
        grid-template-columns: 1fr 1.35fr 1.25fr 1.35fr 1fr;
        gap: 14px;
        align-items: stretch;
    }
    @media (max-width: 980px) {
        .topology-flow-grid {
            grid-template-columns: 1fr;
        }
    }
    .topology-node {
        background: rgba(24, 32, 54, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        padding: 16px 14px !important;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .node-alice {
        border-top: 4px solid #38bdf8 !important;
    }
    .node-eve {
        border-top: 4px solid #f43f5e !important;
        background: linear-gradient(180deg, rgba(50, 20, 35, 0.95) 0%, rgba(24, 32, 54, 0.95) 100%) !important;
    }
    .node-bob {
        border-top: 4px solid #34d399 !important;
    }
    .node-avatar {
        font-size: 2.2rem;
        margin-bottom: 4px;
    }
    .node-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 2px;
    }
    .node-subtitle {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
    }
    .node-key-badge {
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-block;
        font-weight: 600;
        margin-top: auto;
    }
    .badge-alice {
        background: rgba(56, 189, 248, 0.18) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
    }
    .badge-eve {
        background: rgba(244, 63, 94, 0.18) !important;
        color: #fb7185 !important;
        border: 1px solid rgba(244, 63, 94, 0.4) !important;
    }
    .badge-bob {
        background: rgba(52, 211, 153, 0.18) !important;
        color: #34d399 !important;
        border: 1px solid rgba(52, 211, 153, 0.4) !important;
    }
    .topology-link {
        background: rgba(18, 24, 41, 0.8) !important;
        border: 1px dashed rgba(255, 255, 255, 0.18) !important;
        border-radius: 10px !important;
        padding: 14px 12px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        gap: 8px;
    }
    .link-header {
        font-weight: 700;
        color: #e2e8f0;
        font-size: 0.84rem;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 4px;
    }
    .link-item {
        background: rgba(0, 0, 0, 0.35) !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 0.80rem !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .link-item-name {
        color: #94a3b8;
        font-weight: 500;
    }
    .link-item-val {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
    }
    .topology-summary-bar {
        margin-top: 18px;
        padding: 14px 20px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .summary-compromised {
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #fca5a5 !important;
    }
    .summary-thwarted {
        background: rgba(16, 185, 129, 0.15) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #6ee7b7 !important;
    }

    /* Cryptographic HMAC Verification Panel */
    .crypto-console {
        background: rgba(15, 23, 42, 0.96) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin: 14px 0 18px 0 !important;
    }
    .crypto-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 16px;
    }
    @media (max-width: 860px) {
        .crypto-grid {
            grid-template-columns: 1fr;
        }
    }
    .crypto-box {
        background: rgba(24, 32, 54, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 14px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .crypto-box-label {
        font-size: 0.74rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .crypto-tag-code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        font-weight: 700;
        word-break: break-all;
        padding: 6px 10px;
        border-radius: 6px;
        display: inline-block;
    }
    .tag-mismatch {
        background: rgba(239, 68, 68, 0.22) !important;
        color: #fca5a5 !important;
        border: 1px solid rgba(239, 68, 68, 0.5) !important;
    }
    .tag-expected {
        background: rgba(16, 185, 129, 0.22) !important;
        color: #6ee7b7 !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }
    .tag-neutral {
        background: rgba(100, 116, 139, 0.22) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(100, 116, 139, 0.45) !important;
    }
    .crypto-explanation {
        font-size: 0.90rem !important;
        line-height: 1.6 !important;
        padding: 14px 18px !important;
        border-radius: 8px !important;
    }
    .crypto-exp-danger {
        background: rgba(239, 68, 68, 0.12) !important;
        border-left: 4px solid #ef4444 !important;
        color: #fecaca !important;
    }
    .crypto-exp-warning {
        background: rgba(245, 158, 11, 0.12) !important;
        border-left: 4px solid #f59e0b !important;
        color: #fef3c7 !important;
    }

    /* Multi-Party Key Distillation Matrix */
    .key-matrix-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 16px 0 20px 0;
    }
    @media (max-width: 900px) {
        .key-matrix-grid {
            grid-template-columns: 1fr;
        }
    }
    .key-card {
        background: rgba(18, 24, 41, 0.96) !important;
        border-radius: 12px !important;
        padding: 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .key-card-alice {
        border-top: 4px solid #38bdf8 !important;
    }
    .key-card-eve {
        border-top: 4px solid #f43f5e !important;
        background: linear-gradient(180deg, rgba(45, 20, 36, 0.96) 0%, rgba(18, 24, 41, 0.96) 100%) !important;
    }
    .key-card-bob {
        border-top: 4px solid #34d399 !important;
    }
    .key-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .key-card-title {
        font-weight: 700;
        font-size: 1.0rem;
        color: #f8fafc;
    }
    .key-preview-bits {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.84rem;
        background: rgba(0, 0, 0, 0.45);
        padding: 10px 12px;
        border-radius: 8px;
        letter-spacing: 0.04em;
        word-break: break-all;
        color: #f1f5f9;
        margin-bottom: 10px;
        line-height: 1.45;
    }
    .key-hex-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #00f5d4;
        font-weight: 600;
        background: rgba(0, 245, 212, 0.12);
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid rgba(0, 245, 212, 0.3);
    }
    .key-status-text {
        font-size: 0.80rem;
        color: #94a3b8;
        margin-top: 10px;
        line-height: 1.45;
    }
</style>
"""

def clean_html(html_str: str) -> str:
    """
    Cleans an HTML string for Streamlit markdown rendering:
    - Removes HTML comments
    - Strips all leading/trailing whitespace from each line
    - Removes empty lines
    This strictly prevents CommonMark from misinterpreting indented lines as code blocks.
    """
    cleaned = re.sub(r'<!--.*?-->', '', html_str, flags=re.DOTALL)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(lines)

def render_hero(title: str, subtitle: str = "") -> str:
    """Renders the top hero banner with proper emoji rendering."""
    sub_html = f'<div class="quantum-subtitle">{subtitle}</div>' if subtitle else ""
    return clean_html(f"""
    <div class="quantum-hero">
        <div class="quantum-title">
            <span>⚛️</span>
            <span class="gradient-text">{title}</span>
        </div>
        {sub_html}
    </div>
    """)

def render_badge(status: str) -> str:
    """Renders a status badge."""
    status_upper = status.upper()
    if status_upper == "SECURE":
        return '<span class="badge-secure">● SECURE KEY ESTABLISHED</span>'
    elif status_upper == "WARNING":
        return '<span class="badge-warning">▲ ELEVATED NOISE / CAUTION</span>'
    else:
        return '<span class="badge-compromised">✖ EAVESDROPPER / COMPROMISED</span>'
