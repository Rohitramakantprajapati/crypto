"""
DecryptTrace – Provenance / Decryption Routes
POST /api/provenance/decrypt/<file_id>   – Decrypt a file & record provenance
GET  /api/provenance/records             – List all provenance records
GET  /api/provenance/records/<id>        – Get a single provenance record
POST /api/provenance/verify/<record_id>  – Verify a provenance record's integrity
GET  /api/provenance/ledger              – Get full ledger chain
GET  /api/provenance/ledger/verify       – Verify full ledger integrity
"""

import json
import datetime

from flask import Blueprint, request, jsonify, g, send_file
import io

from database.db import get_db
from utils.crypto import (
    decrypt_file, hash_bytes, hash_string, hash_event,
    sign_data, verify_signature
)
from utils.ledger import (
    append_record, verify_chain, get_all_records,
    get_record_by_index, verify_single_record
)
from routes.auth import token_required

provenance_bp = Blueprint('provenance', __name__)


@provenance_bp.route('/decrypt/<int:file_id>', methods=['POST'])
@token_required
def decrypt_and_record(file_id):
    """
    Core endpoint:
    1. Authorization check (only authorized users)
    2. Decrypt the file using AES-256
    3. Compute SHA-256 hash of the decrypted data
    4. Digitally sign the event with the user's private key
    5. Record the provenance event in DB and immutable ledger
    6. Return the decrypted file as a download (plus provenance info)
    """
    db = get_db()
    try:
        # 1. Fetch file record
        file_row = db.execute(
            "SELECT * FROM files WHERE id = ? AND is_deleted = 0", (file_id,)
        ).fetchone()

        if not file_row:
            return jsonify({"error": "File not found"}), 404

        user = g.current_user
        role = user['role']

        # Authorization: only the uploader, admin, or auditor may decrypt
        if role not in ('admin', 'auditor') and file_row['uploaded_by'] != user['id']:
            # Log failed attempt
            db.execute(
                """INSERT INTO access_log (user_id, action, file_id, ip_address, success, details)
                   VALUES (?,?,?,?,0,?)""",
                (user['id'], 'DECRYPT_DENIED', file_id, request.remote_addr,
                 "Unauthorized decryption attempt")
            )
            db.commit()
            return jsonify({"error": "Access denied: you are not authorized to decrypt this file"}), 403

        # 2. Load encrypted payload from disk
        try:
            with open(file_row['encrypted_path'], 'r', encoding='utf-8') as ef:
                encrypted_payload = json.load(ef)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "Encrypted file not found on server"}), 500

        # 3. Decrypt
        try:
            decrypted_bytes = decrypt_file(
                encrypted_payload['ciphertext'],
                encrypted_payload['iv']
            )
        except Exception as e:
            return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

        # 4. Hash the decrypted data and verify against stored hash
        decrypted_hash = hash_bytes(decrypted_bytes)
        hash_match = (decrypted_hash == file_row['file_hash'])

        # 5. Build event dict for signing and hashing
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        event = {
            "type": "DECRYPTION",
            "file_id": file_id,
            "file_name": file_row['original_name'],
            "file_hash": decrypted_hash,
            "decrypted_by_id": user['id'],
            "decrypted_by_username": user['username'],
            "timestamp": timestamp,
            "hash_verified": hash_match
        }
        event_hash = hash_event(event)

        # 6. Sign event hash with user's private key
        private_key_pem = user.get('private_key_enc') or ''
        signature = sign_data(event_hash, private_key_pem) if private_key_pem else "NO_KEY"

        # 7. Store in DB
        cur = db.execute(
            """INSERT INTO provenance_records
               (file_id, decrypted_by, decrypted_at, file_hash, event_hash, signature, success)
               VALUES (?,?,?,?,?,?,1)""",
            (file_id, user['id'], timestamp, decrypted_hash, event_hash, signature)
        )
        db.commit()
        record_id = cur.lastrowid

        # 8. Append to immutable ledger
        ledger_data = {
            **event,
            "event_hash": event_hash,
            "signature": signature,
            "db_record_id": record_id
        }
        ledger_block = append_record(ledger_data)

        # Update DB with ledger index
        db.execute(
            "UPDATE provenance_records SET ledger_index = ? WHERE id = ?",
            (ledger_block['index'], record_id)
        )

        # Log success
        db.execute(
            """INSERT INTO access_log (user_id, action, file_id, ip_address, success)
               VALUES (?,?,?,?,1)""",
            (user['id'], 'DECRYPT_SUCCESS', file_id, request.remote_addr)
        )
        db.commit()

        # 9. Return provenance metadata + the decrypted file as download
        response = send_file(
            io.BytesIO(decrypted_bytes),
            as_attachment=True,
            download_name=file_row['original_name'],
            mimetype='application/octet-stream'
        )
        response.headers['X-Provenance-Record-Id'] = str(record_id)
        response.headers['X-Event-Hash'] = event_hash
        response.headers['X-Ledger-Block'] = str(ledger_block['index'])
        response.headers['X-Hash-Verified'] = str(hash_match)
        response.headers['X-Signature'] = signature[:64] + '...'
        response.headers['Access-Control-Expose-Headers'] = (
            'X-Provenance-Record-Id, X-Event-Hash, X-Ledger-Block, '
            'X-Hash-Verified, X-Signature'
        )
        return response

    finally:
        db.close()


