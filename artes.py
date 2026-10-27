"""Artes do Instagram do Papa Garimpou (stories 1080x1920 e posts 1080x1350), em JPEG.

Zonas seguras do story: nada importante nos 250 px de cima nem nos 340 px de baixo
(ali ficam a barra de progresso e a caixa de resposta do Instagram).
"""
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

PASTA = Path(__file__).parent / "assets"
FONTE = PASTA / "Baloo2.ttf"
SELO = PASTA / "selo-papa.png"

TEMAS = {
    "achadinhos": {"fundo": ((255, 176, 0), (242, 92, 0)), "texto": (30, 27, 75), "destaque": (30, 27, 75),
                    "destaque_txt": (255, 255, 255), "canal": "t.me/papagarimpou"},
    "marcas": {"fundo": ((42, 42, 42), (0, 0, 0)), "texto": (245, 197, 66), "destaque": (245, 197, 66),
               "destaque_txt": (18, 18, 18), "canal": "t.me/papagarimpoumarcas"},
}


def _fonte(tam: int, peso: str = "ExtraBold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTE), tam)
    try:
        f.set_variation_by_name(peso)
    except Exception:
        pass
    return f


def _gradiente(w: int, h: int, c1, c2) -> Image.Image:
    base = Image.new("RGB", (w, h), c1)
    topo = Image.new("RGB", (w, h), c2)
    mask = Image.linear_gradient("L").resize((w, h))
    return Image.composite(topo, base, mask)


def _brl(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _quebrar(draw, texto, fonte, largura, max_linhas=2):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    linhas.append(atual)
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = linhas[-1].rstrip(" ,.-") + "…"
    return linhas


def _centro(draw, y, texto, fonte, cor, w=1080):
    x = (w - draw.textlength(texto, font=fonte)) / 2
    draw.text((x, y), texto, font=fonte, fill=cor)


def _selo(lado: int) -> Image.Image:
    selo = Image.open(SELO).convert("RGBA").resize((lado, lado), Image.LANCZOS)
    mask = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, lado, lado), fill=255)
    out = Image.new("RGBA", (lado + 16, lado + 16), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse((0, 0, lado + 15, lado + 15), fill=(255, 255, 255, 255))
    selo.putalpha(mask)
    out.alpha_composite(selo, (8, 8))
    return out


def _cabecalho(img: Image.Image, tema: dict, y: int = 260):
    d = ImageDraw.Draw(img)
    img.paste(_selo(150), (70, y - 30), _selo(150))
    d.text((250, y - 5), "PAPA", font=_fonte(62), fill=tema["texto"])
    d.text((250, y + 45), "GARIMPOU", font=_fonte(80), fill=tema["texto"])


def _foto_produto(url: str, lado: int) -> Image.Image:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    foto = Image.open(io.BytesIO(r.content)).convert("RGB")
    foto = ImageOps.pad(foto, (lado - 60, lado - 60), color=(255, 255, 255))
    card = Image.new("RGB", (lado, lado), (255, 255, 255))
    card.paste(foto, (30, 30))
    mask = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, lado, lado), radius=48, fill=255)
    card.putalpha(mask)
    return card


def _jpeg(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=90)
    return out.getvalue()


def story_oferta(oferta: dict, canal: str) -> bytes:
    tema = TEMAS[canal]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    _cabecalho(img, tema)
    card = _foto_produto(oferta["imagem"], 820)
    img.alpha_composite(card, (130, 470))
    if oferta.get("desconto"):
        selo_txt = f"-{oferta['desconto']}%"
        f = _fonte(70)
        w = d.textlength(selo_txt, font=f) + 70
        d.rounded_rectangle((910 - w, 440, 960, 560), radius=60, fill=(225, 29, 72))
        d.text((910 - w + 35, 450), selo_txt, font=f, fill=(255, 255, 255))
    y = 1320
    for linha in _quebrar(d, oferta["nome"], _fonte(52, "Bold"), 900):
        _centro(d, y, linha, _fonte(52, "Bold"), tema["texto"])
        y += 62
    y += 10
    if oferta.get("preco_antigo") and oferta["preco_antigo"] > oferta["preco"]:
        txt = f"de {_brl(oferta['preco_antigo'])}"
        f = _fonte(44, "SemiBold")
        x = (1080 - d.textlength(txt, font=f)) / 2
        d.text((x, y), txt, font=f, fill=tema["texto"])
        d.line((x, y + 32, x + d.textlength(txt, font=f), y + 32), fill=tema["texto"], width=4)
        y += 60
    por = f"por {_brl(oferta['preco'])}"
    f = _fonte(78)
    w = d.textlength(por, font=f) + 80
    d.rounded_rectangle(((1080 - w) / 2, y, (1080 + w) / 2, y + 110), radius=55, fill=tema["destaque"])
    _centro(d, y + 8, por, f, tema["destaque_txt"])
    arroba = "@papagarimpoumarcas" if canal == "marcas" else "@papagarimpou"
    _centro(d, 1610, "Link no Telegram, grátis:", _fonte(44, "SemiBold"), tema["texto"])
    _centro(d, 1660, arroba, _fonte(58), tema["texto"])
    return _jpeg(img)


