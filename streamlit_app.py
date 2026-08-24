"""
Streamlit version of Signal — Crisis-Aware Search Reranker.

Run locally:  streamlit run streamlit_app.py
Deploy:      push to GitHub, connect the repo at share.streamlit.io.

The Gradio version (app.py) is preserved for local development. This file is
the entry point Streamlit Community Cloud uses. Both share the same src/
pipeline code.
"""
import streamlit as st
import streamlit.components.v1 as components

from src.live_pipeline import run_pipeline_live

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Signal — Crisis-Aware Search",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={},
)


# ---------------------------------------------------------------------------
# CSS — preserves Signal's visual identity + neutralizes Streamlit's chrome
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #050308;
    --panel: #0F0B1A;
    --panel-2: #150F24;
    --border: #26203A;
    --border-soft: rgba(155,124,255,0.10);
    --text: #F1EFF7;
    --muted: #8B85A3;
    --standard: #9B7CFF;
    --standard-dim: #201546;
    --emergency: #FF4F5C;
    --emergency-dim: #3B0F1A;
    --debunk: #FBBF24;
    --live-ok: #4ADE80;
    --star: rgba(255,255,255,0.55);
}

/* ---- Hide Streamlit's default chrome ---- */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton {
    display: none !important;
}

/* ---- Full-width dark shell ---- */
* { box-sizing: border-box; }
html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main .block-container {
    background: var(--bg) !important;
    padding: 0 !important;
    max-width: 100% !important;
}

/* Layered background: stars, orbs */
body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(1.5px 1.5px at 12% 18%, var(--star), transparent),
        radial-gradient(1.5px 1.5px at 28% 62%, var(--star), transparent),
        radial-gradient(1px 1px at 44% 30%, var(--star), transparent),
        radial-gradient(1.5px 1.5px at 61% 8%, var(--star), transparent),
        radial-gradient(1px 1px at 73% 48%, var(--star), transparent),
        radial-gradient(1.5px 1.5px at 85% 22%, var(--star), transparent),
        radial-gradient(1px 1px at 92% 68%, var(--star), transparent),
        radial-gradient(1.5px 1.5px at 6% 78%, var(--star), transparent),
        radial-gradient(1px 1px at 38% 88%, var(--star), transparent),
        radial-gradient(1.5px 1.5px at 55% 92%, var(--star), transparent);
    animation: twinkle 5s ease-in-out infinite alternate;
}
body::after {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 1000px 620px at 20% -5%, rgba(155,124,255,0.20), transparent 60%),
        radial-gradient(ellipse 720px 460px at 100% 12%, rgba(255,79,92,0.09), transparent 60%),
        radial-gradient(ellipse 640px 600px at 50% 108%, rgba(120,90,220,0.14), transparent 60%);
}
@keyframes twinkle { 0% { opacity: 0.55; } 100% { opacity: 1; } }

