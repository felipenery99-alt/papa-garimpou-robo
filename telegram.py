"""Envio para o Telegram via Bot API, com trava de destino."""
import json
import os
import re
from pathlib import Path

import requests

import config

API = "https://api.telegram.org/bot{token}/{metodo}"


class DestinoProibido(Exception):
    pass


def _token() -> str:
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not t:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")
    return t


def postar_foto(destino: str, foto: bytes, legenda: str) -> dict:
    if destino not in config.DESTINOS_PERMITIDOS:
        raise DestinoProibido(f"destino recusado: {destino}")
    r = requests.post(
        API.format(token=_token(), metodo="sendPhoto"),
        data={"chat_id": destino, "caption": legenda[:1024]},
        files={"photo": ("oferta.jpg", foto, "image/jpeg")},
        timeout=60,
    )
    dados = r.json()
    if not dados.get("ok"):
        raise RuntimeError(f"Telegram recusou: {dados}")
    return dados["result"]


def postar_menu_fixado(destino: str, texto: str, botoes: list[tuple[str, str]]) -> dict:
    """Mensagem com botões (um por linha) que levam aos outros canais, fixada no topo sem notificar."""
    if destino not in config.DESTINOS_PERMITIDOS:
        raise DestinoProibido(f"destino recusado: {destino}")
    teclado = {"inline_keyboard": [[{"text": t, "url": u}] for t, u in botoes]}
    r = requests.post(API.format(token=_token(), metodo="sendMessage"),
                      json={"chat_id": destino, "text": texto, "reply_markup": teclado,
                            "disable_web_page_preview": True, "disable_notification": True}, timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError(f"Telegram recusou o menu: {r}")
    msg = r["result"]
    requests.post(API.format(token=_token(), metodo="pinChatMessage"),
                  json={"chat_id": destino, "message_id": msg["message_id"], "disable_notification": True}, timeout=30)
    return msg


def postar_texto_fixado(destino: str, texto: str) -> int:
    """Texto simples (sem oferta), fixado no topo sem notificar. Devolve o message_id."""
    if destino not in config.DESTINOS_PERMITIDOS:
        raise DestinoProibido(f"destino recusado: {destino}")
    r = requests.post(API.format(token=_token(), metodo="sendMessage"),
                      json={"chat_id": destino, "text": texto, "disable_web_page_preview": True}, timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError(f"Telegram recusou a mensagem: {r}")
    mid = r["result"]["message_id"]
    requests.post(API.format(token=_token(), metodo="pinChatMessage"),
                  json={"chat_id": destino, "message_id": mid, "disable_notification": True}, timeout=30)
    return mid


def desafixar(destino: str, message_id: int) -> None:
    """Tira só essa mensagem do topo; o menu fixado antes volta a aparecer em cima."""
    if destino not in config.DESTINOS_PERMITIDOS:
        raise DestinoProibido(f"destino recusado: {destino}")
    requests.post(API.format(token=_token(), metodo="unpinChatMessage"),
                  json={"chat_id": destino, "message_id": message_id}, timeout=30)


ERROS: list[str] = []   # vai para o relatório diário (lido pelo CEO na nuvem)


def membros(destino: str) -> int | None:
    if destino not in config.DESTINOS_PERMITIDOS or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return None
    try:
        r = requests.get(API.format(token=_token(), metodo="getChatMemberCount"), params={"chat_id": destino}, timeout=30).json()
        return r.get("result")
    except Exception:
        return None


def criar_convite(destino: str, nome: str) -> str:
    """Link de convite próprio (createChatInviteLink); exige o robô com "Convidar usuários" no canal."""
    if destino not in config.DESTINOS_PERMITIDOS:
        raise DestinoProibido(destino)
    r = requests.post(API.format(token=_token(), metodo="createChatInviteLink"),
                      data={"chat_id": destino, "name": nome}, timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError(r.get("description", r))
    return r["result"]["invite_link"]


def entradas_por_convite(offset: int | None) -> tuple[list[tuple[str, str, int]], int | None]:
    """Quem entrou em canal por link de convite desde `offset`: [(canal @, nome do link, user id)].
    Usa getUpdates com chat_member (o Telegram guarda 24 h); devolve o próximo offset."""
    params = {"timeout": 0, "allowed_updates": '["chat_member","message"]'}
    if offset:
        params["offset"] = offset
    r = requests.get(API.format(token=_token(), metodo="getUpdates"), params=params, timeout=30).json()
    saida, prox = [], offset
    for u in r.get("result", []):
        prox = u["update_id"] + 1
        cm = u.get("chat_member") or {}
        link = (cm.get("invite_link") or {}).get("name")
        if link and cm.get("new_chat_member", {}).get("status") == "member"                 and cm.get("old_chat_member", {}).get("status") in ("left", "kicked"):
            saida.append(("@" + cm.get("chat", {}).get("username", ""), link, cm["new_chat_member"]["user"]["id"]))
    return saida, prox


ALERTAS = Path(__file__).parent / "dados" / "alertas.json"


def _segurar(texto: str) -> bool:
    """05/11 (dono: 1 ano sem entrar no Claude): erro comum o robô tenta de novo sozinho na próxima
    execução; só vira aviso no celular se o MESMO erro (texto sem números) continuar por 24 h,
    e depois no máximo 1 vez a cada 24 h. Erro que some por 48 h é esquecido."""
    from datetime import datetime, timedelta
    agora = datetime.now()
    assin = re.sub(r"\d+", "#", texto)[:80]
    try:
        vistos = json.loads(ALERTAS.read_text(encoding="utf-8"))
    except Exception:
        vistos = {}
    vistos = {k: v for k, v in vistos.items() if agora - datetime.fromisoformat(v["ultimo"]) < timedelta(hours=48)}
    v = vistos.setdefault(assin, {"primeiro": agora.isoformat(), "ultimo": agora.isoformat(), "enviado": ""})
    v["ultimo"] = agora.isoformat()
    segura = agora - datetime.fromisoformat(v["primeiro"]) < timedelta(hours=24) or \
        (v["enviado"] and agora - datetime.fromisoformat(v["enviado"]) < timedelta(hours=24))
    if not segura:
        v["enviado"] = agora.isoformat()
    try:
        ALERTAS.parent.mkdir(exist_ok=True)
        ALERTAS.write_text(json.dumps(vistos, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return segura


def avisar_dono(texto: str, prefixo: bool = True, urgente: bool | None = None) -> None:
    """Aviso de problema. Vai só para o chat do dono com o robô (ALERTA_CHAT_ID).
    Nunca para os canais. Se não houver chat configurado, só registra no log.
    `prefixo=False` (03/11, vigia): o texto já vem pronto, sem "⚠️ Robô Papa Garimpou:".
    Urgente (vigia, destino/conta bloqueados, token vencendo) sai na hora; o resto espera 24 h (ver _segurar)."""
    chat = os.environ.get("ALERTA_CHAT_ID", "").strip()
    print(f"[ALERTA] {texto}")
    ERROS.append(texto[:300])
    if urgente is None:
        urgente = not prefixo or "BLOQUEADO" in texto or "TOKEN" in texto.upper()
    if not urgente and _segurar(texto):
        print("[ALERTA] erro comum: o robô tenta de novo; só aviso o dono se durar 24 h")
        return
    if not chat or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return
    try:
        requests.post(
            API.format(token=_token(), metodo="sendMessage"),
            data={"chat_id": chat, "text": f"⚠️ Robô Papa Garimpou: {texto}" if prefixo else texto},
            timeout=30,
        )
    except Exception as e:  # o aviso nunca pode derrubar o robô
        print(f"[ALERTA] falhou ao avisar: {e}")


def mensagem_dono(texto: str) -> bool:
    """04/11 (resumo diário): texto pronto para o chat do dono, sem prefixo e sem entrar na lista de erros.
    Quebra em partes de até 4000 caracteres (limite do Telegram). True só se todas as partes saíram."""
    chat = os.environ.get("ALERTA_CHAT_ID", "").strip()
    if not chat or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("[DONO] sem ALERTA_CHAT_ID/token; não enviei")
        return False
    partes = [texto[i:i + 4000] for i in range(0, len(texto), 4000)] or [""]
    try:
        for p in partes:
            r = requests.post(API.format(token=_token(), metodo="sendMessage"), data={"chat_id": chat, "text": p}, timeout=30).json()
            if not r.get("ok"):
                print(f"[DONO] Telegram recusou: {r}")
                return False
        return True
    except Exception as e:
        print(f"[DONO] falhou: {e}")
        return False


def avisar_venda(texto: str) -> None:
    """Notícia boa (venda): vai só para o chat do dono, sem o prefixo de problema."""
    chat = os.environ.get("ALERTA_CHAT_ID", "").strip()
    print(f"[VENDA] {texto}")
    if not chat or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return
    try:
        requests.post(API.format(token=_token(), metodo="sendMessage"), data={"chat_id": chat, "text": texto}, timeout=30)
    except Exception as e:
        print(f"[VENDA] falhou ao avisar: {e}")
