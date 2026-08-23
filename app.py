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
    --text: #F1EFF7;
    --muted: #8B85A3;
    --standard: #9B7CFF;
    --standard-dim: #201546;
    --emergency: #FF4F5C;
    --emergency-dim: #3B0F1A;
    --star: rgba(255,255,255,0.55);
}

* { box-sizing: border-box; }
body, .gradio-container {
    background: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    position: relative;
}
.gradio-container { max-width: 980px !important; margin: 0 auto !important; }
footer { display: none !important; }

/* Starfield + nebula backdrop */
.gradio-container::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: -2;
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
    background-size: 100% 100%;
    animation: twinkle 5s ease-in-out infinite alternate;
}
.gradio-container::after {
    content: '';
    position: fixed;
    inset: 0;
    z-index: -1;
    background:
        radial-gradient(ellipse 800px 500px at 15% -5%, rgba(155,124,255,0.16), transparent 60%),
        radial-gradient(ellipse 700px 450px at 100% 15%, rgba(255,79,92,0.07), transparent 60%),
        radial-gradient(ellipse 600px 600px at 50% 110%, rgba(120,90,220,0.12), transparent 60%);
}
@keyframes twinkle { 0% { opacity: 0.6; } 100% { opacity: 1; } }

#hero { padding: 44px 0 6px 0; text-align: center; }
#hero .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.35em;
    color: var(--standard);
    text-transform: uppercase;
    margin-bottom: 10px;
}
#hero h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 900 !important;
    font-size: 5rem !important;
    line-height: 0.95 !important;
    color: var(--text) !important;
    margin: 0 0 14px 0 !important;
    text-transform: uppercase;
    text-shadow: 0 0 40px rgba(155,124,255,0.35);
}
#hero p {
    color: var(--muted) !important;
    font-size: 1.02rem !important;
    max-width: 560px;
    margin: 0 auto 30px auto !important;
    line-height: 1.5;
}

/* Radar sweep */
#radar-wrap { display: flex; justify-content: center; margin-bottom: 32px; }
.radar {
    width: 120px; height: 120px;
    border-radius: 50%;
    position: relative;
    border: 1px solid rgba(155,124,255,0.25);
    background: radial-gradient(circle, rgba(155,124,255,0.06) 0%, transparent 70%);
}
.radar::before, .radar::after {
    content: '';
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(155,124,255,0.15);
}
.radar::before { inset: 20px; }
.radar::after { inset: 40px; }
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

#query-row { gap: 10px !important; margin-bottom: 4px !important; }
#query-row textarea, #query-row input {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.02rem !important;
    padding: 16px 18px !important;
}
#query-row textarea:focus, #query-row input:focus {
    border-color: var(--standard) !important;
    box-shadow: 0 0 0 3px rgba(155,124,255,0.18) !important;
}

#search-btn {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: var(--standard) !important;
    color: #0B0616 !important;
    border: none !important;
    border-radius: 10px !important;
    min-width: 140px !important;
    box-shadow: 0 0 20px rgba(155,124,255,0.35);
}
#search-btn:hover { filter: brightness(1.12); transform: translateY(-1px); }

.mode-row { display: flex; align-items: baseline; gap: 14px; margin: 34px 0 4px 0; }
.mode-badge {
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.mode-badge.standard { color: var(--standard); }
.mode-badge.emergency { color: var(--emergency); }
.mode-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.mode-dot.standard { background: var(--standard); box-shadow: 0 0 10px var(--standard); }
.mode-dot.emergency { background: var(--emergency); box-shadow: 0 0 10px var(--emergency); animation: dot-pulse 1s ease-in-out infinite; }
@keyframes dot-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
.mode-note { color: var(--muted); font-size: 0.92rem; margin-bottom: 26px; }

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
    padding: 40px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.9rem;
}
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


def search(query: str):
    if not query or not query.strip():
        return (
            _radar_html(alert=False),
            "",
            "<div class='empty-state'>ENTER A QUERY AND HIT SEARCH TO BEGIN &#8594;</div>",
        )

    output = run_pipeline_live(query, top_k=5)
    mode = output["mode"]
    results = output["results"]
    is_emergency = mode == "emergency"

    radar_html = _radar_html(alert=is_emergency)

    badge_label = "EMERGENCY MODE" if is_emergency else "STANDARD MODE"
    badge_note = (
        "Freshness + credibility weighted heavily — surfacing the newest, most reliable information first."
        if is_emergency else
        "Relevance weighted heavily — standard topical ranking."
    )
    mode_class = "emergency" if is_emergency else "standard"
    header_html = f"""
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
                <span>{r['source']}</span> &nbsp;·&nbsp; <span>{r['publish_date']}</span> &nbsp;·&nbsp;
                <span class="score">SCORE {r['final_score']:.3f}</span>
            </div>
            <div class="signal-bars">{bars}</div>
            <div class="result-text">{r['text']}</div>
            <div class="weights-note">weights[{mode}] &nbsp; w_r={w['w_r']} &nbsp; w_c={w['w_c']} &nbsp; w_f={w['w_f']}</div>
        </div>
        """
        cards.append(card)

    return radar_html, header_html, "\n".join(cards)


with gr.Blocks(title="Signal — Crisis-Aware Search", css=CUSTOM_CSS, theme=gr.themes.Base()) as demo:
    with gr.Column(elem_id="hero"):
        gr.HTML("<div class='eyebrow'>CRISIS-AWARE CREDIBILITY RANKER</div>")
        gr.HTML("<h1>Signal</h1>")
        gr.HTML(
            "<p>Auto-detects whether a query is an active emergency or a standard "
            "lookup, and re-weights relevance, credibility, and freshness in real time.</p>"
        )

    radar_display = gr.HTML(_radar_html(alert=False))

    with gr.Row(elem_id="query-row"):
        query_input = gr.Textbox(
            placeholder="wildfire evacuation Napa right now",
            show_label=False,
            scale=5,
            container=False,
        )
        search_button = gr.Button("Search", elem_id="search-btn", scale=1)

    mode_display = gr.HTML()
    results_display = gr.HTML("<div class='empty-state'>ENTER A QUERY AND HIT SEARCH TO BEGIN &#8594;</div>")

    search_button.click(fn=search, inputs=query_input,
                         outputs=[radar_display, mode_display, results_display])
    query_input.submit(fn=search, inputs=query_input,
                        outputs=[radar_display, mode_display, results_display])

    gr.Examples(
        examples=[
            "wildfire evacuation Napa right now",
            "history of earthquakes in Japan",
            "hurricane landfall Gulf Coast",
            "vaccine microchip conspiracy",
        ],
        inputs=query_input,
    )

if __name__ == "__main__":
    demo.launch()