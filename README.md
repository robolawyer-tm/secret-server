# Secret Server

### Simple. Transparent. Secure.

**Secret Server** is a phone‑friendly, local‑first web app that lets you safely store sensitive data such as passwords, notes, or anything else you want encrypted and under your control.  
Your browser encrypts the data *before* it leaves your device, and the server stores only encrypted JSON payloads.

It turns your phone into a personal vault — where your data stays on your hardware and moves only across your own Wi‑Fi.

---

## 🛡️ How It Works (The Simple Flow)

Secret Server is built from four small, clear components:

1. **Vivify** – The interface. It organizes your data.
2. **Secrecy** – The lock. It encrypts your data in the browser.
3. **Payload** – The box. It packages encrypted data for storage.
4. **Server** – The shelf. It stores the encrypted payloads.

Because encryption happens *before* anything is sent, the server (and anyone who might access it) sees only scrambled data.

---

## 🔑 Two Password Layers (Important)

Secret Server uses **two different passwords**, each serving a different purpose:

### 1. Login Password (UI Access)
- Unlocks the Vivify interface.
- Prevents casual access to the app on your phone.
- **Not** used for encryption.

### 2. Secret Password (Encryption Key)
- This password actually encrypts your data.
- Used to derive the encryption key inside the browser.
- Never sent to the server.

### Convenience Note
For ease of use, the login password is **pre-filled** into the “Secret Password” field.  
However, users may **replace it with a different password** if they want stronger separation between:

- UI access  
- Data encryption  

This gives users flexibility:  
**one password for convenience, or two passwords for stronger compartmentalization.**

---

## 🔒 Security & Safety Notes (Important)

Secret Server is intentionally **local‑first**. To keep it safe:

### ✔ Use it only on networks you trust
- Your home Wi‑Fi  
- Your phone’s personal hotspot  
- A private network you control  

### ✔ Avoid public Wi‑Fi
Even though data is encrypted, public networks add unnecessary risk.

### ✔ Never expose the server to the open internet
This app is designed for simplicity and local use.  
Do **not** port‑forward it or run it on a public IP.

### ✔ Keep your phone locked and updated
Your phone is the vault. Treat it like one.

### ✔ Remember: the server stores only encrypted payloads
Even if someone accessed the storage, they would see only scrambled JSON.

---

## 🔍 Please Audit

- **Encryption Logic:** See `lib/crypto.py`  
- **Storage Logic:** See `lib/storage.py`  
- **Web Server:** See `web_server.py`

Transparency is part of the design — read the code, verify the flow, and trust what you can see.

---

## 🚀 One‑Step Installation (Termux)

Copy and paste this into Termux:

```bash
curl -sSL https://raw.githubusercontent.com/JohnBlakesDad/secret-server/main/install.sh | bash
.

## 🧹 Uninstallation

To remove everything cleanly:
```bash
cd ~/payload-persist && ./uninstall.sh
```

---


