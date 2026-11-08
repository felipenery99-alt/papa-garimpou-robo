"""Publicação no Instagram @papa.garimpou pela API oficial da Meta (Graph API).

Trava: antes de publicar, confere que a conta do token é exatamente @papa.garimpou.
As imagens precisam de endereço público: o robô grava em midia/ do próprio
repositório (público), faz push e usa o link raw.githubusercontent.com.
"""
import json
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


def validade_token() -> dict:
    """05/11 (1 ano sem o dono): tipo e vencimento do META_TOKEN (debug_token). expires_at 0 = não vence.
    data_access_expires_at = até quando a Meta deixa ler dados sem o dono entrar de novo (90 dias de uso)."""
    t = _token()
    d = requests.get(f"{G}/debug_token", params={"input_token": t, "access_token": t}, timeout=30).json().get("data", {})
    if not d:
        raise RuntimeError("debug_token sem dados")
    return {"tipo": d.get("type"), "valido": d.get("is_valid"), "vence": d.get("expires_at") or 0,
            "acesso_vence": d.get("data_access_expires_at") or 0, "escopos": d.get("scopes", [])}


# 05/11 (1 ano sem o dono): cada imagem no main ficava para sempre no histórico do git (~7 MB/dia → ~2,5 GB/ano).
# Agora as imagens do Instagram vão para um ramo à parte, recriado vazio todo dia: a Meta só precisa do link
# por alguns minutos, e o que fica de fora do main o GitHub limpa sozinho. Só o story-link (que a rodada usa
# como arquivo local) continua no main.
RAMO_MIDIA = "midia-temp"
_RAMO_PRONTO = [""]


def _gh(metodo: str, caminho: str, **kw) -> dict:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    r = requests.request(metodo, f"https://api.github.com/repos/{repo}{caminho}", timeout=60,
                         headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                  "Accept": "application/vnd.github+json"}, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub {metodo} {caminho}: {r.status_code} {r.text[:200]}")
    return r.json() if r.text else {}