def story_top4(ofertas: list[dict]) -> bytes:
    """Story com os 4 melhores achados juntos (formato que as contas grandes de achados usam).
    Preços sempre os reais da loja; o "de" só aparece se a loja informou."""
    tema = TEMAS["achadinhos"]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    _cabecalho(img, tema)
    _centro(d, 415, "OS 4 MELHORES ACHADOS", _fonte(66), tema["texto"])
    lado, gap, x0, y0 = 380, 60, 130, 510
    for i, o in enumerate(ofertas[:4]):
        x = x0 + (i % 2) * (lado + gap)
        y = y0 + (i // 2) * (lado + 180)
        img.alpha_composite(_foto_produto(o["imagem"], lado), (x, y))
        if o.get("desconto"):
            txt, f = f"-{o['desconto']}%", _fonte(48)
            w = d.textlength(txt, font=f) + 40
            d.rounded_rectangle((x + lado - w - 10, y - 20, x + lado + 10, y + 60), radius=40, fill=(225, 29, 72))
            d.text((x + lado - w + 10, y - 14), txt, font=f, fill=(255, 255, 255))
        nome = _quebrar(d, o["nome"], _fonte(34, "Bold"), lado, max_linhas=1)[0]
        d.text((x + (lado - d.textlength(nome, font=_fonte(34, "Bold"))) / 2, y + lado + 12), nome,
               font=_fonte(34, "Bold"), fill=tema["texto"])
        por, f = _brl(o["preco"]), _fonte(54)
        w = d.textlength(por, font=f) + 50
        d.rounded_rectangle((x + (lado - w) / 2, y + lado + 62, x + (lado + w) / 2, y + lado + 142), radius=40,
                            fill=tema["destaque"])
        d.text((x + (lado - w) / 2 + 25, y + lado + 66), por, font=f, fill=tema["destaque_txt"])
    _centro(d, 1610, "Links no Telegram, grátis:", _fonte(44, "SemiBold"), tema["texto"])
    _centro(d, 1660, "@papagarimpou", _fonte(58), tema["texto"])
    return _jpeg(img)


def capa_reel(linhas=("ACHADOS", "DO PAPA"), sub="Só marca boa, com desconto de verdade") -> bytes:
    """Primeiro quadro do Reels: o Papa grande e a chamada."""
    tema = TEMAS["achadinhos"]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(560), (252, 330))
    y = 960
    for linha in linhas:
        _centro(d, y, linha, _fonte(140), tema["texto"])
        y += 150
    _centro(d, y + 20, sub, _fonte(52, "Bold"), (255, 255, 255))
    return _jpeg(img)


def story_convite() -> bytes:
    """Story fixo de convite para os canais (o mesmo todo dia)."""
    tema = TEMAS["achadinhos"]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(520), (270, 300))
    y = 880
    for linha, tam in (("O PAPA GARIMPA", 96), ("SÓ MARCA", 120), ("BOA", 120)):
        _centro(d, y, linha, _fonte(tam), tema["texto"])
        y += tam + 10
    y += 30
    for linha in ("Achou, postou. Só loja oficial.", "Grátis, no Telegram."):
        _centro(d, y, linha, _fonte(54, "Bold"), (255, 255, 255))
        y += 70
    y += 40
    d.rounded_rectangle((140, y, 940, y + 130), radius=65, fill=tema["destaque"])
    _centro(d, y + 18, "LINK NA BIO", _fonte(80), (255, 255, 255))
    _centro(d, y + 160, "ou procure no Telegram:", _fonte(44, "SemiBold"), tema["texto"])
    _centro(d, y + 210, "@papagarimpou", _fonte(60), tema["texto"])
    return _jpeg(img)


