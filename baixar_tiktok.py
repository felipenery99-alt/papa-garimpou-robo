"""09/11 (CEO): baixa as cópias de TikTok dos Reels do dia para PAPA-GARIMPOU\\posts\\tiktok\\AAAAMMDD.
Roda no PC (PG · Instagram, antes de postar pelo Chrome M): python -I baixar_tiktok.py [AAAA-MM-DD]
O vídeo fica no ramo de mídia do dia no GitHub, que é recriado todo dia: baixar no mesmo dia."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import requests

PASTA = Path(__file__).resolve().parent
DESTINO = PASTA.parent / "posts" / "tiktok"


def main() -> int:
    dia = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    subprocess.run(["git", "pull", "--rebase", "-q"], cwd=PASTA, check=False)
    h = json.loads((PASTA / "dados" / "historico.json").read_text(encoding="utf-8"))
    itens = h.get("tiktok", {}).get(dia, [])
    if not itens:
        print(f"nenhum vídeo de TikTok em {dia}")
        return 0
    pasta = DESTINO / dia.replace("-", "")
    pasta.mkdir(parents=True, exist_ok=True)
    for i in itens:
        nome = i["hora"].replace(":", "")
        (pasta / f"{nome}.txt").write_text(i["legenda"], encoding="utf-8")
        mp4 = pasta / f"{nome}.mp4"
        if mp4.exists():
            print(f"{mp4.name}: já baixado")
            continue
        if not i.get("url"):
            print(f"{nome}: sem vídeo ({i.get('erro', '?')})")
            continue
        r = requests.get(i["url"], timeout=120)
        if r.status_code != 200:
            print(f"{nome}: não baixou ({r.status_code}); o ramo de mídia pode já ter sido recriado")
            continue
        mp4.write_bytes(r.content)
        print(f"{mp4} ({len(r.content) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