/* Make sure Streamlit content sits above the background layers */
[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

/* ---- Top nav ---- */
.top-nav {
    position: sticky; top: 0; z-index: 20;
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 40px;
    background: rgba(5,3,8,0.60);
    backdrop-filter: blur(14px) saturate(140%);
    -webkit-backdrop-filter: blur(14px) saturate(140%);
    border-bottom: 1px solid var(--border-soft);
    margin-bottom: 20px;
}
.top-nav .brand { display: flex; align-items: center; gap: 12px; }
.logo-mark {
    position: relative;
    width: 26px; height: 26px; border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #C4B0FF, var(--standard) 55%, #3A1E8C 100%);
    box-shadow: 0 0 14px rgba(155,124,255,0.55), inset 0 0 6px rgba(255,255,255,0.15);
}
.logo-mark::after {
    content: ''; position: absolute; inset: -5px; border-radius: 50%;
    border: 1px solid rgba(155,124,255,0.25);
    animation: pulse-ring 2.6s ease-in-out infinite;
}
@keyframes pulse-ring { 0%,100% { transform: scale(1); opacity: 0.6; } 50% { transform: scale(1.15); opacity: 0.15; } }
.wordmark {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800; font-size: 1.4rem;
    color: var(--text);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.beta-pill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    padding: 3px 8px;
    border: 1px solid rgba(155,124,255,0.45);
    color: var(--standard);
    border-radius: 4px;
    text-transform: uppercase;
}
.nav-links {
    display: flex; gap: 28px; align-items: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.74rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}
.nav-links a { color: var(--muted); text-decoration: none; transition: color 0.15s; }
.nav-links a:hover { color: var(--text); }
.nav-cta {
    padding: 8px 14px;
    border: 1px solid rgba(155,124,255,0.5);
    color: var(--text) !important;
    border-radius: 6px;
    background: rgba(155,124,255,0.08);
}
.nav-cta:hover { background: rgba(155,124,255,0.18); }

/* ---- Hero ---- */
#hero { padding: 60px 0 8px 0; text-align: center; }
#hero .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.4em;
    color: var(--standard);
    text-transform: uppercase;
    margin-bottom: 14px;
}
#hero h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 900 !important;
    font-size: 6rem !important;
    line-height: 0.92 !important;
    color: var(--text) !important;
    margin: 0 0 18px 0 !important;
    text-transform: uppercase;
    text-shadow: 0 0 50px rgba(155,124,255,0.4);
    letter-spacing: -0.01em;
}
#hero p.tagline {
    color: var(--text) !important;
    font-size: 1.15rem !important;
    max-width: 640px;
    margin: 0 auto 6px auto !important;
    line-height: 1.5;
    font-weight: 500;
}
#hero p.sub {
    color: var(--muted) !important;
    font-size: 0.98rem !important;
    max-width: 580px;
    margin: 0 auto !important;
    line-height: 1.55;
}
.status-line {
    display: inline-flex; align-items: center;
    gap: 14px; margin-top: 28px;
    padding: 8px 18px;
    background: rgba(15,11,26,0.55);
    border: 1px solid var(--border);
    border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    color: var(--muted);
    text-transform: uppercase;
}
.status-line .live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--live-ok);
    box-shadow: 0 0 10px var(--live-ok);
    animation: live-pulse 1.4s ease-in-out infinite;
}
.status-line .sep { color: #3A3352; }
@keyframes live-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ---- Radar ---- */
#radar-wrap { display: flex; justify-content: center; margin: 30px 0 8px 0; }
.radar {
    width: 130px; height: 130px;
    border-radius: 50%;
    position: relative;
    border: 1px solid rgba(155,124,255,0.25);
    background: radial-gradient(circle, rgba(155,124,255,0.08) 0%, transparent 70%);
}
.radar::before, .radar::after {
    content: '';
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(155,124,255,0.15);
}
.radar::before { inset: 20px; }
.radar::after { inset: 42px; }
.radar-sweep {
    position: absolute; inset: 0;
    border-radius: 50%;
    background: conic-gradient(from 0deg, rgba(155,124,255,0.55), transparent 35%);
    animation: sweep-rotate 3.5s linear infinite;
}
.radar-sweep.alert {
    background: conic-gradient(from 0deg, rgba(255,79,92,0.65), transparent 30%);
    animation: sweep-rotate 0.9s linear infinite;
}
@keyframes sweep-rotate { 100% { transform: rotate(360deg); } }
.radar-blip {
    position: absolute;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--standard);
    box-shadow: 0 0 8px var(--standard);
    animation: blip-pulse 2.4s ease-in-out infinite;
}
.radar-blip.alert { background: var(--emergency); box-shadow: 0 0 8px var(--emergency); animation-duration: 0.8s; }
@keyframes blip-pulse { 0%,100% { opacity: 0.25; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.3); } }
.radar-dot-center {
    position: absolute; left: 50%; top: 50%; width: 4px; height: 4px;
    margin: -2px 0 0 -2px; border-radius: 50%; background: var(--text);
}

/* ---- Search input & button (Streamlit-native, restyled) ---- */
[data-testid="stTextInput"] label { display: none !important; }
[data-testid="stTextInput"] > div > div > input,
[data-testid="stTextInput"] input {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.02rem !important;
    padding: 18px 20px !important;
    box-shadow: 0 0 30px rgba(0,0,0,0.4) !important;
    min-height: 60px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--standard) !important;
    box-shadow: 0 0 0 3px rgba(155,124,255,0.22), 0 0 30px rgba(0,0,0,0.4) !important;
}

