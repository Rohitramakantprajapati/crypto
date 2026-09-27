"""
DecryptTrace – Flask Application Entry Point
Production-ready: works with gunicorn (Render.com) and locally.
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "decrypttrace_secret_key_change_in_prod")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # CORS – allow all origins (lock down in production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Init DB ────────────────────────────────────────────────────────────────
    from database.db import init_db
    with app.app_context():
        init_db()

    # ── Register Blueprints ────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.files import files_bp
    from routes.provenance import provenance_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp,       url_prefix='/api/auth')
    app.register_blueprint(files_bp,      url_prefix='/api/files')
    app.register_blueprint(provenance_bp, url_prefix='/api/provenance')
    app.register_blueprint(admin_bp,      url_prefix='/api/admin')

    # ── Health Check ───────────────────────────────────────────────────────────
    @app.route('/')
    @app.route('/api/health')
    def health():
        return {"status": "ok", "service": "DecryptTrace API", "version": "1.0.0"}, 200

    # ── Global Error Handlers ──────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Endpoint not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"error": "Method not allowed"}, 405

    @app.errorhandler(413)
    def too_large(e):
        return {"error": "File too large. Maximum size is 16 MB"}, 413

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error"}, 500

    return app


# Gunicorn entry point
application = create_app()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    application.run(host='0.0.0.0', port=port, debug=debug)
