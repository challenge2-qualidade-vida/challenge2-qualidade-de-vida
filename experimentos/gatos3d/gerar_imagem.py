"""Tópico 25: gera a imagem de um gato no espaço gratuito do FLUX.1 schnell, sem conta.

Rodar:  python3 experimentos/gatos3d/gerar_imagem.py "<descrição>" <semente> <saída.webp>
A descrição e as sementes usadas estão em docs/desenvolvimento/25-gatos-3d.md.
Sem conta, a cota é pequena: se der erro, peça uma imagem por vez ou espere.
"""

import json, subprocess, sys
BASE = "https://black-forest-labs-flux-1-schnell.hf.space/gradio_api/call/infer"
prompt, seed, saida = sys.argv[1], int(sys.argv[2]), sys.argv[3]
corpo = json.dumps({"data": [prompt, seed, False, 896, 1024, 4]})
r = subprocess.run(["curl", "-sS", "-m", "60", "-H", "Content-Type: application/json", "-d", corpo, BASE], capture_output=True, text=True, check=True)
ev = json.loads(r.stdout)["event_id"]
s = subprocess.run(["curl", "-sSN", "-m", "240", f"{BASE}/{ev}"], capture_output=True, text=True).stdout
tipo, url = None, None
for l in s.splitlines():
    if l.startswith("event:"): tipo = l[6:].strip()
    elif l.startswith("data:") and tipo == "complete": url = json.loads(l[5:])[0]["url"]
    elif l.startswith("data:") and tipo == "error": sys.exit("ERRO " + l)
if not url: sys.exit("sem resposta: " + s[:300])
subprocess.run(["curl", "-sS", "-m", "60", "-o", saida, url], check=True)
print("ok", saida)
