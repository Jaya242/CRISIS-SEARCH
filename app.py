"""
Gradio UI for the crisis-aware fact-checker.
Run: python app.py
"""
import gradio as gr

from src.live_pipeline import run_pipeline_live

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

* { box-sizing: border-box; }
html, body { margin: 0 !important; padding: 0 !important; background: var(--bg) !important; }
body, .gradio-container {
    background: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text);
    position: relative;
}
.gradio-container,
.gradio-container > .main,
.gradio-container .contain,
.gradio-container .wrap,
gradio-app,
gradio-app > .gradio-container {
    max-width: 100vw !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: var(--bg) !important;
}
footer { display: none !important; }

/* Layered background: stars, orbs, grain */
body::before {
    content: '';
    position: fixed; inset: 0; z-index: -3; pointer-events: none;
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
    position: fixed; inset: 0; z-index: -2; pointer-events: none;
    background:
        radial-gradient(ellipse 1000px 620px at 20% -5%, rgba(155,124,255,0.20), transparent 60%),
        radial-gradient(ellipse 720px 460px at 100% 12%, rgba(255,79,92,0.09), transparent 60%),
        radial-gradient(ellipse 640px 600px at 50% 108%, rgba(120,90,220,0.14), transparent 60%);
}
@keyframes twinkle { 0% { opacity: 0.55; } 100% { opacity: 1; } }

/* Reading columns constrain content on wide monitors */
.content-narrow { max-width: 900px; margin: 0 auto; padding: 0 40px; }
.content-mid    { max-width: 1120px; margin: 0 auto; padding: 0 40px; }
.content-wide   { max-width: 1280px; margin: 0 auto; padding: 0 40px; }

/* ------------------ TOP NAV ------------------ */
.top-nav {
    position: sticky; top: 0; z-index: 20;
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 40px;
    background: rgba(5,3,8,0.60);
    backdrop-filter: blur(14px) saturate(140%);
    -webkit-backdrop-filter: blur(14px) saturate(140%);
    border-bottom: 1px solid var(--border-soft);
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

/* ------------------ HERO ------------------ */
#hero { padding: 80px 0 8px 0; text-align: center; }
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
    font-size: 6.5rem !important;
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

/* ------------------ RADAR ------------------ */
#radar-wrap { display: flex; justify-content: center; margin: 44px 0 8px 0; }
.radar {
    width: 140px; height: 140px;
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
.radar::before { inset: 22px; }
.radar::after { inset: 46px; }
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

/* ------------------ QUERY ROW ------------------ */
#query-row { gap: 10px !important; margin: 0 auto !important; max-width: 860px !important; padding: 0 40px; }
#query-row textarea, #query-row input {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.02rem !important;
    padding: 18px 20px !important;
    box-shadow: 0 0 30px rgba(0,0,0,0.4);
}
#query-row textarea:focus, #query-row input:focus {
    border-color: var(--standard) !important;
    box-shadow: 0 0 0 3px rgba(155,124,255,0.22), 0 0 30px rgba(0,0,0,0.4) !important;
}
#search-btn {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    background: linear-gradient(180deg, #B096FF, var(--standard)) !important;
    color: #0B0616 !important;
    border: none !important;
    border-radius: 12px !important;
    min-width: 150px !important;
    box-shadow: 0 8px 24px rgba(155,124,255,0.35), inset 0 1px 0 rgba(255,255,255,0.3);
    transition: transform 0.15s, filter 0.15s;
}
#search-btn:hover { filter: brightness(1.10); transform: translateY(-1px); }

/* ------------------ EXAMPLES ------------------ */
.examples-wrap { max-width: 900px; margin: 20px auto 0 auto; padding: 0 40px; }
.examples-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: var(--muted);
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 14px;
}
.example-group {
    display: flex; align-items: center; gap: 12px;
    margin: 10px 0;
    flex-wrap: wrap;
}
.example-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.22em;
    color: var(--muted);
    text-transform: uppercase;
    min-width: 96px;
    display: flex; align-items: center; gap: 8px;
}
.example-label .lbl-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.example-label.live    .lbl-dot { background: var(--emergency); box-shadow: 0 0 8px var(--emergency); animation: dot-pulse 1s ease-in-out infinite; }
.example-label.debunk  .lbl-dot { background: var(--debunk); box-shadow: 0 0 8px var(--debunk); }
.example-label.history .lbl-dot { background: var(--standard); box-shadow: 0 0 8px var(--standard); }
@keyframes dot-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
button.example-chip {
    background: rgba(15,11,26,0.55) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 8px 14px !important;
    border-radius: 6px !important;
    min-height: auto !important;
    box-shadow: none !important;
    letter-spacing: 0.01em !important;
    text-transform: none !important;
    transition: border-color 0.15s, background 0.15s, transform 0.15s;
}
button.example-chip:hover {
    border-color: var(--standard) !important;
    background: rgba(32,21,70,0.45) !important;
    transform: translateY(-1px);
}

/* ------------------ MODE HEADER + RESULTS ------------------ */
.results-wrap { max-width: 1120px; margin: 0 auto; padding: 20px 40px 30px 40px; }
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

/* ------------------ HOW SIGNAL RANKS ------------------ */
.ranks-strip { max-width: 1280px; margin: 60px auto 0 auto; padding: 60px 40px 20px 40px; border-top: 1px solid var(--border); }
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

