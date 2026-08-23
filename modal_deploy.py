"""
Deploy Signal (crisis-aware search) to Modal.

Prereqs (run in your shell, from the factchecker/ directory):

  pip install modal
  modal setup                                              # opens browser to auth

  # Create a persistent volume for the fine-tuned checkpoint (one-time)
  modal volume create signal-checkpoints
  modal volume put signal-checkpoints checkpoints/best_model.pt best_model.pt

  # Deploy
  modal deploy modal_deploy.py

Modal prints a URL like `https://<username>--signal-ui.modal.run` on success.
That is your permanent shareable URL.
"""
import modal

# ------------------------------------------------------------------
# Image: CPU-only torch (~200MB vs ~6GB for the CUDA build). The app
# doesn't use a GPU, so we save massive amounts of build time and disk.
# transformers pinned <4.44 to dodge a known bug in tensor_parallel.py
# where AllReduceBackward references `torch` before it's bound in the
# module namespace, triggering NameError during library import.
# ------------------------------------------------------------------
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.2,<2.5",
        index_url="https://download.pytorch.org/whl/cpu",
    )
    .pip_install(
        "transformers>=4.40,<4.44",
        "sentence-transformers>=2.7,<3.1",
        "peft>=0.10,<0.14",
        "gradio==4.44.1",           # exact pin — dodges TemplateResponse signature bug
        "starlette>=0.37,<0.38",    # matches what gradio 4.44 expects
        "fastapi>=0.110,<0.112",    # pulls a compatible starlette
        "scikit-learn>=1.4",
        "numpy<2",
        "pandas>=2.2",
    )
    .env({"SIGNAL_CKPT_PATH": "/checkpoints/best_model.pt"})
    .add_local_python_source("app", "src")
)

app = modal.App("signal", image=image)
checkpoint_volume = modal.Volume.from_name("signal-checkpoints", create_if_missing=True)


@app.function(
    volumes={"/checkpoints": checkpoint_volume},
    memory=2048,
    cpu=2.0,
    scaledown_window=600,
    min_containers=1,        # always warm. Flip back to 0 after recording.
    max_containers=1,
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def ui():
    """Serve the Gradio Blocks over Modal's ASGI runtime, plus a plain
    FastAPI endpoint that bypasses Gradio's queue entirely.

    Why the bypass: Gradio's queue uses long-lived SSE streams that need
    per-container session affinity. On Modal, requests get load-balanced
    unpredictably even with min_containers=max_containers=1 — the SSE
    stream that carries the result almost never lands on the same
    container as the join, so it 503s in <1 second with an opaque
    "unexpected_error". Config tweaks can't fix this; the transport is
    the wrong shape.

    /api/search is a plain synchronous POST. It calls the same search()
    function the Gradio button calls, but the client hits it directly via
    fetch() (see app.py's <script> tag). No queue, no SSE, no session
    state, no lottery. If it fails, it fails visibly with a real HTTP
    status code.
    """
    from fastapi import FastAPI, Form, Request
    from fastapi.responses import HTMLResponse
    import gradio as gr

    from app import demo, search

    web_app = FastAPI()

    # ------------------------------------------------------------------
    # Social scraper middleware
    # ------------------------------------------------------------------
    # Gradio injects its own og:*/twitter:* meta tags into the head, and
    # even when we pass head= into gr.Blocks() our tags are just appended
    # alongside the defaults. Social scrapers (LinkedIn, Facebook, Slack,
    # Twitter) then pick unpredictably between the duplicates, and the
    # LinkedIn preview ends up pointing at gradio.app with a blank image.
    #
    # The fix: when a request's User-Agent identifies it as a social
    # scraper, we short-circuit before Gradio ever sees it and return a
    # minimal HTML page with ONLY our meta tags. Humans hitting the URL
    # in a real browser fall through to the normal Gradio app.

    SOCIAL_SCRAPER_UAS = (
        "linkedinbot", "facebookexternalhit", "facebookcatalog",
        "twitterbot", "slackbot", "slack-imgproxy",
        "whatsapp", "telegram", "discordbot",
        "skypeuripreview", "redditbot", "pinterest",
    )

    SOCIAL_LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Signal &mdash; Crisis-Aware Search Reranker</title>
<meta name="description" content="Signal auto-detects whether your query is an active emergency or a standard lookup, then re-weights relevance, credibility, and freshness in real time. Crisis-aware search reranker." />

<meta property="og:type" content="website" />
<meta property="og:site_name" content="Signal" />
<meta property="og:title" content="Signal &mdash; Crisis-Aware Search Reranker" />
<meta property="og:description" content="Ranks news the way a newsroom would, not the way a search engine does. Auto-detects emergencies and re-weights credibility, freshness, and relevance in real time." />
<meta property="og:url" content="https://jaya242--signal-ui.modal.run" />
<meta property="og:image" content="https://raw.githubusercontent.com/Jaya242/CRISIS-SEARCH/main/docs/og-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Signal - crisis-aware news reranker with emergency mode showing red radar and ranked results" />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Signal &mdash; Crisis-Aware Search Reranker" />
<meta name="twitter:description" content="Ranks news the way a newsroom would, not the way a search engine does." />
<meta name="twitter:image" content="https://raw.githubusercontent.com/Jaya242/CRISIS-SEARCH/main/docs/og-image.png" />
</head>
<body style="font-family: system-ui, sans-serif; background: #050308; color: #F1EFF7; padding: 40px; max-width: 640px; margin: 0 auto;">
<h1>Signal</h1>
<p>Crisis-aware search reranker. <a href="https://jaya242--signal-ui.modal.run" style="color:#9B7CFF">Open the demo &rarr;</a></p>
<p><a href="https://github.com/Jaya242/CRISIS-SEARCH" style="color:#9B7CFF">Source on GitHub &rarr;</a></p>
</body>
</html>
"""

    @web_app.middleware("http")
    async def social_scraper_middleware(request: Request, call_next):
        if request.url.path in ("/", ""):
            ua = request.headers.get("user-agent", "").lower()
            if any(bot in ua for bot in SOCIAL_SCRAPER_UAS):
                return HTMLResponse(SOCIAL_LANDING_HTML)
        return await call_next(request)

    @web_app.post("/api/search", response_class=HTMLResponse)
    def api_search(query: str = Form("")):
        try:
            return search(query)
        except Exception as e:
            return HTMLResponse(
                content=(
                    "<div class='empty-state' style='color:#FF4F5C'>"
                    f"Search error: {type(e).__name__}. Please try again."
                    "</div>"
                ),
                status_code=500,
            )

    return gr.mount_gradio_app(web_app, demo, path="/")
