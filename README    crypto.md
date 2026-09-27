# 🔐 DecryptTrace – Secure Decryption Provenance System

**Smart India Hackathon 2025 — Problem Statement 237**
**Theme:** Cryptographic Attribution and Immutable Decryption Provenance
**Category:** Software

---

## 📖 Overview

DecryptTrace is a web-based system that creates a **tamper-evident, cryptographically verifiable record** of every decryption event performed on sensitive data. It answers three questions for any decrypted file:

1. **Who** decrypted it (attribution)
2. **When** it was decrypted (timestamp)
3. **Whether** the record or data was altered afterward (immutability)

This is achieved by combining **encryption, hashing, digital signatures, and an immutable ledger** into a single verifiable audit trail.

---

## ⚙️ How It Works (Flow)

```
User Authentication
        ↓
Encrypted File / Data
        ↓
Authorization Check
        ↓
Decryption
        ↓
Generate SHA-256 Hash
        ↓
Digital Signature
        ↓
Store Provenance Record
        ↓
Immutable Ledger
        ↓
Verification
```

---

## 🧩 Tech Stack

| Component        | Technology                              |
|-------------------|------------------------------------------|
| Frontend          | HTML, CSS, JavaScript / React            |
| Backend           | Python (Flask) / Node.js                 |
| Encryption        | AES                                       |
| Hashing           | SHA-256                                   |
| Authentication    | Login + Digital Signatures (Public-Key)  |
| Immutable Record  | Blockchain / Local Immutable Ledger       |
| Database          | MySQL / MongoDB                           |

---

## ✅ Setup Instructions (To-Do)

- [ ] Clone or download the project repository
- [ ] Install backend dependencies (`pip install -r requirements.txt` or `npm install`)
- [ ] Set up the database (MySQL/MongoDB) and update connection credentials in the config file
- [ ] Generate or configure public/private key pairs for digital signatures
- [ ] Set up the local blockchain / immutable ledger module (or connect to a test network, e.g., Ethereum testnet)
- [ ] Configure environment variables (DB credentials, secret keys, AES keys)
- [ ] Run the backend server
- [ ] Run the frontend application
- [ ] Test login with a sample authorized user account

---

## 🚀 Usage Instructions (To-Do)

- [ ] Log in as an authorized user
- [ ] Upload the file to be encrypted
- [ ] Confirm the file is encrypted (AES) and stored
- [ ] As an authorized user, trigger the **decrypt** action on the file
- [ ] Verify the system automatically:
  - [ ] Generates a SHA-256 hash of the file/event
  - [ ] Creates a digital signature tied to the user's identity
  - [ ] Records who decrypted it and the exact timestamp
  - [ ] Stores this record in the immutable ledger
- [ ] Use the **Verify** button/page to confirm a record's authenticity
- [ ] Attempt to tamper with a record (test case) and confirm the system detects the change

---

## 📜 Rules & Guidelines (To-Do)

- [ ] Only authorized users (role-based access) may decrypt files
- [ ] Every decryption attempt — successful or failed — must be logged
- [ ] Private keys used for digital signatures must never be stored in plain text
- [ ] AES encryption keys must be stored securely (e.g., in a key vault, not hardcoded)
- [ ] Once a provenance record is written to the ledger, it must never be edited or deleted
- [ ] All hashes must be recalculated and cross-checked during verification, not just stored blindly
- [ ] Access to the verification interface should be available to auditors/admins, even if they weren't the ones who decrypted the file
- [ ] Sensitive file content itself should not be stored in the ledger — only hashes/metadata (to preserve confidentiality)
- [ ] System must clearly flag when a file or record fails verification (tamper detected)
- [ ] Follow secure coding practices (input validation, no plaintext secrets, HTTPS in production)

---

## 🛡️ Feasibility Notes

- Prototype does **not** require a production-grade blockchain — a simplified local immutable ledger is sufficient for demonstration.
- Existing open-source cryptographic libraries can be used for AES, SHA-256, and digital signatures.
- Key management and access control are the most critical security aspects to get right.

---

## 🎯 Target Users

- Educational institutions
- Government departments
- Financial organizations
- Healthcare organizations
- Legal/document management systems
- Enterprises handling confidential information

---

## 📚 References

- NIST — Cryptographic Standards
- NIST — SHA-256 / Secure Hash Standards
- NIST — Digital Signature Standard
- OWASP — Cryptographic Storage Guidelines
- Ethereum / Blockchain documentation

---

## 👥 Team

- **Team Name:** [Your Team Name]
- **Team ID:** [Your Team ID]
- **Problem Statement:** PS 237 – Cryptographic Attribution and Immutable Decryption Provenance
