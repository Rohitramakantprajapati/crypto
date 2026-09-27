# 🔐 DecryptTrace – Secure Decryption Provenance System

> **Smart India Hackathon 2025 — Problem Statement 237**  
> **Theme:** Cryptographic Attribution and Immutable Decryption Provenance

[![Deploy Frontend](https://img.shields.io/badge/Frontend-GitHub%20Pages-blue?logo=github)](https://rohitramakantprajapati.github.io/crypto)
[![Backend](https://img.shields.io/badge/Backend-Render.com-46E3B7?logo=render)](https://decrypttrace-api.onrender.com/api/health)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend (GitHub Pages)** | https://rohitramakantprajapati.github.io/crypto |
| **Backend API (Render)** | https://decrypttrace-api.onrender.com/api/health |

**Demo Credentials:**
- Admin: `admin` / `admin123`
- User: `user` / `user123`

---

## 📖 Overview

DecryptTrace creates a **tamper-evident, cryptographically verifiable record** of every decryption event performed on sensitive data. It answers three critical questions:

1. **Who** decrypted it — Attribution via RSA digital signatures
2. **When** it was decrypted — Immutable UTC timestamp in blockchain ledger
3. **Whether** the record was altered — Tamper detection via SHA-256 hash chain

---

## ⚙️ How It Works

```
User Authentication (JWT)
        ↓
Upload File → AES-256-CBC Encryption
        ↓
Authorization Check (RBAC)
        ↓
Decrypt → SHA-256 Hash of content
        ↓
RSA-2048 Digital Signature (PSS-SHA256)
        ↓
Store Provenance Record (SQLite)
        ↓
Append to Immutable Blockchain Ledger
        ↓
Cryptographic Verification available anytime
```

---

## 🧩 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5 + Vanilla CSS + JavaScript (SPA) |
| **Backend** | Python 3 + Flask 3.0 |
| **Encryption** | AES-256-CBC (`cryptography` lib) |
| **Hashing** | SHA-256 (built-in `hashlib`) |
| **Auth** | JWT (PyJWT) + RSA-2048 Digital Signatures |
| **Immutable Ledger** | Local Blockchain (append-only JSON chain) |
| **Database** | SQLite |
| **Deployment** | GitHub Pages (frontend) + Render.com (backend) |

---

## 🗂️ Project Structure

```
crypto/
├── backend/
│   ├── app.py               ← Flask entry point (gunicorn-ready)
│   ├── .env.example         ← Environment variable template
│   ├── requirements.txt     ← Python dependencies
│   ├── Procfile             ← Render/Heroku deployment
│   ├── database/db.py       ← SQLite schema & init
│   ├── routes/
│   │   ├── auth.py          ← JWT auth + RSA keypair generation
│   │   ├── files.py         ← AES-256 file encryption/upload
│   │   ├── provenance.py    ← Core: decrypt + sign + ledger
│   │   └── admin.py         ← Admin panel endpoints
│   └── utils/
│       ├── crypto.py        ← AES-256, SHA-256, RSA-PSS
│       └── ledger.py        ← Immutable blockchain ledger
├── frontend/
│   ├── index.html           ← Single Page Application
│   ├── style.css            ← Dark glassmorphism design
│   └── app.js               ← Full SPA logic
├── .github/workflows/
│   └── deploy.yml           ← GitHub Actions → GitHub Pages
├── render.yaml              ← Render.com auto-deploy config
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.12+
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Rohitramakantprajapati/crypto.git
cd crypto
```

### 2. Set up backend
```bash
cd backend
cp .env.example .env          # copy env template
pip install -r requirements.txt
python app.py
```
Backend runs at: **http://127.0.0.1:5000**

### 3. Open frontend
Open `frontend/index.html` in any browser.

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | ❌ | Register user (RSA keypair auto-generated) |
| `POST` | `/api/auth/login` | ❌ | Login → JWT token |
| `GET` | `/api/auth/me` | ✅ | Current user info |
| `POST` | `/api/files/upload` | ✅ | Upload + AES-256 encrypt |
| `GET` | `/api/files/` | ✅ | List files |
| `POST` | `/api/provenance/decrypt/<id>` | ✅ | **Core: Decrypt + Sign + Ledger** |
| `GET` | `/api/provenance/records` | ✅ | Audit trail |
| `POST` | `/api/provenance/verify/<id>` | ✅ | Cryptographic verification |
| `GET` | `/api/provenance/ledger` | ✅ Admin | Full blockchain ledger |
| `GET` | `/api/provenance/ledger/verify` | ✅ Admin | Verify chain integrity |
| `GET` | `/api/admin/stats` | ✅ Admin | System statistics |
| `GET` | `/api/admin/logs` | ✅ Admin | Access audit logs |

---

## 🛡️ Security Features

- ✅ AES-256-CBC encryption at rest
- ✅ SHA-256 file content hashing
- ✅ RSA-2048 digital signatures (PSS-SHA256)
- ✅ JWT Bearer token authentication (8h expiry)
- ✅ Role-based access control (Admin / Auditor / User)
- ✅ Append-only immutable ledger (blockchain-style)
- ✅ Live hash recomputation during verification
- ✅ Tamper detection with visual alerts
- ✅ Full access logging (all events, including failed attempts)

---

## 👥 Team

| Field | Detail |
|-------|--------|
| **Problem Statement** | PS 237 – Cryptographic Attribution & Immutable Decryption Provenance |
| **Hackathon** | Smart India Hackathon 2025 |
| **Category** | Software |
| **Theme** | Blockchain & Cybersecurity |

---

## 📚 References

- [NIST FIPS 197 – AES](https://csrc.nist.gov/publications/detail/fips/197/final)
- [NIST FIPS 180-4 – SHA-256](https://csrc.nist.gov/publications/detail/fips/180/4/final)
- [NIST FIPS 186-5 – DSS (RSA-PSS)](https://csrc.nist.gov/publications/detail/fips/186/5/final)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Python cryptography library](https://cryptography.io/)
