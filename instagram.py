"""Publicação no Instagram @papa.garimpou pela API oficial da Meta (Graph API).

Trava: antes de publicar, confere que a conta do token é exatamente @papa.garimpou.
As imagens precisam de endereço público: o robô grava em midia/ do próprio
repositório (público), faz push e usa o link raw.githubusercontent.com.
"""
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests

import config

G = "https://graph.facebook.com/v21.0"
PASTA = Path(__file__).parent
MIDIA = PASTA / "midia"
# GITHUB_REPOSITORY vem do próprio GitHub Actions ("dono/repo"); nada de nome fixo no código.
REPO_RAW = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', '')}/main/midia/"


class ContaErrada(Exception):
    pass


def _token() -> str:
    t = os.environ.get("META_TOKEN", "")
    if not t:
        raise RuntimeError("META_TOKEN não configurado")
    return t


def conta() -> dict:
    """Descobre o Instagram ligado à Página e trava se não for o permitido."""
    r = requests.get(f"{G}/me/accounts", params={"access_token": _token(),
                     "fields": "id,name,access_token,instagram_business_account{id,username}"}, timeout=30).json()
    for p in r.get("data", []):
        ig = p.get("instagram_business_account") or {}
        if ig.get("username") == config.INSTAGRAM_PERMITIDO:
            return {"ig_id": ig["id"], "page_id": p["id"], "page_token": p.get("access_token")}
    raise ContaErrada(f"Instagram @{config.INSTAGRAM_PERMITIDO} não encontrado no token: {r}")


def hospedar(nome: str, conteudo: bytes) -> str:
    """Grava a imagem em midia/, publica no repositório e devolve a URL pública."""
    MIDIA.mkdir(exist_ok=True)
    (MIDIA / nome).write_bytes(conteudo)
    if os.environ.get("GITHUB_ACTIONS"):
        subprocess.run(["git", "add", f"midia/{nome}"], cwd=PASTA, check=True)
        subprocess.run(["git", "commit", "-m", f"mídia {nome}"], cwd=PASTA, check=True)
        subprocess.run(["git", "pull", "--rebase", "-q"], cwd=PASTA, check=True)
        subprocess.run(["git", "push", "-q"], cwd=PASTA, check=True)
        time.sleep(5)
    return REPO_RAW + nome


def _criar(ig_id: str, **params) -> str:
    r = requests.post(f"{G}/{ig_id}/media", data={"access_token": _token(), **params}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"Instagram recusou o container: {r}")
    return r["id"]


