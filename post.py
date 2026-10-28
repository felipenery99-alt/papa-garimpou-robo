"""Monta a legenda do post no modelo do Papa e aplica o selo do Papa na foto."""
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageOps

PASTA = Path(__file__).parent
SELO = PASTA / "assets" / "selo-papa.png"


def _brl(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def legenda(oferta: dict, canal: str) -> str:
    linhas = ["😎💎 PAPA GARIMPOU", "", oferta["nome"].strip(), ""]
    if oferta.get("preco_antigo") and oferta["preco_antigo"] > oferta["preco"]:
        linhas.append(f"❌ De: {_brl(oferta['preco_antigo'])}")
    linhas.append(f"✅ Por: {_brl(oferta['preco'])} ({oferta['desconto']}% OFF)")
    if oferta.get("extra"):
        linhas.append(f"💡 {oferta['extra']}")
    if oferta.get("vendas"):
        v = oferta["vendas"]
        txt = f"+{v // 1000} mil" if v >= 1000 else f"+{v}"
        linhas.append(f"⭐ {oferta.get('nota', '')} · {txt} vendidos".replace(" ·  ", " "))
    linhas.append("")
    if oferta.get("loja"):   # ofertas manuais (Amazon etc.) trazem a linha da loja pronta
        linhas.append(f"🏪 {oferta['loja']}")
    elif canal == "marcas" or oferta.get("loja_oficial"):
        linhas.append(f"🏪 Loja oficial · {oferta.get('plataforma', 'Shopee')}")
    linhas.append(f"👉 {oferta['link']}")
    linhas += ["", "⏳ Preço pode mudar a qualquer momento", "#publi link de afiliado"]
    return "\n".join(linhas)


def _garantir_selo() -> None:
    """Se o selo não estiver no repositório, baixa a foto do canal Achadinhos pelo
    próprio bot e recorta só o mascote (mesmo recorte do selo local)."""
    if SELO.exists():
        return
    import os
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    api = f"https://api.telegram.org/bot{token}"
    foto = requests.get(f"{api}/getChat", params={"chat_id": "@papagarimpou"}, timeout=30).json()["result"]["photo"]
    caminho = requests.get(f"{api}/getFile", params={"file_id": foto["big_file_id"]}, timeout=30).json()["result"]["file_path"]
    img = Image.open(io.BytesIO(requests.get(f"https://api.telegram.org/file/bot{token}/{caminho}", timeout=30).content))
    w, h = img.size
    img = img.convert("RGBA").crop((int(w * 0.231), int(h * 0.153), int(w * 0.769), int(h * 0.690)))
    SELO.parent.mkdir(exist_ok=True)
    img.resize((400, 400), Image.LANCZOS).save(SELO)


def foto_com_selo(url_imagem: str) -> bytes:
    try:
        _garantir_selo()
    except Exception as e:
        print(f"selo indisponível: {e}")
    """Baixa a foto do produto, deixa quadrada (1080) e põe o selo do Papa no canto."""
    r = requests.get(url_imagem, timeout=30)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    img = ImageOps.pad(img, (1080, 1080), color=(255, 255, 255))
    if SELO.exists():
        selo = Image.open(SELO).convert("RGBA")
        lado = 230
        selo = selo.resize((lado, lado), Image.LANCZOS)
        mask = Image.new("L", (lado, lado), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, lado, lado), fill=255)
        selo.putalpha(Image.composite(selo.getchannel("A"), Image.new("L", (lado, lado), 0), mask))
        # borda branca para destacar em qualquer foto
        borda = Image.new("RGBA", (lado + 12, lado + 12), (0, 0, 0, 0))
        ImageDraw.Draw(borda).ellipse((0, 0, lado + 11, lado + 11), fill=(255, 255, 255, 255))
        borda.alpha_composite(selo, (6, 6))
        img = img.convert("RGBA")
        img.alpha_composite(borda, (1080 - lado - 40, 1080 - lado - 40))
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, "JPEG", quality=88)
    return out.getvalue()