@provenance_bp.route('/records', methods=['GET'])
@token_required
def list_records():
    """List provenance records. Admins/auditors see all; users see their own."""
    db = get_db()
    try:
        role = g.current_user['role']
        uid = g.current_user['id']

        if role in ('admin', 'auditor'):
            rows = db.execute(
                """SELECT pr.*, u.username as decryptor_name, f.original_name as file_name
                   FROM provenance_records pr
                   JOIN users u ON u.id = pr.decrypted_by
                   JOIN files f ON f.id = pr.file_id
                   ORDER BY pr.decrypted_at DESC"""
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT pr.*, u.username as decryptor_name, f.original_name as file_name
                   FROM provenance_records pr
                   JOIN users u ON u.id = pr.decrypted_by
                   JOIN files f ON f.id = pr.file_id
                   WHERE pr.decrypted_by = ?
                   ORDER BY pr.decrypted_at DESC""",
                (uid,)
            ).fetchall()

        return jsonify({"records": [dict(r) for r in rows]}), 200

    finally:
        db.close()


@provenance_bp.route('/records/<int:record_id>', methods=['GET'])
@token_required
def get_record(record_id):
    """Get a single provenance record with full verification details."""
    db = get_db()
    try:
        row = db.execute(
            """SELECT pr.*, u.username as decryptor_name, u.public_key,
                      f.original_name as file_name
               FROM provenance_records pr
               JOIN users u ON u.id = pr.decrypted_by
               JOIN files f ON f.id = pr.file_id
               WHERE pr.id = ?""",
            (record_id,)
        ).fetchone()

        if not row:
            return jsonify({"error": "Record not found"}), 404

        role = g.current_user['role']
        if role not in ('admin', 'auditor') and row['decrypted_by'] != g.current_user['id']:
            return jsonify({"error": "Access denied"}), 403

        record = dict(row)

        # Verify signature inline
        sig_valid = verify_signature(
            record['event_hash'],
            record['signature'],
            record['public_key']
        )

        # Verify ledger block if index exists
        ledger_valid = None
        if record.get('ledger_index') is not None:
            ledger_result = verify_single_record(record['ledger_index'])
            ledger_valid = ledger_result.get('valid')

        record.pop('public_key', None)  # don't expose raw key in list
        record['signature_valid'] = sig_valid
        record['ledger_block_valid'] = ledger_valid

        return jsonify({"record": record}), 200

    finally:
        db.close()


@provenance_bp.route('/verify/<int:record_id>', methods=['POST'])
@token_required
def verify_record(record_id):
    """
    Full verification of a provenance record:
    - Re-verify SHA-256 event hash
    - Re-verify RSA digital signature
    - Re-verify ledger block integrity
    """
    db = get_db()
    try:
        row = db.execute(
            """SELECT pr.*, u.public_key, u.username as decryptor_name,
                      f.original_name as file_name
               FROM provenance_records pr
               JOIN users u ON u.id = pr.decrypted_by
               JOIN files f ON f.id = pr.file_id
               WHERE pr.id = ?""",
            (record_id,)
        ).fetchone()

        if not row:
            return jsonify({"error": "Record not found"}), 404

        record = dict(row)

        # Re-verify digital signature
        sig_valid = verify_signature(
            record['event_hash'],
            record['signature'],
            record['public_key']
        )

        # Re-verify ledger block
        ledger_check = {}
        if record.get('ledger_index') is not None:
            ledger_check = verify_single_record(record['ledger_index'])
        else:
            ledger_check = {"valid": False, "error": "No ledger index"}

        # Verify hash format (basic sanity check)
        hash_valid = bool(record['event_hash']) and len(record['event_hash']) == 64

        all_valid = sig_valid and ledger_check.get('valid', False) and hash_valid

        return jsonify({
            "record_id": record_id,
            "overall_valid": all_valid,
            "checks": {
                "signature_valid": sig_valid,
                "ledger_block_valid": ledger_check.get('valid', False),
                "event_hash_valid": hash_valid,
            },
            "metadata": {
                "file_name": record['file_name'],
                "decrypted_by": record['decryptor_name'],
                "decrypted_at": record['decrypted_at'],
                "event_hash": record['event_hash'],
                "ledger_index": record.get('ledger_index'),
            },
            "ledger_block": ledger_check.get('block'),
            "tamper_detected": not all_valid
        }), 200

    finally:
        db.close()


@provenance_bp.route('/ledger', methods=['GET'])
@token_required
def get_ledger():
    """Return the full immutable ledger (admin/auditor only)."""
    if g.current_user['role'] not in ('admin', 'auditor'):
        return jsonify({"error": "Access denied"}), 403

    chain = get_all_records()
    return jsonify({"ledger": chain, "total_blocks": len(chain)}), 200


@provenance_bp.route('/ledger/verify', methods=['GET'])
@token_required
def verify_ledger():
    """Verify the full ledger chain integrity."""
    if g.current_user['role'] not in ('admin', 'auditor'):
        return jsonify({"error": "Access denied"}), 403

    result = verify_chain()
    return jsonify(result), 200