/* Primary "Search" button */
[data-testid="stButton"] > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(180deg, #B096FF, var(--standard)) !important;
    color: #0B0616 !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 18px 20px !important;
    min-height: 60px !important;
    box-shadow: 0 8px 24px rgba(155,124,255,0.35), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    transition: transform 0.15s, filter 0.15s !important;
    width: 100% !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    filter: brightness(1.10) !important;
    transform: translateY(-1px) !important;
}

/* Secondary buttons — example chips */
[data-testid="stButton"] > button:not([kind="primary"]),
.stButton > button:not([data-testid="baseButton-primary"]) {
    background: rgba(15,11,26,0.55) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    letter-spacing: 0.01em !important;
    text-transform: none !important;
    transition: border-color 0.15s, background 0.15s, transform 0.15s !important;
    font-weight: 500 !important;
    min-height: auto !important;
    box-shadow: none !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: var(--standard) !important;
    background: rgba(32,21,70,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ---- Examples label rows ---- */
.examples-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: var(--muted);
    text-transform: uppercase;
    text-align: center;
    margin: 24px 0 14px 0;
}
.example-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.22em;
    color: var(--muted);
    text-transform: uppercase;
    display: flex; align-items: center; gap: 8px;
    padding: 10px 0;
    height: 100%;
}
.example-label .lbl-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.example-label.live    .lbl-dot { background: var(--emergency); box-shadow: 0 0 8px var(--emergency); animation: dot-pulse 1s ease-in-out infinite; }
.example-label.debunk  .lbl-dot { background: var(--debunk); box-shadow: 0 0 8px var(--debunk); }
.example-label.history .lbl-dot { background: var(--standard); box-shadow: 0 0 8px var(--standard); }
@keyframes dot-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ---- Mode header + result cards ---- */
.mode-row { display: flex; align-items: baseline; gap: 14px; margin: 34px 0 4px 0; }
.mode-badge {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 1.7rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.mode-badge.standard { color: var(--standard); }
.mode-badge.emergency { color: var(--emergency); }
.mode-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.mode-dot.standard { background: var(--standard); box-shadow: 0 0 10px var(--standard); }
.mode-dot.emergency { background: var(--emergency); box-shadow: 0 0 10px var(--emergency); animation: dot-pulse 1s ease-in-out infinite; }
.mode-note { color: var(--muted); font-size: 0.95rem; margin-bottom: 26px; }

.result-card {
    background: linear-gradient(180deg, var(--panel), var(--panel-2));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.result-card:hover { border-color: var(--accent, var(--standard)); transform: translateY(-1px); }
.result-card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: var(--accent, var(--standard));
    box-shadow: 0 0 12px var(--accent, var(--standard));
}
.result-card .rank {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--muted);
    font-size: 0.75rem;
    letter-spacing: 0.15em;
}
.result-card h3 {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    line-height: 1.15;
    color: var(--text);
    margin: 4px 0 10px 0;
}
.result-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.result-meta .score {
    color: var(--accent, var(--standard));
    font-weight: 600;
    background: rgba(255,255,255,0.04);
    padding: 2px 8px;
    border-radius: 4px;
}
.signal-bars { display: flex; gap: 20px; margin-bottom: 16px; flex-wrap: wrap; }
.signal-bar-wrap { flex: 1; min-width: 150px; }
.signal-bar-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    color: var(--muted);
    display: flex; justify-content: space-between; margin-bottom: 5px;
}
.signal-bar-track { height: 5px; background: rgba(255,255,255,0.07); border-radius: 3px; overflow: hidden; }
.signal-bar-fill { height: 100%; border-radius: 3px; }
.signal-bar-fill.r { background: #7C9FFF; }
.signal-bar-fill.c { background: #4ADE80; }
.signal-bar-fill.f { background: #FBBF24; }
.result-text { color: #B4AFC7; font-size: 0.94rem; line-height: 1.6; }
.weights-note {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #504A66;
    margin-top: 14px;
    border-top: 1px dashed var(--border);
    padding-top: 10px;
}
.empty-state {
    text-align: center;
    color: var(--muted);
    padding: 20px 0 10px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 0.15em;
}

/* ---- How Signal ranks ---- */
.ranks-strip { padding: 60px 40px 20px 40px; border-top: 1px solid var(--border); margin-top: 60px; }
.ranks-header { text-align: center; margin-bottom: 44px; }
.ranks-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.35em;
    color: var(--standard);
    text-transform: uppercase;
}
.ranks-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 2.8rem;
    color: var(--text);
    margin: 12px 0 8px 0;
    text-transform: uppercase;
    line-height: 1.05;
}
.ranks-sub { color: var(--muted); max-width: 680px; margin: 8px auto 0 auto; line-height: 1.55; }
.rank-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
@media (max-width: 900px) { .rank-cards { grid-template-columns: 1fr; } }
.rank-card {
    background: linear-gradient(180deg, var(--panel), var(--panel-2));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 26px 28px;
    position: relative;
    display: flex; flex-direction: column;
}
.rank-card::after {
    content: '';
    position: absolute; inset: 0; border-radius: 14px; pointer-events: none;
    background: linear-gradient(180deg, rgba(155,124,255,0.06), transparent 40%);
}
.rank-card .num {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--standard);
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    margin-bottom: 6px;
}
.rank-card .name {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800; font-size: 1.75rem;
    color: var(--text);
    margin: 2px 0 12px 0;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}
.rank-card .desc { color: var(--muted); font-size: 0.92rem; line-height: 1.55; margin-bottom: 20px; }
.rank-card .weights { display: flex; gap: 14px; margin-top: auto; padding-top: 16px; border-top: 1px dashed var(--border); }
.rank-card .weight { flex: 1; }
.rank-card .weight-lbl {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 6px;
}
.rank-card .weight-lbl .m-dot { width: 6px; height: 6px; border-radius: 50%; }
.rank-card .weight.standard  .m-dot { background: var(--standard); }
.rank-card .weight.emergency .m-dot { background: var(--emergency); }
.rank-card .weight-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.25rem;
    font-weight: 600;
}
.rank-card .weight.standard  .weight-val { color: var(--standard); }
.rank-card .weight.emergency .weight-val { color: var(--emergency); }

