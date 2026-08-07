"""
app.py — TradePost
==================
Application factory wiring auth, REST API, and Jinja2 page routes
into a single Flask server.

Session strategy: JWT stored in localStorage and as `tp_token` cookie.
Page routes use Flask render_template(); API routes return JSON.
"""

import os
import jwt
from flask import Flask, render_template, redirect, url_for, request, jsonify

from views.auth   import auth_bp
from views.routes import api_bp
from views.pages  import pages_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Config ────────────────────────────────────────────────────────
    app.config["JWT_SECRET"] = os.environ.get(
        "JWT_SECRET", "CHANGE_ME_before_deploying_to_production"
    )
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

    # ── Blueprints ────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)    # POST /auth/register, /auth/login
    app.register_blueprint(api_bp)     # /api/posts, /api/offers, …
    app.register_blueprint(pages_bp)   # GET /, /dashboard, /login, /register

    # Custom Jinja2 filters
    app.jinja_env.filters['chr'] = chr

    # ── Liveness ──────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ── Global error handlers ──────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/") or request.path.startswith("/auth/"):
            return jsonify({"error": "Endpoint not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error."}), 500

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application = create_app()
    print(f"\n  TradePost — Peer-to-Peer Barter Exchange")
    print(f"  http://127.0.0.1:{port}\n")
    application.run(host="0.0.0.0", port=port)
