"""
DecryptTrace – File Routes
POST /api/files/upload    – Upload and encrypt a file
GET  /api/files/          – List all files (own or admin sees all)
GET  /api/files/<id>      – Get file metadata
DELETE /api/files/<id>    – Soft-delete a file (admin only)
"""

import os
import json
import datetime
import uuid

from flask import Blueprint, request, jsonify, g, send_file
from werkzeug.utils import secure_filename

from database.db import get_db
from utils.crypto import encrypt_file, hash_bytes
from routes.auth import token_required

files_bp = Blueprint('files', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'csv', 'json', 'xml', 'png', 'jpg', 'jpeg'}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _ensure_upload_dir():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file():
    """Upload a file – it will be AES-256 encrypted at rest."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    file_bytes = file.read()
    if len(file_bytes) == 0:
        return jsonify({"error": "File is empty"}), 400

    # Hash the original file
    file_hash = hash_bytes(file_bytes)

    # Encrypt
    encrypted = encrypt_file(file_bytes)

    # Save encrypted payload to disk
    _ensure_upload_dir()
    safe_name = secure_filename(file.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}.enc"
    stored_path = os.path.join(UPLOAD_FOLDER, stored_name)

    with open(stored_path, 'w', encoding='utf-8') as f_out:
        json.dump(encrypted, f_out)

    # Save metadata to DB
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO files (filename, original_name, file_hash, encrypted_path, uploaded_by)
               VALUES (?, ?, ?, ?, ?)""",
            (stored_name, safe_name, file_hash, stored_path, g.current_user['id'])
        )
        db.commit()
        file_id = cur.lastrowid

        # Log
        db.execute(
            "INSERT INTO access_log (user_id, action, file_id, ip_address, success) VALUES (?,?,?,?,1)",
            (g.current_user['id'], 'UPLOAD', file_id, request.remote_addr)
        )
        db.commit()

        return jsonify({
            "message": "File uploaded and encrypted successfully",
            "file": {
                "id": file_id,
                "original_name": safe_name,
                "file_hash": file_hash,
                "uploaded_at": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }), 201

    finally:
        db.close()


@files_bp.route('/', methods=['GET'])
@token_required
def list_files():
    """List files. Admins/auditors see all; regular users see only their own."""
    db = get_db()
    try:
        role = g.current_user['role']
        uid = g.current_user['id']

        if role in ('admin', 'auditor'):
            rows = db.execute(
                """SELECT f.*, u.username as uploader_name
                   FROM files f
                   JOIN users u ON u.id = f.uploaded_by
                   WHERE f.is_deleted = 0
                   ORDER BY f.uploaded_at DESC"""
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT f.*, u.username as uploader_name
                   FROM files f
                   JOIN users u ON u.id = f.uploaded_by
                   WHERE f.uploaded_by = ? AND f.is_deleted = 0
                   ORDER BY f.uploaded_at DESC""",
                (uid,)
            ).fetchall()

        files_list = [dict(r) for r in rows]
        # Remove the local path from response for security
        for f in files_list:
            f.pop('encrypted_path', None)

        return jsonify({"files": files_list}), 200

    finally:
        db.close()


@files_bp.route('/<int:file_id>', methods=['GET'])
@token_required
def get_file(file_id):
    """Get metadata for a single file."""
    db = get_db()
    try:
        row = db.execute(
            """SELECT f.*, u.username as uploader_name
               FROM files f JOIN users u ON u.id = f.uploaded_by
               WHERE f.id = ? AND f.is_deleted = 0""",
            (file_id,)
        ).fetchone()

        if not row:
            return jsonify({"error": "File not found"}), 404

        # Permission: only owner, admin, or auditor
        role = g.current_user['role']
        if role not in ('admin', 'auditor') and row['uploaded_by'] != g.current_user['id']:
            return jsonify({"error": "Access denied"}), 403

        data = dict(row)
        data.pop('encrypted_path', None)
        return jsonify({"file": data}), 200

    finally:
        db.close()


@files_bp.route('/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(file_id):
    """Soft-delete a file (admin only)."""
    if g.current_user['role'] != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    db = get_db()
    try:
        row = db.execute("SELECT id FROM files WHERE id = ? AND is_deleted = 0", (file_id,)).fetchone()
        if not row:
            return jsonify({"error": "File not found"}), 404

        db.execute("UPDATE files SET is_deleted = 1 WHERE id = ?", (file_id,))
        db.execute(
            "INSERT INTO access_log (user_id, action, file_id, ip_address, success) VALUES (?,?,?,?,1)",
            (g.current_user['id'], 'DELETE_FILE', file_id, request.remote_addr)
        )
        db.commit()
        return jsonify({"message": "File deleted successfully"}), 200

    finally:
        db.close()