/* ------------------ SOURCES ------------------ */
.sources-strip { max-width: 1280px; margin: 0 auto; padding: 50px 40px 30px 40px; text-align: center; }
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
    opacity: 0.65;
    transition: opacity 0.2s, color 0.2s;
}
.source-item:hover { opacity: 1; color: var(--text); }
.sources-note {
    margin-top: 22px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.18em;
    color: #504A66;
    text-transform: uppercase;
}

/* ------------------ FOOTER ------------------ */
.site-footer {
    border-top: 1px solid var(--border);
    max-width: 1280px;
    margin: 30px auto 0 auto;
    padding: 30px 40px;
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
"""

BLIP_POSITIONS = [(18, 30), (85, 22), (62, 88), (30, 70), (75, 60)]

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
        <a href="https://github.com" target="_blank" class="nav-cta">GitHub &#8599;</a>
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
            <div class="desc">Semantic similarity between the query and each article, from a fine-tuned cross-encoder. The dominant signal in normal conditions.</div>
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
            <div class="desc">Source-level trust score derived from a publisher whitelist and historical accuracy. Weighted heavier in emergencies where rumor is expensive.</div>
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
    <div class="sources-label">Ingesting live from</div>
    <div class="sources-row">
        <span class="source-item">Reuters</span>
        <span class="source-item">Associated Press</span>
        <span class="source-item">BBC</span>
        <span class="source-item">NYT</span>
        <span class="source-item">The Guardian</span>
        <span class="source-item">NPR</span>
        <span class="source-item">USGS</span>
        <span class="source-item">NOAA</span>
    </div>
    <div class="sources-note">via Google News RSS &nbsp;&middot;&nbsp; publisher credibility scored per source</div>
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
        <a href="https://github.com" target="_blank">GitHub &#8599;</a>
    </div>
</div>
"""


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


EMPTY_STATE_HTML = (
    _radar_html(alert=False)
    + "<div class='empty-state'>Enter a query above to begin &#8594;</div>"
)


def search(query: str):
    if not query or not query.strip():
        return EMPTY_STATE_HTML

    output = run_pipeline_live(query, top_k=5)
    mode = output["mode"]
    results = output["results"]
    is_emergency = mode == "emergency"

    if not results:
        return (
            _radar_html(alert=is_emergency)
            + "<div class='empty-state'>No live results found &mdash; try a different query.</div>"
        )

    radar_html = _radar_html(alert=is_emergency)

    badge_label = "Emergency mode" if is_emergency else "Standard mode"
    badge_note = (
        "Freshness + credibility weighted heavily &mdash; surfacing the newest, most reliable information first."
        if is_emergency else
        "Relevance weighted heavily &mdash; standard topical ranking."
    )
    mode_class = "emergency" if is_emergency else "standard"
    header_html = f"""
    <div class="results-wrap">
      <div class="mode-row">
        <span class="mode-dot {mode_class}"></span>
        <span class="mode-badge {mode_class}">{badge_label}</span>
      </div>
      <div class="mode-note">{badge_note}</div>
    """

    accent = "var(--emergency)" if is_emergency else "var(--standard)"

    cards = []
    for i, r in enumerate(results, 1):
        b = r["breakdown"]
        w = b["weights_used"]
        bars = (
            _bar("RELEVANCE", b["relevance"], "r")
            + _bar("CREDIBILITY", b["credibility"], "c")
            + _bar("FRESHNESS", b["freshness"], "f")
        )
        card = f"""
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
        """
        cards.append(card)

    return radar_html + header_html + "\n".join(cards) + "</div>"


EXAMPLES = [
    ("live", "LIVE", [
        "wildfire evacuation zones california",
        "earthquake tsunami warning japan",
    ]),
    ("debunk", "MISINFO", [
        "5g towers cause covid",
        "vaccine microchip conspiracy",
    ]),
    ("history", "HISTORY", [
        "how did the fukushima disaster unfold",
        "hurricane katrina timeline",
    ]),
]


with gr.Blocks(title="Signal — Crisis-Aware Search", css=CUSTOM_CSS, theme=gr.themes.Base()) as demo:
    gr.HTML(NAV_HTML)
    gr.HTML(HERO_HTML)

    with gr.Row(elem_id="query-row"):
        query_input = gr.Textbox(
            placeholder="e.g. wildfire evacuation zones california",
            show_label=False,
            scale=5,
            container=False,
        )
        search_button = gr.Button("Search", elem_id="search-btn", scale=1)

    example_chips: list[tuple[gr.Button, str]] = []
    with gr.Column(elem_classes=["examples-wrap"]):
        gr.HTML("<div class='examples-title'>Try one of these &mdash; each shows a different mode</div>")
        for cls, label, queries in EXAMPLES:
            with gr.Row(elem_classes=["example-group"]):
                gr.HTML(
                    f"<div class='example-label {cls}'><span class='lbl-dot'></span>{label}</div>"
                )
                for q in queries:
                    btn = gr.Button(q, elem_classes=["example-chip"])
                    example_chips.append((btn, q))

    output_display = gr.HTML(EMPTY_STATE_HTML, elem_classes=["results-wrap"])

    search_button.click(fn=search, inputs=query_input, outputs=output_display)
    query_input.submit(fn=search, inputs=query_input, outputs=output_display)

    for btn, q in example_chips:
        btn.click(fn=lambda q=q: q, outputs=query_input) \
           .then(fn=search, inputs=query_input, outputs=output_display)

    gr.HTML(RANKS_STRIP_HTML)
    gr.HTML(SOURCES_STRIP_HTML)
    gr.HTML(FOOTER_HTML)

if __name__ == "__main__":
    demo.launch(share=True)
