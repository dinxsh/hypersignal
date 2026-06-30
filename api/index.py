"""Vercel Python entrypoint for the hypersignal API.

Deploy the repo root as a Vercel Python project; Vercel serves this FastAPI
``app``. Routes: GET /report, /signal, /lending, /whales, /flows, /healthz.

Set GOLDRUSH_API_KEY in the Vercel project's Environment Variables for live
data; without it the app serves the recorded fixtures so the deploy works out
of the box. The entrypoint is declared in pyproject.toml ([tool.vercel]).
"""
import os
import sys

# The hypersignal package lives in ../src (bundled with the deployment).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hypersignal.serve import create_app  # noqa: E402

app = create_app()