/* ---- Sources ---- */
.sources-strip { padding: 50px 40px 30px 40px; text-align: center; }
.sources-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.35em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 22px;
}
.sources-row {
    display: flex; justify-content: center; align-items: center;
    gap: 44px; flex-wrap: wrap;
}
.source-item {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.7;
}
.sources-note {
    margin-top: 22px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.18em;
    color: #504A66;
    text-transform: uppercase;
}

/* ---- Footer ---- */
.site-footer {
    border-top: 1px solid var(--border);
    padding: 30px 40px;
    margin-top: 30px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
.site-footer a { color: var(--muted); text-decoration: none; }
.site-footer a:hover { color: var(--text); }
.site-footer .foot-brand { display: flex; align-items: center; gap: 10px; }
.site-footer .foot-brand .logo-mark { width: 16px; height: 16px; }

/* ---- Scroll-down hint (shown after a search fires) ---- */
.scroll-hint {
    text-align: center;
    padding: 22px 0 6px 0;
    margin-top: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.28em;
    color: var(--standard);
    text-transform: uppercase;
    opacity: 0.9;
}
.scroll-hint .arrow {
    display: inline-block;
    margin-left: 8px;
    animation: bounce-arrow 1.2s ease-in-out infinite;
    font-size: 0.95rem;
}
@keyframes bounce-arrow {
    0%, 100% { transform: translateY(0); opacity: 0.6; }
    50% { transform: translateY(5px); opacity: 1; }
}

/* ---- Mobile ---- */
@media (max-width: 720px) {
    .top-nav { padding: 12px 16px; }
    .top-nav .nav-links a:not(.nav-cta) { display: none; }
    #hero { padding: 30px 16px 6px 16px; }
    #hero h1 { font-size: 3.5rem !important; }
    #hero p.tagline { font-size: 1rem !important; }
    .status-line { font-size: 0.55rem; padding: 6px 12px; flex-wrap: wrap; justify-content: center; }
    .ranks-strip, .sources-strip, .site-footer { padding-left: 16px !important; padding-right: 16px !important; }
    .ranks-title { font-size: 2rem; }
    .rank-cards { grid-template-columns: 1fr !important; }
    .site-footer { flex-direction: column; align-items: flex-start; }
}
"""


# ---------------------------------------------------------------------------
# Static HTML fragments (nav, hero, ranks strip, sources, footer)
# ---------------------------------------------------------------------------
NAV_HTML = """
<div class="top-nav">
    <div class="brand">
        <span class="logo-mark"></span>
        <span class="wordmark">Signal</span>
        <span class="beta-pill">Beta</span>
    </div>
    <div class="nav-links">
        <a href="#how-it-ranks">How it ranks</a>
        <a href="#sources">Sources</a>
        <a href="https://github.com/Jaya242/CRISIS-SEARCH" target="_blank" class="nav-cta">GitHub &#8599;</a>
    </div>
</div>
"""

HERO_HTML = """
<div id="hero">
    <div class="eyebrow">Crisis-aware credibility ranker</div>
    <h1>Signal</h1>
    <p class="tagline">Rank news the way a newsroom would &mdash; not the way a search engine does.</p>
    <p class="sub">Signal auto-detects whether your query is an active emergency or a standard lookup, then re-weights relevance, credibility, and freshness in real time.</p>
    <div class="status-line">
        <span class="live-dot"></span>
        <span>Live</span>
        <span class="sep">/</span>
        <span>Google News RSS</span>
        <span class="sep">/</span>
        <span>Reranker v2</span>
    </div>
</div>
"""

RANKS_STRIP_HTML = """
<div class="ranks-strip" id="how-it-ranks">
    <div class="ranks-header">
        <div class="ranks-eyebrow">How Signal ranks</div>
        <div class="ranks-title">Three signals, two weight profiles</div>
        <div class="ranks-sub">The final score is a weighted sum of three per-document signals. Signal shifts the weights based on whether the query looks like an active emergency &mdash; freshness and source credibility matter more when lives are on the line.</div>
    </div>
    <div class="rank-cards">
        <div class="rank-card">
            <div class="num">01</div>
            <div class="name">Relevance</div>
            <div class="desc">Semantic similarity between the query and each article, from a MiniLM bi-encoder used off-the-shelf. The dominant signal in normal conditions.</div>
            <div class="weights">
                <div class="weight standard">
                    <div class="weight-lbl"><span class="m-dot"></span>Standard</div>
                    <div class="weight-val">0.75</div>
                </div>
                <div class="weight emergency">
                    <div class="weight-lbl"><span class="m-dot"></span>Emergency</div>
                    <div class="weight-val">0.45</div>
                </div>
            </div>
        </div>
        <div class="rank-card">
            <div class="num">02</div>
            <div class="name">Credibility</div>
            <div class="desc">Hybrid trust: 60% publisher-level prior from a curated reputation table + 40% per-article score from a DistilBERT classifier fine-tuned on LIAR2. Weighted heavier in emergencies where rumor is expensive.</div>
            <div class="weights">
                <div class="weight standard">
                    <div class="weight-lbl"><span class="m-dot"></span>Standard</div>
                    <div class="weight-val">0.10</div>
                </div>
                <div class="weight emergency">
                    <div class="weight-lbl"><span class="m-dot"></span>Emergency</div>
                    <div class="weight-val">0.25</div>
                </div>
            </div>
        </div>
        <div class="rank-card">
            <div class="num">03</div>
            <div class="name">Freshness</div>
            <div class="desc">Exponential decay on publish time. A three-day-old article about an active hurricane is nearly worthless; for a history query, dates barely matter.</div>
            <div class="weights">
                <div class="weight standard">
                    <div class="weight-lbl"><span class="m-dot"></span>Standard</div>
                    <div class="weight-val">0.15</div>
                </div>
                <div class="weight emergency">
                    <div class="weight-lbl"><span class="m-dot"></span>Emergency</div>
                    <div class="weight-val">0.30</div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

SOURCES_STRIP_HTML = """
<div class="sources-strip" id="sources">
    <div class="sources-label">Live retrieval</div>
    <div class="sources-row">
        <span class="source-item">Google News RSS &nbsp;&mdash;&nbsp; hundreds of publishers</span>
    </div>
    <div class="sources-note">Publisher-level trust prior applied per result &nbsp;&middot;&nbsp; no whitelist filtering at retrieval</div>
</div>
"""

FOOTER_HTML = """
<div class="site-footer">
    <div class="foot-brand">
        <span class="logo-mark"></span>
        <span>Signal &middot; Crisis-aware search</span>
    </div>
    <div>
        <a href="#how-it-ranks">How it ranks</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="#sources">Sources</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href="https://github.com/Jaya242/CRISIS-SEARCH" target="_blank">GitHub &#8599;</a>
    </div>
</div>
"""

BLIP_POSITIONS = [(18, 30), (85, 22), (62, 88), (30, 70), (75, 60)]


def _radar_html(alert: bool) -> str:
    cls = "alert" if alert else ""
    blips = "".join(
        f'<div class="radar-blip {cls}" style="left:{x}%; top:{y}%; animation-delay:{i*0.3}s"></div>'
        for i, (x, y) in enumerate(BLIP_POSITIONS)
    )
    return f"""
    <div id="radar-wrap">
      <div class="radar">
        <div class="radar-sweep {cls}"></div>
        <div class="radar-dot-center"></div>
        {blips}
      </div>
    </div>
    """


def _bar(label: str, value: float, css_class: str) -> str:
    pct = max(0, min(100, value * 100))
    return f"""
    <div class="signal-bar-wrap">
      <div class="signal-bar-label"><span>{label}</span><span>{value:.2f}</span></div>
      <div class="signal-bar-track"><div class="signal-bar-fill {css_class}" style="width:{pct:.0f}%"></div></div>
    </div>
    """


def _flatten_html(html: str) -> str:
    """Strip leading whitespace from every line and drop empty lines.

    Streamlit's markdown parser treats any line starting with 4+ spaces as
    a code block — even inside st.markdown(unsafe_allow_html=True). Our
    triple-quoted template strings are indented for Python readability, so
    without this the results render as literal HTML source instead of
    laying out the cards. This flattens the string so markdown sees a
    single unindented HTML blob and hands it straight to the browser.
    """
    return "\n".join(
        line.lstrip() for line in html.splitlines() if line.strip()
    )


EMPTY_STATE_HTML = _flatten_html(
    _radar_html(alert=False)
    + "<div class='empty-state'>Enter a query above to begin &#8594;</div>"
)


@st.cache_data(ttl=300, show_spinner=False)
def render_results(query: str) -> str:
    """Run the pipeline and return the full results HTML (radar + mode + cards).

    Cached for 5 minutes per query, so repeat searches — same query typed
    twice, or the same chip clicked again — return instantly instead of
    re-running the whole retrieve → embed → classify → rank pipeline.
    """
    try:
        output = run_pipeline_live(query.strip(), top_k=5)
    except Exception as e:
        return _flatten_html(
            _radar_html(alert=False)
            + f"<div class='empty-state' style='color:#FF4F5C'>Couldn't reach the news feed. Try again in a moment.<br/><span style='opacity:0.5; font-size:0.75rem'>({type(e).__name__})</span></div>"
        )

    mode = output["mode"]
    results = output["results"]
    is_emergency = mode == "emergency"

    if not results:
        return (
            _radar_html(alert=is_emergency)
            + "<div class='empty-state'>No articles matched your query in the last 30 days.</div>"
        )

    radar_html = _radar_html(alert=is_emergency)
    badge_label = "Emergency mode" if is_emergency else "Standard mode"
    badge_note = (
        "Freshness + credibility weighted heavily &mdash; surfacing the newest, most reliable information first."
        if is_emergency else
        "Relevance weighted heavily &mdash; standard topical ranking."
    )
    mode_class = "emergency" if is_emergency else "standard"
    accent = "var(--emergency)" if is_emergency else "var(--standard)"

    header_html = f"""
    <div id="results-anchor"></div>
    <div class="mode-row">
      <span class="mode-dot {mode_class}"></span>
      <span class="mode-badge {mode_class}">{badge_label}</span>
    </div>
    <div class="mode-note">{badge_note}</div>
    """

    cards = []
    for i, r in enumerate(results, 1):
        b = r["breakdown"]
        w = b["weights_used"]
        bars = (
            _bar("RELEVANCE", b["relevance"], "r")
            + _bar("CREDIBILITY", b["credibility"], "c")
            + _bar("FRESHNESS", b["freshness"], "f")
        )
        cards.append(f"""
        <div class="result-card" style="--accent:{accent}">
            <div class="rank">RESULT {i:02d}</div>
            <h3><a href="{r.get('link', '#')}" target="_blank" style="color:inherit; text-decoration:none;">{r['title']} &#8599;</a></h3>
            <div class="result-meta">
                <span>{r['source']}</span> &nbsp;&middot;&nbsp; <span>{r['publish_date']}</span> &nbsp;&middot;&nbsp;
                <span class="score">SCORE {r['final_score']:.3f}</span>
            </div>
            <div class="signal-bars">{bars}</div>
            <div class="result-text">{r['text']}</div>
            <div class="weights-note">weights[{mode}] &nbsp; w_r={w['w_r']} &nbsp; w_c={w['w_c']} &nbsp; w_f={w['w_f']}</div>
        </div>
        """)

    return _flatten_html(radar_html + header_html + "\n".join(cards))


# ---------------------------------------------------------------------------
# Session state + callbacks
# ---------------------------------------------------------------------------
# Streamlit widget rules require that any change to a widget's key in
# session_state happens BEFORE the widget is created for the current run.
# Callbacks fire before the next script run, so they're the safe place to
# (a) populate the query box from a chip click and (b) mark a pending
# search that we execute below, after the widgets have been declared.

if "results_html" not in st.session_state:
    st.session_state.results_html = EMPTY_STATE_HTML
# The "controlled" query string we own. The widget key is different
# (`query_widget_v2`) — this side-steps a Streamlit bug where writing to a
# widget's own key from a callback doesn't always update what the widget
# displays on the next render.
if "controlled_query" not in st.session_state:
    st.session_state.controlled_query = ""
# Bump the widget key when we programmatically change the query. This
# forces Streamlit to re-instantiate the widget with the new value= arg,
# because the key has changed. Ugly but reliable.
if "widget_gen" not in st.session_state:
    st.session_state.widget_gen = 0


def _search_from_input():
    """Search button callback — uses whatever is currently in the query widget."""
    widget_key = f"query_widget_v{st.session_state.widget_gen}"
    q = st.session_state.get(widget_key, "").strip()
    if q:
        st.session_state.controlled_query = q
        st.session_state._pending_query = q


def _search_from_chip(q: str):
    """Chip click callback — writes the query into the box AND marks pending.

    Bumps widget_gen so the text_input re-instantiates with the new value.
    """
    q = q.strip()
    if not q:
        return
    st.session_state.controlled_query = q
    st.session_state._pending_query = q
    st.session_state.widget_gen += 1


# ---------------------------------------------------------------------------
# Render page
# ---------------------------------------------------------------------------
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)
st.markdown(NAV_HTML, unsafe_allow_html=True)
st.markdown(HERO_HTML, unsafe_allow_html=True)