INSTITUCIONAIS = [
    # (título linhas, subtítulo linhas) — histórias fixas do Papa, sem oferta
    (("RÉPLICA?", "AQUI NÃO."), ("O Papa só garimpa marca boa", "e loja oficial.")),
    (("COMO", "FUNCIONA"), ("1. Entre no canal do Papa", "2. Ative as notificações", "3. Compre com desconto")),
    (("O PAPA", "GARIMPOU"), ("Lacoste, Nike, Lupo, JBL...", "tudo com desconto de verdade.")),
]


def story_institucional(i: int) -> bytes:
    """Stories fixos que giram quando não há oferta (o convite é o índice -1)."""
    if i < 0:
        return story_convite()
    tema = TEMAS["marcas"] if i % 2 else TEMAS["achadinhos"]
    titulo, sub = INSTITUCIONAIS[i % len(INSTITUCIONAIS)]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(440), (310, 300))
    y = 820
    for linha in titulo:
        _centro(d, y, linha, _fonte(120), tema["texto"])
        y += 130
    y += 30
    for linha in sub:
        _centro(d, y, linha, _fonte(54, "Bold"), (255, 255, 255))
        y += 72
    _centro(d, 1560, "Telegram grátis: @papagarimpou", _fonte(50), tema["texto"])
    _centro(d, 1625, "link na bio", _fonte(44, "SemiBold"), tema["texto"])
    return _jpeg(img)


def feed_institucional(i: int) -> bytes:
    """Post de feed fixo 1080x1350, para nunca passar um dia sem feed."""
    tema = TEMAS["marcas"] if i % 2 else TEMAS["achadinhos"]
    titulo, sub = INSTITUCIONAIS[i % len(INSTITUCIONAIS)]
    img = _gradiente(1080, 1350, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(400), (330, 110))
    y = 580
    for linha in titulo:
        _centro(d, y, linha, _fonte(118), tema["texto"])
        y += 125
    y += 20
    for linha in sub:
        _centro(d, y, linha, _fonte(50, "Bold"), (255, 255, 255))
        y += 66
    _centro(d, 1230, "Telegram grátis: @papagarimpou · link na bio", _fonte(40, "SemiBold"), tema["texto"])
    return _jpeg(img)


LEGENDAS_INSTITUCIONAIS = [
    "😎💎 Réplica? Aqui não.\n\nO Papa só garimpa produto original, de marca boa e em loja oficial. Desconto de verdade, sem cilada.",
    "😎💎 Como funciona o Papa Garimpou:\n\n1. Entra no canal do Telegram (link na bio)\n2. Ativa as notificações\n3. Pega o achado antes de acabar",
    "😎💎 Lacoste, Nike, Lupo, Calvin Klein, JBL, Growth...\n\nAchou marca boa com desconto de verdade, o Papa posta na hora no Telegram.",
]


def post_oferta(oferta: dict, canal: str) -> bytes:
    """Post de feed 1080x1350 ('Achado do dia')."""
    tema = TEMAS[canal]
    img = _gradiente(1080, 1350, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    _cabecalho(img, tema, y=90)
    img.alpha_composite(_foto_produto(oferta["imagem"], 700), (190, 290))
    y = 1020
    for linha in _quebrar(d, oferta["nome"], _fonte(46, "Bold"), 940):
        _centro(d, y, linha, _fonte(46, "Bold"), tema["texto"])
        y += 56
    por = f"{_brl(oferta['preco'])}  ·  -{oferta.get('desconto', 0)}%"
    f = _fonte(70)
    w = d.textlength(por, font=f) + 80
    d.rounded_rectangle(((1080 - w) / 2, y + 10, (1080 + w) / 2, y + 115), radius=52, fill=tema["destaque"])
    _centro(d, y + 18, por, f, tema["destaque_txt"])
    return _jpeg(img)


def capa_top5() -> bytes:
    tema = TEMAS["achadinhos"]
    img = _gradiente(1080, 1350, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(440), (310, 140))
    _centro(d, 660, "TOP 5", _fonte(170), tema["texto"])
    _centro(d, 850, "DO PAPA HOJE", _fonte(96), tema["texto"])
    _centro(d, 1010, "Só marca boa, com desconto de verdade", _fonte(46, "Bold"), (255, 255, 255))
    _centro(d, 1160, "arrasta pro lado 👉".replace("👉", "→"), _fonte(56, "Bold"), tema["texto"])
    return _jpeg(img)
