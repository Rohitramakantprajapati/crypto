"""
DecryptTrace – Immutable Local Ledger
A simple append-only blockchain-style ledger stored as JSON.
Each block contains: index, timestamp, data, previous_hash, and its own hash.
"""

import json
import os
import hashlib
import datetime

from dotenv import load_dotenv

load_dotenv()

LEDGER_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', 'ledger', 'immutable_ledger.json'
)


def _ensure_ledger_dir():
    os.makedirs(os.path.dirname(LEDGER_FILE), exist_ok=True)


def _load_chain() -> list:
    _ensure_ledger_dir()
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_chain(chain: list):
    _ensure_ledger_dir()
    with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
        json.dump(chain, f, indent=2, ensure_ascii=True)


def _hash_block(block: dict) -> str:
    """Compute SHA-256 hash of a block (excluding its own hash field)."""
    block_copy = {k: v for k, v in block.items() if k != 'hash'}
    raw = json.dumps(block_copy, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _genesis_block() -> dict:
    """Create the genesis (first) block."""
    block = {
        "index": 0,
        "timestamp": "2025-01-01T00:00:00Z",
        "data": {"type": "GENESIS", "message": "DecryptTrace Ledger Initialized"},
        "previous_hash": "0" * 64,
        "hash": ""
    }
    block["hash"] = _hash_block(block)
    return block


def append_record(record_data: dict) -> dict:
    """
    Append a new immutable provenance record to the ledger.
    Returns the newly created block.
    """
    chain = _load_chain()

    if not chain:
        chain.append(_genesis_block())

    previous_block = chain[-1]
    new_index = len(chain)

    block = {
        "index": new_index,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "data": record_data,
        "previous_hash": previous_block["hash"],
        "hash": ""
    }
    block["hash"] = _hash_block(block)

    chain.append(block)
    _save_chain(chain)
    return block


def verify_chain() -> dict:
    """
    Verify integrity of the entire ledger chain.
    Returns { 'valid': bool, 'tampered_at': int | None, 'total_blocks': int }
    """
    chain = _load_chain()

    if not chain:
        return {"valid": True, "tampered_at": None, "total_blocks": 0}

    # Verify genesis
    genesis = chain[0]
    if _hash_block(genesis) != genesis.get("hash"):
        return {"valid": False, "tampered_at": 0, "total_blocks": len(chain)}

    for i in range(1, len(chain)):
        block = chain[i]
        prev_block = chain[i - 1]

        # 1. Recompute block's own hash
        if _hash_block(block) != block.get("hash"):
            return {"valid": False, "tampered_at": i, "total_blocks": len(chain)}

        # 2. Ensure chain linkage
        if block.get("previous_hash") != prev_block.get("hash"):
            return {"valid": False, "tampered_at": i, "total_blocks": len(chain)}

    return {"valid": True, "tampered_at": None, "total_blocks": len(chain)}


def get_all_records() -> list:
    """Return all blocks in the ledger."""
    return _load_chain()


def get_record_by_index(index: int) -> dict | None:
    """Return a specific block by its index."""
    chain = _load_chain()
    if 0 <= index < len(chain):
        return chain[index]
    return None


def verify_single_record(index: int) -> dict:
    """
    Verify a single record's integrity.
    Returns { 'valid': bool, 'block': dict, 'recomputed_hash': str }
    """
    chain = _load_chain()
    if index < 0 or index >= len(chain):
        return {"valid": False, "error": "Block not found"}

    block = chain[index]
    recomputed = _hash_block(block)
    valid = recomputed == block.get("hash")

    if valid and index > 0:
        # Also check chain linkage
        prev_block = chain[index - 1]
        if block.get("previous_hash") != prev_block.get("hash"):
            valid = False

    return {
        "valid": valid,
        "block": block,
        "recomputed_hash": recomputed
    }
