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


ERROS: list[str] = []   # vai para o relatório diário (lido pelo CEO na nuvem)


def membros(destino: str) -> int | None:
    if destino not in config.DESTINOS_PERMITIDOS or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return None
    try:
        r = requests.get(API.format(token=_token(), metodo="getChatMemberCount"), params={"chat_id": destino}, timeout=30).json()
        return r.get("result")
    except Exception:
        return None


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