# Search row — centered container
st.write("")  # small spacer
_, center_col, _ = st.columns([1, 5, 1])
with center_col:
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        st.text_input(
            "Query",
            value=st.session_state.controlled_query,
            placeholder="e.g. wildfire evacuation zones california",
            label_visibility="collapsed",
            key=f"query_widget_v{st.session_state.widget_gen}",
            on_change=_search_from_input,
        )
    with btn_col:
        st.button(
            "SEARCH",
            type="primary",
            key="search_btn",
            on_click=_search_from_input,
        )

    # Example chips grouped by intent
    st.markdown(
        "<div class='examples-title'>Try one of these &mdash; each shows a different mode</div>",
        unsafe_allow_html=True,
    )

    EXAMPLES = [
        ("live", "LIVE", "wildfire evacuation zones california", "earthquake tsunami warning japan"),
        ("debunk", "MISINFO", "5g towers cause covid", "vaccine microchip conspiracy"),
        ("history", "HISTORY", "how did the fukushima disaster unfold", "hurricane katrina timeline"),
    ]

    for cls, label, q1, q2 in EXAMPLES:
        lbl_col, chip1_col, chip2_col = st.columns([1, 2, 2])
        with lbl_col:
            st.markdown(
                f"<div class='example-label {cls}'><span class='lbl-dot'></span>{label}</div>",
                unsafe_allow_html=True,
            )
        with chip1_col:
            st.button(q1, key=f"ex_{cls}_1", on_click=_search_from_chip, args=(q1,))
        with chip2_col:
            st.button(q2, key=f"ex_{cls}_2", on_click=_search_from_chip, args=(q2,))

    # Execute pending search now that widgets are declared. The spinner
    # displays here so the user sees "Ranking..." in the results area,
    # not somewhere else on the page.
    _pending = st.session_state.pop("_pending_query", None)
    if _pending:
        with st.spinner("Ranking..."):
            st.session_state.results_html = render_results(_pending)
        st.session_state._just_searched = True
        st.session_state.has_results = True

    # Scroll hint — shown once the user has run at least one search.
    # Backup UX for when Streamlit's iframe sandbox blocks auto-scroll.
    if st.session_state.get("has_results", False):
        st.markdown(
            "<div class='scroll-hint'>Scroll down to see your results "
            "<span class='arrow'>&#8595;</span></div>",
            unsafe_allow_html=True,
        )

    # Results area
    st.markdown(
        f"<div style='margin: 30px 0 40px 0'>{st.session_state.results_html}</div>",
        unsafe_allow_html=True,
    )

