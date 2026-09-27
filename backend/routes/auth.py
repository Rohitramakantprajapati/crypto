"""
DecryptTrace – Authentication Routes
POST /api/auth/register  – Register a new user (generates RSA keypair)
POST /api/auth/login     – Login, returns JWT
GET  /api/auth/me        – Return current user info
"""

import datetime
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db
from utils.crypto import generate_rsa_keypair

auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────────────
# JWT Helper
# ─────────────────────────────────────────────

def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    """Decorator: protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Authorization token missing"}), 401

        try:
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE id = ?", (payload["sub"],)
        ).fetchone()
        db.close()

        if not user:
            return jsonify({"error": "User not found"}), 401

        g.current_user = dict(user)
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator: require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = data.get('role', 'user')

    # Validation
    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if role not in ('user', 'admin', 'auditor'):
        role = 'user'

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone()
        if existing:
            return jsonify({"error": "Username or email already exists"}), 409

        # Generate RSA keypair for this user
        public_pem, private_pem = generate_rsa_keypair()
        password_hash = generate_password_hash(password)

        cur = db.execute(
            """INSERT INTO users (username, email, password_hash, role, public_key, private_key_enc)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, email, password_hash, role, public_pem, private_pem)
        )
        db.commit()
        user_id = cur.lastrowid

        token = create_token(user_id, role)

        return jsonify({
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "role": role,
                "public_key": public_pem
            }
        }), 201

    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, username)
        ).fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            # Log failed attempt
            db.execute(
                "INSERT INTO access_log (action, ip_address, success, details) VALUES (?,?,0,?)",
                ('LOGIN_FAILED', request.remote_addr, f"Failed login for: {username}")
            )
            db.commit()
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_token(user['id'], user['role'])

        # Log success
        db.execute(
            "INSERT INTO access_log (user_id, action, ip_address, success) VALUES (?,?,?,1)",
            (user['id'], 'LOGIN', request.remote_addr)
        )
        db.commit()

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "role": user['role'],
                "public_key": user['public_key']
            }
        }), 200

    finally:
        db.close()


@auth_bp.route('/me', methods=['GET'])
@token_required
def me():
    user = g.current_user
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "role": user['role'],
        "public_key": user['public_key'],
        "created_at": user['created_at']
    }), 200
