"""
Gradio UI for the crisis-aware fact-checker.
Run: python app.py
"""
import gradio as gr

from src.pipeline import run_pipeline


def search(query: str):
    if not query or not query.strip():
        return "Enter a query above.", ""

    output = run_pipeline(query, top_k=5)
    mode = output["mode"]
    results = output["results"]

    mode_badge = "🚨 EMERGENCY MODE" if mode == "emergency" else "🔎 STANDARD MODE"
    mode_note = (
        "Freshness + credibility weighted heavily — prioritizing recent, reliable info."
        if mode == "emergency"
        else "Relevance weighted heavily — standard topical search."
    )

    result_blocks = []
    for i, r in enumerate(results, 1):
        b = r["breakdown"]
        block = f"""
### {i}. {r['title']}
**Source:** {r['source']} | **Published:** {r['publish_date']} | **Score:** {r['final_score']:.3f}

**Why this ranked here:**
- Relevance: {b['relevance']:.2f}
- Credibility: {b['credibility']:.2f}
- Freshness: {b['freshness']:.2f}
- Weights used ({mode}): w_r={b['weights_used']['w_r']}, w_c={b['weights_used']['w_c']}, w_f={b['weights_used']['w_f']}

{r['text']}
"""
        result_blocks.append(block)

    return f"## {mode_badge}\n{mode_note}", "\n---\n".join(result_blocks)


with gr.Blocks(title="Crisis-Aware Fact Checker") as demo:
    gr.Markdown("# Crisis-Aware Search & Credibility Ranker")
    gr.Markdown(
        "Searches a news corpus, auto-detects whether your query is an "
        "active emergency or a standard search, and re-weights relevance, "
        "credibility, and freshness accordingly."
    )

    query_input = gr.Textbox(
        label="Search query",
        placeholder="e.g. 'wildfire evacuation Napa right now' or 'history of earthquakes in Japan'",
    )
    search_button = gr.Button("Search", variant="primary")

    mode_display = gr.Markdown()
    results_display = gr.Markdown()

    search_button.click(fn=search, inputs=query_input, outputs=[mode_display, results_display])
    query_input.submit(fn=search, inputs=query_input, outputs=[mode_display, results_display])

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