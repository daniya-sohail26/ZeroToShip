"""
app.py — TradePost Phase 5 (Final)
===================================
Application factory wiring all phases into one unified server:
  - Phase 1/3: TradeStore business logic & flat-file persistence
  - Phase 2:   JWT auth (register / login)
  - Phase 3:   REST API endpoints (/api/*)
  - Phase 4/5: Jinja2 HTML pages served by Flask (/, /dashboard, /login, /register)

Session strategy: JWT stored in localStorage by the browser.
All page routes use Flask's render_template(); the API routes return JSON.
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
        return jsonify({"status": "ok", "phase": 5}), 200

    # ── Global error handlers ──────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        # Return JSON for API paths, HTML page otherwise
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
    print(f"\n  TradePost  — Phase 5 Final")
    print(f"  http://127.0.0.1:{port}\n")
    application.run(host="0.0.0.0", port=port)
