"""Robô do Papa Garimpou — roda a cada 15 min (GitHub Actions).

Em cada execução: vê se algum horário sorteado do dia chegou; se sim, garimpa,
filtra (marca boa, loja oficial, nota, vendas, desconto), escolhe a melhor oferta
ainda não postada nos últimos 7 dias, aplica o selo do Papa e posta no canal.

Uso:
  python principal.py                 # execução normal (precisa dos segredos)
  python principal.py --ensaio        # usa ofertas de exemplo, não posta nada
  python principal.py --agenda        # mostra os horários de hoje
  python principal.py --testar-shopee # testa a API da Shopee sem postar
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import config
import horarios
import post
import qualidade

PASTA = Path(__file__).parent
HIST = PASTA / "dados" / "historico.json"
FUSO = ZoneInfo(config.FUSO)


def carregar_hist() -> dict:
    if HIST.exists():
        return json.loads(HIST.read_text(encoding="utf-8"))
    return {"slots_feitos": [], "postados": {}}


def salvar_hist(h: dict) -> None:
    limite = (datetime.now(FUSO) - timedelta(days=30)).date().isoformat()
    h["slots_feitos"] = [s for s in h["slots_feitos"] if s[:10] >= limite]
    h["postados"] = {k: v for k, v in h["postados"].items() if v[:10] >= limite}
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


def ja_postado_recente(h: dict, oferta_id: str, agora: datetime) -> bool:
    quando = h["postados"].get(oferta_id)
    if not quando:
        return False
    return datetime.fromisoformat(quando) > agora - timedelta(days=config.NAO_REPETIR_DIAS)


def garimpar(canal: str, fonte, h: dict, agora: datetime, rodada: int) -> dict | None:
    termos = config.BUSCAS[canal]
    inicio = rodada % len(termos)
    reprovados = {}
    for termo in termos[inicio:] + termos[:inicio]:
        try:
            ofertas = fonte(termo)
        except Exception as e:
            raise RuntimeError(f"busca '{termo}' falhou: {e}") from e
        boas = []
        for o in ofertas:
            ok, motivo = qualidade.avaliar(o, canal)
            if ok and not ja_postado_recente(h, o["id"], agora):
                boas.append(o)
            elif not ok:
                reprovados[motivo] = reprovados.get(motivo, 0) + 1
        if boas:
            return max(boas, key=qualidade.pontuar)
    print(f"[{canal}] nenhuma oferta boa. Reprovações: {reprovados}")
    return None


def ofertas_exemplo(termo: str) -> list[dict]:
    exemplo = json.loads((PASTA / "dados" / "exemplo_ofertas.json").read_text(encoding="utf-8"))
    return exemplo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensaio", action="store_true")
    ap.add_argument("--agenda", action="store_true")
    ap.add_argument("--testar-shopee", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    agora = datetime.now(FUSO)
    agenda = horarios.agenda_do_dia(agora.date())

    if args.agenda:
        for canal, hs in agenda.items():
            print(canal, " ".join(x.strftime("%H:%M") for x in hs))
        return 0

    if args.verificar:
        # Confere o bot sem postar nada: identidade, permissão nos 2 canais e chats privados que deram /start.
        import os
        import requests
        tk = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not tk:
            print("sem TELEGRAM_BOT_TOKEN")
            return 1
        api = f"https://api.telegram.org/bot{tk}"
        eu = requests.get(f"{api}/getMe", timeout=30).json()
        print("bot:", eu.get("ok"), eu.get("result", {}).get("username"))
        bot_id = eu.get("result", {}).get("id")
        for canal, destino in config.CANAIS.items():
            m = requests.get(f"{api}/getChatMember", params={"chat_id": destino, "user_id": bot_id}, timeout=30).json()
            r = m.get("result", {})
            print(f"{canal} {destino}: status={r.get('status')} pode_postar={r.get('can_post_messages')} {'' if m.get('ok') else m}")
        up = requests.get(f"{api}/getUpdates", timeout=30).json()
        privados = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
                    for u in up.get("result", []) if u.get("message", {}).get("chat", {}).get("type") == "private"}
        print("chats privados com o bot (para ALERTA_CHAT_ID):", privados or "nenhum — mande /start para o bot")
        return 0

    if args.testar_shopee:
        import shopee
        for o in shopee.buscar("cueca lupo", 5):
            print(qualidade.avaliar(o, "marcas"), o["nome"][:60], o["preco"], o["desconto"], o["loja_oficial"])
        return 0

    if args.ensaio:
        saida = PASTA / "dados" / "ensaio"
        saida.mkdir(parents=True, exist_ok=True)
        h = {"slots_feitos": [], "postados": {}}
        for canal in config.CANAIS:
            o = garimpar(canal, ofertas_exemplo, h, agora, 0)
            if not o:
                continue
            (saida / f"{canal}.txt").write_text(post.legenda(o, canal), encoding="utf-8")
            try:
                (saida / f"{canal}.jpg").write_bytes(post.foto_com_selo(o["imagem"]))
            except Exception as e:
                print(f"[{canal}] foto não baixou no ensaio: {e}")
            print(f"[{canal}] escolhida: {o['nome']} → {config.CANAIS[canal]} (ensaio, nada postado)")
        return 0

    import os
    import telegram
    import shopee
    if not (os.environ.get("SHOPEE_APP_ID") and os.environ.get("SHOPEE_SECRET") and os.environ.get("TELEGRAM_BOT_TOKEN")):
        print("chaves ainda não configuradas (Shopee/Telegram) — robô em espera, nada postado")
        return 0
    import random
    import time as _time
    h = carregar_hist()
    hoje = agora.date().isoformat()
    # Cada execução (20 por dia, horários no robo.yml) posta em 1 canal: o que tiver
    # menos posts hoje (empate = sorteio). Assim cada canal fica com 10 horários próprios.
    contagem = {c: sum(1 for s in h["slots_feitos"] if s.startswith(f"{hoje} {c}")) for c in config.CANAIS}
    abertos = [c for c, n in contagem.items() if n < config.POSTS_POR_CANAL_DIA]
    if not abertos:
        print("cota do dia já cumprida")
        return 0
    menor = min(contagem[c] for c in abertos)
    canal_da_vez = random.choice([c for c in abertos if contagem[c] == menor])
    pendentes = [(canal_da_vez, f"{hoje} {canal_da_vez} {agora:%H:%M}")]
    erros = 0
    for canal, chave in pendentes:
        try:
            oferta = garimpar(canal, shopee.buscar, h, agora, len(h["slots_feitos"]))
            if not oferta:
                telegram.avisar_felipe(f"sem oferta boa para {canal} em {chave}; pulei o horário.")
            else:
                telegram.postar_foto(config.CANAIS[canal], post.foto_com_selo(oferta["imagem"]),
                                     post.legenda(oferta, canal))
                h["postados"][oferta["id"]] = agora.isoformat()
                print(f"postado {chave}: {oferta['nome'][:60]}")
            h["slots_feitos"].append(chave)
        except telegram.DestinoProibido as e:
            telegram.avisar_felipe(f"BLOQUEADO destino errado: {e}")
            erros += 1
        except Exception as e:
            telegram.avisar_felipe(f"erro em {chave}: {e}. Não postei.")
            h["slots_feitos"].append(chave)
            erros += 1
    salvar_hist(h)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
