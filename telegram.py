"""Envio para o Telegram via Bot API, com trava de destino."""
import os

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


def avisar_dono(texto: str) -> None:
    """Aviso de problema. Vai só para o chat do dono com o robô (ALERTA_CHAT_ID).
    Nunca para os canais. Se não houver chat configurado, só registra no log."""
    chat = os.environ.get("ALERTA_CHAT_ID", "").strip()
    print(f"[ALERTA] {texto}")
    ERROS.append(texto[:300])
    if not chat or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return
    try:
        requests.post(
            API.format(token=_token(), metodo="sendMessage"),
            data={"chat_id": chat, "text": f"⚠️ Robô Papa Garimpou: {texto}"},
            timeout=30,
        )
    except Exception as e:  # o aviso nunca pode derrubar o robô
        print(f"[ALERTA] falhou ao avisar: {e}")


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
