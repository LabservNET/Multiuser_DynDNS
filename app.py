import requests
import json
import os
import sys
import time
import urllib3
import socket
import logging
import traceback

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config(path="config.json"):
    """Lädt die Konfigurationsdatei."""
    if not os.path.exists(path):
        print(f"Konfigurationsdatei '{path}' nicht gefunden.")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)

def get_current_ip(ip_source):
    """Ermittelt die aktuelle IP basierend auf der ip_source."""
    try:
        if ip_source["type"] == "url":
            r = requests.get(ip_source["url"], timeout=10, verify=False)
            r.raise_for_status()
            return r.text.strip()
        elif ip_source["type"] == "command":
            ip = os.popen(ip_source["command"]).read().strip()
            if not ip:
                raise Exception("IP konnte nicht per command ermittelt werden!")
            return ip
        elif ip_source["type"] == "resolve":
            return socket.gethostbyname(ip_source["hostname"])
        else:
            raise Exception("Unbekannter ip_source type")
    except Exception as e:
        raise Exception(f"Fehler beim Abrufen der IP: {e}")

def update_cloudflare(user_cfg, new_ip, messages):
    """Aktualisiert die DNS-Einträge bei Cloudflare."""
    cf = user_cfg["cloudflare"]
    headers = {
        "Authorization": f"Bearer {cf['api_token']}",
        "Content-Type": "application/json"
    }
    url = f"https://api.cloudflare.com/client/v4/zones/{cf['zone_id']}/dns_records?type=A"
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        r.raise_for_status()
        records = r.json()["result"]
        changes = []
        selected_domains = user_cfg.get("domains", [])  # Liste der zu aktualisierenden Domains
        for rec in records:
            if rec["name"] in selected_domains:  # Nur ausgewählte Domains prüfen
                if rec["content"] != new_ip:
                    logging.info(format_message(messages.get("ip_mismatch", "[{user}] IP-Abweichung erkannt: {name} hat {old_ip}, erwartet {new_ip}"),
                                                 user=user_cfg['name'], name=rec['name'], old_ip=rec['content'], new_ip=new_ip))
                    update_url = f"https://api.cloudflare.com/client/v4/zones/{cf['zone_id']}/dns_records/{rec['id']}"
                    data = {
                        "type": "A",
                        "name": rec["name"],
                        "content": new_ip,
                        "ttl": rec["ttl"],
                        "proxied": rec["proxied"]
                    }
                    resp = requests.put(update_url, headers=headers, json=data, timeout=10, verify=False)
                    resp.raise_for_status()
                    changes.append({
                        "name": rec["name"],
                        "old_ip": rec["content"],
                        "new_ip": new_ip
                    })
                    logging.info(format_message(messages.get("ip_updated", "[{user}] IP für {name} wurde auf {new_ip} aktualisiert."),
                                                 user=user_cfg['name'], name=rec['name'], new_ip=new_ip))
                else:
                    logging.info(format_message(messages.get("ip_correct", "[{user}] IP für {name} ist bereits korrekt: {new_ip}"),
                                                 user=user_cfg['name'], name=rec['name'], new_ip=new_ip))
        return changes
    except requests.exceptions.HTTPError as http_err:
        logging.error(format_message(messages.get("error", "[{user}] HTTP-Fehler: {error}"),
                                     user=user_cfg['name'], error=http_err))
        logging.error(f"URL: {url}")
        raise Exception(f"Fehler bei der Aktualisierung von Cloudflare: {http_err}")
    except Exception as e:
        logging.error(format_message(messages.get("error", "[{user}] Allgemeiner Fehler: {error}"),
                                     user=user_cfg['name'], error=e))
        logging.error(traceback.format_exc())
        raise Exception(f"Fehler bei der Aktualisierung von Cloudflare: {e}")

def format_message(template, **kwargs):
    """Ersetzt Platzhalter in Nachrichten durch die entsprechenden Werte."""
    return template.format(**kwargs)

def main():
    """Hauptfunktion des Programms."""
    cfg = load_config()
    messages = cfg.get("messages", {})
    update_interval = cfg.get("update_interval", 300)  # Standard: 300 Sekunden
    last_ips = {}  # Speichert die letzte IP für jeden Benutzer

    while True:
        try:
            for user_cfg in cfg.get("users", []):  # Multi-User-Support
                user_name = user_cfg.get("name", "Unbekannt")
                enable_api = user_cfg.get("enable_api", True)
                ip_source = user_cfg.get("ip_source", cfg.get("ip_source", {}))  # Benutzerdefinierte oder globale ip_source
                try:
                    new_ip = get_current_ip(ip_source)
                    logging.info(format_message(messages.get("current_ip", "[{user}] Die aktuelle IP lautet: {new_ip}"), user=user_name, new_ip=new_ip))
                    last_ip = last_ips.get(user_name)
                    if new_ip != last_ip:
                        if last_ip is not None:
                            logging.info(format_message(messages.get("ip_change", "[{user}] IP-Wechsel erkannt: {last_ip} -> {new_ip}"), user=user_name, last_ip=last_ip, new_ip=new_ip))
                        if enable_api and user_cfg.get("cloudflare", {}).get("api_token"):
                            update_cloudflare(user_cfg, new_ip, messages)
                        else:
                            logging.info(format_message(messages.get("api_disabled", "[{user}] API ist deaktiviert. Keine Änderungen vorgenommen."), user=user_name))
                        last_ips[user_name] = new_ip
                    else:
                        logging.info(format_message(messages.get("ip_unchanged", "[{user}] IP hat sich nicht geändert. Keine Aktion notwendig."), user=user_name))
                except Exception as e:
                    logging.error(format_message(messages.get("error", "[{user}] Ein Fehler ist aufgetreten: {error}"), user=user_name, error=e))
                    logging.error(traceback.format_exc())
        except Exception as e:
            logging.error(format_message(messages.get("error", "Globaler Fehler: {error}"), error=e))
            logging.error(traceback.format_exc())
        time.sleep(update_interval)  # Wartezeit aus der config.json

if __name__ == "__main__":
    main()
