"""
DecryptTrace – Crypto utilities
AES-256 encryption/decryption, SHA-256 hashing, RSA digital signatures.
"""

import os
import hashlib
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization, padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# AES-256-CBC Encryption / Decryption
# ─────────────────────────────────────────────

def _get_aes_key() -> bytes:
    """Return a 32-byte AES key from environment."""
    raw = os.getenv("AES_KEY", "decrypttrace_aes_key_must_be_32b!")
    key = raw.encode("utf-8")
    # Ensure exactly 32 bytes (pad or truncate)
    return (key + b'\x00' * 32)[:32]


def encrypt_file(file_bytes: bytes) -> dict:
    """
    Encrypt raw file bytes using AES-256-CBC.
    Returns: { 'ciphertext': <hex>, 'iv': <hex> }
    """
    key = _get_aes_key()
    iv = os.urandom(16)

    padder = PKCS7(128).padder()
    padded_data = padder.update(file_bytes) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return {
        "ciphertext": ciphertext.hex(),
        "iv": iv.hex()
    }


def decrypt_file(ciphertext_hex: str, iv_hex: str) -> bytes:
    """
    Decrypt AES-256-CBC ciphertext back to raw bytes.
    """
    key = _get_aes_key()
    iv = bytes.fromhex(iv_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data


# ─────────────────────────────────────────────
# SHA-256 Hashing
# ─────────────────────────────────────────────

def hash_bytes(data: bytes) -> str:
    """Return hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_string(text: str) -> str:
    """Return hex SHA-256 digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_event(event_dict: dict) -> str:
    """
    Create a deterministic SHA-256 hash of a provenance event dict.
    Keys are sorted to ensure consistency.
    """
    canonical = json.dumps(event_dict, sort_keys=True, ensure_ascii=True)
    return hash_string(canonical)


# ─────────────────────────────────────────────
# RSA Key Generation
# ─────────────────────────────────────────────

def generate_rsa_keypair() -> tuple[str, str]:
    """
    Generate a 2048-bit RSA key pair.
    Returns (public_key_pem, private_key_pem) as strings.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    return public_pem, private_pem


# ─────────────────────────────────────────────
# Digital Signatures (RSA-PSS with SHA-256)
# ─────────────────────────────────────────────

def sign_data(data: str, private_key_pem: str) -> str:
    """
    Sign a string with RSA-PSS (SHA-256).
    Returns base64-encoded signature.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
        backend=default_backend()
    )
    signature = private_key.sign(
        data.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("utf-8")


def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify an RSA-PSS signature.
    Returns True if valid, False otherwise.
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8"),
            backend=default_backend()
        )
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            data.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
