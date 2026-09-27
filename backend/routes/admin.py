"""
DecryptTrace – Admin Routes
GET /api/admin/users           – List all users
GET /api/admin/logs            – Full access log
GET /api/admin/stats           – System statistics
PUT /api/admin/users/<id>/role – Change user role
"""

from flask import Blueprint, request, jsonify, g

from database.db import get_db
from routes.auth import token_required

admin_bp = Blueprint('admin', __name__)


def _admin_only(f):
    from functools import wraps
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/users', methods=['GET'])
@_admin_only
def list_users():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return jsonify({"users": [dict(r) for r in rows]}), 200
    finally:
        db.close()


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@_admin_only
def change_role(user_id):
    data = request.get_json(silent=True) or {}
    new_role = data.get('role', '')
    if new_role not in ('user', 'admin', 'auditor'):
        return jsonify({"error": "Invalid role. Must be: user, admin, auditor"}), 400

    db = get_db()
    try:
        row = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404

        db.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        db.commit()
        return jsonify({"message": f"Role updated to '{new_role}'"}), 200
    finally:
        db.close()


@admin_bp.route('/logs', methods=['GET'])
@_admin_only
def access_logs():
    limit = min(int(request.args.get('limit', 100)), 500)
    db = get_db()
    try:
        rows = db.execute(
            """SELECT al.*, u.username
               FROM access_log al
               LEFT JOIN users u ON u.id = al.user_id
               ORDER BY al.timestamp DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
        return jsonify({"logs": [dict(r) for r in rows]}), 200
    finally:
        db.close()


@admin_bp.route('/stats', methods=['GET'])
@_admin_only
def stats():
    db = get_db()
    try:
        total_users = db.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
        total_files = db.execute("SELECT COUNT(*) as c FROM files WHERE is_deleted=0").fetchone()['c']
        total_decryptions = db.execute("SELECT COUNT(*) as c FROM provenance_records").fetchone()['c']
        failed_attempts = db.execute(
            "SELECT COUNT(*) as c FROM access_log WHERE success=0"
        ).fetchone()['c']
        recent_activity = db.execute(
            """SELECT al.action, al.timestamp, u.username, al.success
               FROM access_log al
               LEFT JOIN users u ON u.id = al.user_id
               ORDER BY al.timestamp DESC LIMIT 10"""
        ).fetchall()

        return jsonify({
            "stats": {
                "total_users": total_users,
                "total_files": total_files,
                "total_decryptions": total_decryptions,
                "failed_attempts": failed_attempts,
            },
            "recent_activity": [dict(r) for r in recent_activity]
        }), 200
    finally:
        db.close()
