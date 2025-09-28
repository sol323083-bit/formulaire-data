try:
    details_cmd = ['netsh', 'wlan', 'show', 'profile', 'name="'+profile_name+'"', 'key=clear']
    details = subprocess.check_output(details_cmd, text=True)
    print("Détails bruts :", details)
    for detail in details.split('\n'):  # Ligne 25
        print("Ligne analysée :", detail)
        if "Key Content" in detail:
            key_value = detail.split(':')[1].strip()
            print(f"Clé trouvée pour {profile_name} : {key_value}")
            wifi_data[profile_name] = key_value
except subprocess.CalledProcessError as e:
    print(f"Erreur subprocess pour {profile_name} : {e}")
except Exception as e:
    print(f"Erreur inattendue pour {profile_name} : {e}")