def _ramo_do_dia() -> None:
    """Garante o ramo de mídia de hoje: se a ponta não for de hoje, recria o ramo com um commit sem passado."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    if _RAMO_PRONTO[0] == hoje:
        return
    try:
        ponta = _gh("GET", f"/git/ref/heads/{RAMO_MIDIA}")["object"]["sha"]
        if _gh("GET", f"/git/commits/{ponta}")["message"].startswith(f"midia {hoje}"):
            _RAMO_PRONTO[0] = hoje
            return
        existe = True
    except RuntimeError:
        existe = False
    blob = _gh("POST", "/git/blobs", json={"content": "Imagens temporárias do Instagram (recriado todo dia).\n",
                                            "encoding": "utf-8"})["sha"]
    arvore = _gh("POST", "/git/trees", json={"tree": [{"path": "LEIA.txt", "mode": "100644", "type": "blob",
                                                       "sha": blob}]})["sha"]
    commit = _gh("POST", "/git/commits", json={"message": f"midia {hoje}", "tree": arvore, "parents": []})["sha"]
    if existe:
        _gh("PATCH", f"/git/refs/heads/{RAMO_MIDIA}", json={"sha": commit, "force": True})
    else:
        _gh("POST", "/git/refs", json={"ref": f"refs/heads/{RAMO_MIDIA}", "sha": commit})
    _RAMO_PRONTO[0] = hoje


def _esperar_raw(url: str, nome: str) -> None:
    # 02/11: story das 08:52 falhou com 2207052 ("Only photo or video"): a Meta buscou o link raw antes de
    # ele servir a imagem. Só devolve a URL quando ela responde 200 com content-type de imagem.
    for _ in range(12):
        try:
            r = requests.head(url, timeout=15, allow_redirects=True)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise RuntimeError(f"mídia {nome} não ficou disponível no GitHub em 60 s")


def hospedar(nome: str, conteudo: bytes, permanente: bool = False) -> str:
    """Publica a imagem e devolve a URL pública. `permanente` (story-link): grava em midia/ do main."""
    import base64
    if os.environ.get("GITHUB_ACTIONS") and os.environ.get("GITHUB_TOKEN") and not permanente:
        try:
            _ramo_do_dia()
            _gh("PUT", f"/contents/{nome}", json={"message": f"mídia {nome}", "branch": RAMO_MIDIA,
                                                   "content": base64.b64encode(conteudo).decode()})
            url = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', '')}/{RAMO_MIDIA}/{nome}"
            _esperar_raw(url, nome)
            return url
        except Exception as e:   # se o ramo falhar, segue pelo jeito antigo (main) para não perder a peça
            print(f"[midia] ramo {RAMO_MIDIA} falhou ({e}); usando midia/ do main")
    MIDIA.mkdir(exist_ok=True)
    (MIDIA / nome).write_bytes(conteudo)
    if os.environ.get("GITHUB_ACTIONS"):
        subprocess.run(["git", "add", f"midia/{nome}"], cwd=PASTA, check=True)
        # mesma imagem já publicada antes (ex.: nova tentativa): nada a gravar, segue com o link que já existe
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PASTA).returncode != 0:
            subprocess.run(["git", "commit", "-m", f"mídia {nome}"], cwd=PASTA, check=True)
            # 05/11 19h15 (post_achado perdido): outra sessão gravou no main entre o pull e o push e o push foi
            # recusado. Agora tenta até 5 vezes (pull --rebase + push) antes de desistir.
            for tentativa in range(5):
                subprocess.run(["git", "pull", "--rebase", "--autostash", "-q"], cwd=PASTA, check=False)
                if subprocess.run(["git", "push", "-q"], cwd=PASTA).returncode == 0:
                    break
                time.sleep(3 * (tentativa + 1))
            else:
                raise RuntimeError(f"push da mídia {nome} recusado 5 vezes")
        _esperar_raw(REPO_RAW + nome, nome)
    return REPO_RAW + nome


def foto_fbcdn(url: str) -> str:
    """01/11 (sessão Instagram): a Business Suite bloqueia raw.githubusercontent por CSP, mas aceita fbcdn.
    Sobe a imagem como foto NÃO publicada da Página e devolve a maior versão (scontent…fbcdn.net)."""
    c = conta()
    tk = c["page_token"] or _token()
    r = requests.post(f"{G}/{c['page_id']}/photos", data={"access_token": tk, "url": url, "published": "false"},
                      timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"Página recusou a foto: {r}")
    imgs = requests.get(f"{G}/{r['id']}", params={"access_token": tk, "fields": "images"}, timeout=30).json()
    maior = max(imgs.get("images", []), key=lambda i: i.get("width", 0) * i.get("height", 0), default=None)
    if not maior:
        raise RuntimeError(f"foto sem 'images': {imgs}")
    return maior["source"]


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


_COTA = {"quando": 0.0, "livre": 999}


def _cota_livre(ig_id: str) -> int:
    """05/11 (1 ano sem o dono): limite da Meta para publicações pela API em 24 h (content_publishing_limit).
    Consulta no máximo a cada 10 min; se a consulta falhar, não trava a publicação."""
    if time.time() - _COTA["quando"] > 600:
        try:
            d = requests.get(f"{G}/{ig_id}/content_publishing_limit", timeout=30,
                             params={"access_token": _token(), "fields": "quota_usage,config"}).json()["data"][0]
            _COTA["livre"] = int(d.get("config", {}).get("quota_total", 100)) - int(d.get("quota_usage", 0))
        except Exception:
            _COTA["livre"] = 999
        _COTA["quando"] = time.time()
    return _COTA["livre"]


def _publicar(ig_id: str, container: str) -> str:
    if _cota_livre(ig_id) <= 5:   # folga: o resto fica para depois, sem erro da Meta
        raise RuntimeError("cota de publicações do Instagram em 24 h quase no fim; peça adiada")
    _esperar(container)
    for tentativa in range(6):
        r = requests.post(f"{G}/{ig_id}/media_publish", data={"access_token": _token(), "creation_id": container}, timeout=60).json()
        if "id" in r:
            _COTA["livre"] -= 1
            return r["id"]
        # 2207027 = "mídia não está pronta": a Meta ainda está processando; espera e tenta de novo
        if r.get("error", {}).get("error_subcode") != 2207027:
            break
        time.sleep(10)
    raise RuntimeError(f"Instagram não publicou: {r}")


def story(imagem: bytes, nome: str) -> str:
    c = conta()
    url = hospedar(nome, imagem)
    return _publicar(c["ig_id"], _criar(c["ig_id"], image_url=url, media_type="STORIES"))


def foto(imagem: bytes, nome: str, legenda: str) -> str:
    c = conta()
    url = hospedar(nome, imagem)
    return _publicar(c["ig_id"], _criar(c["ig_id"], image_url=url, caption=legenda))


def carrossel(imagens: list[bytes], prefixo: str, legenda: str, colaboradores: list[str] | None = None) -> str:
    """`colaboradores` (01/11, post Collab): usuários convidados como coautores, sem @;
    o post só aparece no perfil deles depois que aceitarem o convite no app."""
    c = conta()
    filhos = []
    for i, img in enumerate(imagens):
        url = hospedar(f"{prefixo}-{i}.jpg", img)
        filhos.append(_criar(c["ig_id"], image_url=url, is_carousel_item="true"))
    for f in filhos:
        _esperar(f)
    return _publicar(c["ig_id"], _criar(c["ig_id"], media_type="CAROUSEL", children=",".join(filhos), caption=legenda,
                                          **({"collaborators": json.dumps(colaboradores)} if colaboradores else {})))


def permalink(media_id: str) -> str:
    r = requests.get(f"{G}/{media_id}", params={"access_token": _token(), "fields": "permalink,shortcode"}, timeout=30).json()
    return r.get("permalink") or r.get("shortcode") or str(r)


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


PALAVRAS_CHAVE = ("quero", "link", "eu", "manda", "eu quero", "canais", "canal", "telegram")
# 02/11: 81 visitas no perfil e só 1 clique no link da bio. Quem comenta CANAIS recebe os 4 canais
# no direct, mesmo num post com DM própria (ex.: carrossel com links de produto).
PALAVRAS_CANAIS = ("canais", "canal", "telegram")
RESPOSTA_DM = ("Oi! Aqui é o Papa 😎💎\n\nAchou coisa boa de marca, em loja oficial, "
               "eu posto na hora, grátis no Telegram:\n\n🛒 Achadinhos: https://t.me/papagarimpou\n"
               "👕 Marcas e esporte: https://t.me/papagarimpoumarcas\n"
               "📱 Eletrônicos e games: https://t.me/papagarimpoutech\n"
               "💎 Quer tudo num lugar só? https://t.me/papagarimpouofertas\n\nÉ só entrar e ativar as notificações!"
               # 08/11 (CEO): anúncio deu 95 cliques e 0 membro; quem não tem o app vê os achados sem instalar
               "\n\nNão tem Telegram? Veja os achados no navegador: https://t.me/s/papagarimpouofertas")


def _resposta_dm() -> str:
    """05/11 (CEO): quem comenta TELEGRAM recebe o convite "ig-dm" (conta quantos entram por ele) no lugar
    do link público do canal geral. Sem o arquivo de convites, vai o texto de sempre."""
    try:
        link = json.loads((PASTA / "dados" / "convites.json").read_text(encoding="utf-8"))["ig-dm"]
    except Exception:
        return RESPOSTA_DM
    return RESPOSTA_DM.replace("https://t.me/papagarimpouofertas", link)


def _convite_extra() -> str:
    """06/11 (CEO): seguidores 151→291 em 1 dia e membros parados em 16. Quem pede os links de produto
    (QUERO no carrossel) é o lead mais quente: a DM de links passa a terminar com o convite do Telegram."""
    try:
        link = json.loads((PASTA / "dados" / "convites.json").read_text(encoding="utf-8"))["ig-dm"]
    except Exception:
        link = "https://t.me/papagarimpouofertas"
    return (f"\n\n💎 Quer achados assim todo dia, grátis? Entra no Telegram do Papa: {link}"
            "\nSem Telegram? Abre no navegador: https://t.me/s/papagarimpouofertas")


def responder_comentarios(ja_respondidos: set, dm_por_post: dict | None = None) -> list[str]:
    """Quem comenta QUERO/LINK/EU nos últimos posts recebe os links na DM (resposta privada)
    e uma resposta pública curta. Devolve os ids de comentário respondidos agora.
    `dm_por_post` (01/11): texto próprio por post, ex. os 5 links do carrossel salvável."""
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
            pede_canais = any(texto.startswith(k) or k in texto.split() for k in PALAVRAS_CANAIS)
            ok_dm = False
            if c.get("page_token"):
                r = requests.post(f"{G}/{c['page_id']}/messages", params={"access_token": c["page_token"]},
                                  json={"recipient": {"comment_id": cm["id"]}, "message": {"text": _resposta_dm() if pede_canais or p["id"] not in (dm_por_post or {}) else dm_por_post[p["id"]] + _convite_extra()}}, timeout=30).json()
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