def _esperar(container: str, limite=60):
    for _ in range(limite // 3):
        s = requests.get(f"{G}/{container}", params={"access_token": _token(), "fields": "status_code"}, timeout=30).json()
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram não processou a mídia: {s}")
        time.sleep(3)


def _publicar(ig_id: str, container: str) -> str:
    _esperar(container)
    r = requests.post(f"{G}/{ig_id}/media_publish", data={"access_token": _token(), "creation_id": container}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"Instagram não publicou: {r}")
    return r["id"]


def story(imagem: bytes, nome: str) -> str:
    c = conta()
    url = hospedar(nome, imagem)
    return _publicar(c["ig_id"], _criar(c["ig_id"], image_url=url, media_type="STORIES"))


def foto(imagem: bytes, nome: str, legenda: str) -> str:
    c = conta()
    url = hospedar(nome, imagem)
    return _publicar(c["ig_id"], _criar(c["ig_id"], image_url=url, caption=legenda))


def carrossel(imagens: list[bytes], prefixo: str, legenda: str) -> str:
    c = conta()
    filhos = []
    for i, img in enumerate(imagens):
        url = hospedar(f"{prefixo}-{i}.jpg", img)
        filhos.append(_criar(c["ig_id"], image_url=url, is_carousel_item="true"))
    for f in filhos:
        _esperar(f)
    return _publicar(c["ig_id"], _criar(c["ig_id"], media_type="CAROUSEL", children=",".join(filhos), caption=legenda))


def reels(video: bytes, legenda: str) -> str:
    """Publica um Reels (também vai para o feed). O vídeo sobe direto para a Meta
    (upload resumable), sem passar pelo repositório, para não inchar o git."""
    c = conta()
    cont = _criar(c["ig_id"], media_type="REELS", upload_type="resumable", caption=legenda, share_to_feed="true")
    r = requests.post(f"https://rupload.facebook.com/ig-api-upload/v21.0/{cont}", data=video, timeout=300,
                      headers={"Authorization": f"OAuth {_token()}", "offset": "0", "file_size": str(len(video))}).json()
    if not r.get("success"):
        raise RuntimeError(f"Instagram recusou o envio do vídeo: {r}")
    _esperar(cont, limite=300)
    return _publicar(c["ig_id"], cont)


def stories_ativos() -> int:
    """Quantos stories estão no ar agora (últimas 24 h)."""
    c = conta()
    r = requests.get(f"{G}/{c['ig_id']}/stories", params={"access_token": _token(), "fields": "id"}, timeout=30).json()
    return len(r.get("data", []))


def metricas() -> dict:
    """Seguidores, posts e alcance do dia (para o relatório)."""
    c = conta()
    perfil = requests.get(f"{G}/{c['ig_id']}", params={"access_token": _token(),
                          "fields": "followers_count,media_count"}, timeout=30).json()
    ins = requests.get(f"{G}/{c['ig_id']}/insights", params={"access_token": _token(), "metric": "reach,profile_views,website_clicks",
                       "period": "day", "metric_type": "total_value"}, timeout=30).json()
    alcance = {d["name"]: d.get("total_value", {}).get("value") for d in ins.get("data", [])}
    return {"seguidores": perfil.get("followers_count"), "posts": perfil.get("media_count"), **alcance}


PALAVRAS_CHAVE = ("quero", "link", "eu", "manda", "eu quero")
RESPOSTA_DM = ("Oi! Aqui é o Papa 😎💎\n\nAchou coisa boa de marca, em loja oficial, "
               "eu posto na hora, grátis no Telegram:\n\n🛒 Achadinhos: https://t.me/papagarimpou\n"
               "👕 Marcas e esporte: https://t.me/papagarimpoumarcas\n\nÉ só entrar e ativar as notificações!")


def responder_comentarios(ja_respondidos: set) -> list[str]:
    """Quem comenta QUERO/LINK/EU nos últimos posts recebe os links na DM (resposta privada)
    e uma resposta pública curta. Devolve os ids de comentário respondidos agora."""
    c = conta()
    feitos = []
    posts = requests.get(f"{G}/{c['ig_id']}/media", params={"access_token": _token(), "fields": "id", "limit": 6}, timeout=30).json()
    for p in posts.get("data", []):
        coms = requests.get(f"{G}/{p['id']}/comments", params={"access_token": _token(), "fields": "id,text,username"}, timeout=30).json()
        for cm in coms.get("data", []):
            if cm["id"] in ja_respondidos or cm.get("username") == config.INSTAGRAM_PERMITIDO:
                continue
            texto = (cm.get("text") or "").strip().lower()
            if not any(texto.startswith(k) or k in texto.split() for k in PALAVRAS_CHAVE):
                continue
            ok_dm = False
            if c.get("page_token"):
                r = requests.post(f"{G}/{c['page_id']}/messages", params={"access_token": c["page_token"]},
                                  json={"recipient": {"comment_id": cm["id"]}, "message": {"text": RESPOSTA_DM}}, timeout=30).json()
                ok_dm = "message_id" in r or "recipient_id" in r
            publica = "Te mandei no direct! 💎" if ok_dm else "Os links estão na bio, é grátis! 💎"
            requests.post(f"{G}/{cm['id']}/replies", data={"access_token": _token(), "message": publica}, timeout=30)
            feitos.append(cm["id"])
    return feitos


def limpar_midia(hoje: str, dias=2):
    """Apaga do repositório as imagens com data no nome (AAAAMMDD-...) de mais de `dias` dias.
    (Não dá para usar a data do arquivo: no GitHub tudo é baixado de novo a cada execução.)"""
    if not MIDIA.exists():
        return
    corte = (datetime.strptime(hoje, "%Y-%m-%d").toordinal() - dias)
    velhas = []
    for f in MIDIA.iterdir():
        try:
            if datetime.strptime(f.name[:8], "%Y%m%d").toordinal() < corte:
                velhas.append(f)
        except ValueError:
            continue
    if velhas and os.environ.get("GITHUB_ACTIONS"):
        subprocess.run(["git", "rm", "-q", *[f"midia/{f.name}" for f in velhas]], cwd=PASTA, check=False)
