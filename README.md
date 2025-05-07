# 🌐 Multi-User Dynamic DNS Updater for Cloudflare (Python)

This Python script allows you to dynamically update **A-records** for multiple users in Cloudflare using their current IP address. It supports various IP detection methods and includes built-in logging and error handling.

---

## ✅ Features

- Supports **multiple users**, each with their own Cloudflare settings
- Detects external IP using:
  - Public APIs (`type: "url"`)
  - DNS hostname resolution (`type: "resolve"`)
  - Custom shell commands (`type: "command"`)
- Automatically updates A-records in Cloudflare
- Detects and logs IP changes, mismatches, and update results
- Fully configurable output messages
- Secure use of API tokens
- Runs as a background daemon (interval-based loop)

---

## 📁 File Structure

```
project/
│
├── app.py                 # Main script
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
└── README.md              # This documentation
```

---

## 🛠️ Installation

```bash
git clone https://github.com/your-repo/cloudflare-ddns-updater.git
cd cloudflare-ddns-updater
pip install -r requirements.txt
python3 app.py
```

---

## 📦 requirements.txt

```
requests 
urllib3
```

---

## ⚙️ Configuration: config.json

This file controls everything: user data, messages, IP sources, intervals.

### Top-Level Keys

| Key              | Type     | Description                                  |
|------------------|----------|----------------------------------------------|
| update_interval  | Integer  | Seconds to wait between update checks        |
| messages         | Object   | Custom log messages using placeholders       |
| users            | Array    | User definitions with individual settings    |

---

### 👤 User Object Format

```json
{
  "name": "User1",
  "enable_api": true,
  "ip_source": {
    "type": "resolve",
    "hostname": "example.dyndns.net"
  },
  "cloudflare": {
    "api_token": "your-cloudflare-api-token",
    "zone_id": "your-cloudflare-zone-id"
  },
  "domains": [
    "sub.example.com"
  ]
}
```

---

### 🧠 IP Source Types

| Type       | Description                                      | Required Key         |
|------------|--------------------------------------------------|----------------------|
| `url`      | Use HTTP GET to get public IP                    | `url`                |
| `command`  | Run a shell command to get IP                    | `command`            |
| `resolve`  | Resolve a DNS hostname to get current IP         | `hostname`           |

---

### 🗨️ Messages Block Example

```json
"messages": {
  "current_ip": "[{user}] Current IP: {new_ip}",
  "ip_change": "[{user}] IP changed: {last_ip} -> {new_ip}",
  "ip_mismatch": "[{user}] DNS record {name} has {old_ip}, expected {new_ip}",
  "ip_updated": "[{user}] Updated {name} to {new_ip}",
  "ip_correct": "[{user}] IP for {name} is already correct: {new_ip}",
  "api_disabled": "[{user}] API disabled. No update performed.",
  "ip_unchanged": "[{user}] IP unchanged. No action taken.",
  "error": "[{user}] Error occurred: {error}"
}
```

---

## 🧪 Example Output

```
[2025-05-07 12:00:00] INFO: [User1] Current IP: 203.0.113.42
[2025-05-07 12:00:00] INFO: [User1] IP changed: 198.51.100.10 -> 203.0.113.42
[2025-05-07 12:00:01] INFO: [User1] DNS record sub.example.com has 198.51.100.10, expected 203.0.113.42
[2025-05-07 12:00:02] INFO: [User1] Updated sub.example.com to 203.0.113.42
```

---

## 🧑‍💻 Running the Script

```bash
python ddns_updater.py
```

The script runs in an infinite loop, checking and updating every X seconds based on your configuration.

---

## 🛡️ Security Tips

- Keep your `config.json` file secure.
- Make sure your Cloudflare API tokens are restricted to DNS edit permissions for security.

---

## 📚 License

MIT License — feel free to use, modify, and share.
