from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def exfil():
    data = request.json
    print("Données reçues :", data)  # Affiche dans le terminal pour debug
    with open('exfil_data.json', 'a') as f:  # Sauvegarde dans un fichier
        f.write(str(data) + '\n')
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)  # Écoute sur 192.168.2.154:8080
