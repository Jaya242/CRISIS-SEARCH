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
    scaledown_window=600,   # keep warm 10 min after last request
    min_containers=0,        # scale to zero when idle (free tier friendly)
    max_containers=1,
)
@modal.concurrent(max_inputs=10)
@modal.asgi_app()
def ui():
    """Serve the Gradio Blocks over Modal's ASGI runtime."""
    from fastapi import FastAPI
    import gradio as gr

    # Import here (inside the container), not at module top level:
    # the app module loads torch + the fine-tuned classifier, which
    # only exist inside the Modal image.
    from app import demo

    # Gradio 4.x requires .queue() before mounting into FastAPI,
    # otherwise event handlers (button click, textbox submit) 500 at
    # request time with a "queue not initialized" style error.
    demo.queue()

    web_app = FastAPI()
    return gr.mount_gradio_app(web_app, demo, path="/")
