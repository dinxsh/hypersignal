"""Vercel Python serverless function: GET /api/report?coin=HYPE

Reuses the hypersignal engine. If GOLDRUSH_API_KEY is set in the Vercel project
env, it returns a live report; otherwise it serves the recorded fixtures so the
deployment still works out of the box. The dashboard also falls back to a
bundled snapshot if this function is unavailable, so the site never breaks.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import os
import sys

# The hypersignal package lives in ../src (included via vercel.json includeFiles).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hypersignal import Settings, run  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (Vercel/BaseHTTPRequestHandler API)
        coin = "HYPE"
        try:
            qs = parse_qs(urlparse(self.path).query)
            coin = (qs.get("coin") or ["HYPE"])[0].upper()
        except Exception:
            pass

        settings = Settings.from_env()
        offline = not settings.api_key
        try:
            report = run(settings, offline=offline, coin=coin)
            body = report.model_dump_json().encode("utf-8")
            status = 200
        except Exception as exc:  # never 500 the dashboard; report the error
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            status = 502

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        # Cache at the edge so a fleet of clients shares one upstream pull.
        self.send_header("Cache-Control", "s-maxage=15, stale-while-revalidate=60")
        self.end_headers()
        self.wfile.write(body)