# Bottom sections — full width
st.markdown(RANKS_STRIP_HTML, unsafe_allow_html=True)
st.markdown(SOURCES_STRIP_HTML, unsafe_allow_html=True)
st.markdown(FOOTER_HTML, unsafe_allow_html=True)

# Auto-scroll to the results. The race we're fighting: Streamlit sometimes
# commits the results HTML to the DOM before this script fires, sometimes
# after. If the anchor element isn't there yet, scrollIntoView silently
# does nothing. Fix is to watch for the anchor via MutationObserver, then
# keep scrolling for a beat afterward to overpower any late Streamlit
# re-renders that might reset the scroll position.
if st.session_state.pop("_just_searched", False):
    components.html(
        """
        <script>
        (function() {
            const targetId = 'results-anchor';

            function getParentDoc() {
                for (const ctx of [window.top, window.parent]) {
                    try {
                        if (ctx && ctx.document) return ctx.document;
                    } catch (e) {}
                }
                return null;
            }

            function scrollNow(doc) {
                const el = doc.getElementById(targetId) || doc.querySelector('.mode-row');
                if (el) {
                    el.scrollIntoView({behavior: 'smooth', block: 'start'});
                    return true;
                }
                return false;
            }

            function forceHashScroll() {
                for (const ctx of [window.top, window.parent]) {
                    try {
                        if (ctx && ctx.location) {
                            ctx.location.hash = '';
                            ctx.location.hash = targetId;
                            return true;
                        }
                    } catch (e) {}
                }
                return false;
            }

            const doc = getParentDoc();
            if (!doc) {
                // Zero DOM access — fall back to pure hash-based navigation
                setTimeout(forceHashScroll, 200);
                return;
            }

            // First: try scrolling immediately in case the anchor is already there
            let scrolled = scrollNow(doc);

            // Second: if the anchor isn't there yet, watch for it
            if (!scrolled) {
                const observer = new MutationObserver(() => {
                    if (scrollNow(doc)) {
                        observer.disconnect();
                        scrolled = true;
                    }
                });
                observer.observe(doc.body, {childList: true, subtree: true});
                // Stop observing after 3s no matter what — belt-and-suspenders
                setTimeout(() => observer.disconnect(), 3000);
            }

            // Third: for 800ms after the initial scroll, keep re-asserting it
            // every animation frame. This defeats any late Streamlit reflows
            // that might reset the scroll position back to the top.
            const start = Date.now();
            function keepScrolling() {
                if (scrolled) scrollNow(doc);
                if (Date.now() - start < 800) requestAnimationFrame(keepScrolling);
            }
            requestAnimationFrame(keepScrolling);

            // Fourth: hash-based fallback in case scrollIntoView is a no-op
            setTimeout(forceHashScroll, 400);
        })();
        </script>
        """,
        height=0,
    )
