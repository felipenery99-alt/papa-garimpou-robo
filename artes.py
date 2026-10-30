"""Artes do Instagram do Papa Garimpou (stories 1080x1920 e posts 1080x1350), em JPEG.

Zonas seguras do story: nada importante nos 250 px de cima nem nos 340 px de baixo
(ali ficam a barra de progresso e a caixa de resposta do Instagram).
"""
import io
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

import config

PASTA = Path(__file__).parent / "assets"
FONTE = PASTA / "Baloo2.ttf"
SELO = PASTA / "selo-papa.png"

TEMAS = {
    "achadinhos": {"fundo": ((255, 176, 0), (242, 92, 0)), "texto": (30, 27, 75), "destaque": (30, 27, 75),
                    "destaque_txt": (255, 255, 255), "canal": "t.me/papagarimpou"},
    "marcas": {"fundo": ((42, 42, 42), (0, 0, 0)), "texto": (245, 197, 66), "destaque": (245, 197, 66),
               "destaque_txt": (18, 18, 18), "canal": "t.me/papagarimpoumarcas"},
    "tech": {"fundo": ((30, 27, 75), (8, 12, 32)), "texto": (125, 211, 252), "destaque": (125, 211, 252),
             "destaque_txt": (8, 12, 32), "canal": "t.me/papagarimpoutech"},
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
    tema = tema_oferta(oferta)
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
    arroba = config.CANAIS.get(canal, "@papagarimpou")
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
    """Story fixo de convite: mostra os 4 canais para a pessoa escolher o seu."""
    # 30/10: o convite antigo ("@papagarimpou") não virava clique (2 cliques/dia, 2 membros/canal).
    # Agora lista os 4 canais grátis, cada um com o assunto, para quem só quer tech ou só roupa achar o seu.
    tema = TEMAS["achadinhos"]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(420), (330, 260))
    y = 730
    for linha, tam in (("4 CANAIS GRÁTIS", 104), ("ESCOLHA O SEU", 92)):
        _centro(d, y, linha, _fonte(tam), tema["texto"])
        y += tam + 14
    y += 30
    for assunto, arroba in (("Casa, cozinha e beleza", "@papagarimpou"),
                            ("Roupa, tênis e esporte", "@papagarimpoumarcas"),
                            ("Eletrônicos e games", "@papagarimpoutech"),
                            ("Todas as ofertas juntas", "@papagarimpouofertas")):
        _centro(d, y, assunto, _fonte(42, "SemiBold"), (255, 255, 255))
        _centro(d, y + 50, arroba, _fonte(56), tema["texto"])
        y += 140
    y += 20
    d.rounded_rectangle((140, y, 940, y + 130), radius=65, fill=tema["destaque"])
    _centro(d, y + 18, "LINK NA BIO", _fonte(80), (255, 255, 255))
    _centro(d, y + 160, "Só marca boa e loja oficial. Sem cilada.", _fonte(40, "SemiBold"), tema["texto"])
    return _jpeg(img)


def story_parceria(arroba: str, assuntos: list[str]) -> bytes:
    """Story de troca de divulgação com outro perfil de achadinhos (parceria sem custo)."""
    tema = PALETAS_OFERTA[5]
    img = _gradiente(1080, 1920, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(360), (360, 280))
    y = 720
    _centro(d, y, "O PAPA INDICA", _fonte(104), tema["texto"])
    y += 134
    _centro(d, y, "Perfil parceiro com achado bom:", _fonte(46, "SemiBold"), (255, 255, 255))
    y += 90
    fonte = _fonte(76)
    while d.textlength(arroba, font=fonte) > 960:
        fonte = _fonte(fonte.size - 4)
    d.rounded_rectangle((60, y - 10, 1020, y + 120), radius=60, fill=tema["destaque"])
    _centro(d, y + 12, arroba, fonte, tema["destaque_txt"])
    y += 190
    for a in assuntos:
        _centro(d, y, a, _fonte(50, "SemiBold"), (255, 255, 255))
        y += 70
    _centro(d, y + 50, "Corre lá e segue!", _fonte(64), tema["destaque"])
    return _jpeg(img)


# Dono, 29/10: "você ainda está postando coisa da mesma cor". A cor da arte de oferta não segue
# mais o canal (num dia só de games saía tudo azul-escuro): gira por estas paletas, pela oferta.
PALETAS_OFERTA = [
    {"fundo": ((255, 176, 0), (242, 92, 0)), "texto": (30, 27, 75), "destaque": (30, 27, 75), "destaque_txt": (255, 255, 255)},
    {"fundo": ((30, 27, 75), (8, 12, 32)), "texto": (125, 211, 252), "destaque": (125, 211, 252), "destaque_txt": (8, 12, 32)},
    {"fundo": ((42, 42, 42), (0, 0, 0)), "texto": (245, 197, 66), "destaque": (245, 197, 66), "destaque_txt": (18, 18, 18)},
    {"fundo": ((255, 77, 94), (159, 18, 57)), "texto": (255, 255, 255), "destaque": (255, 255, 255), "destaque_txt": (159, 18, 57)},
    {"fundo": ((16, 185, 129), (6, 95, 70)), "texto": (255, 255, 255), "destaque": (255, 230, 150), "destaque_txt": (6, 78, 59)},
    {"fundo": ((139, 92, 246), (76, 29, 149)), "texto": (255, 255, 255), "destaque": (253, 224, 71), "destaque_txt": (59, 7, 100)},
    {"fundo": ((255, 248, 232), (255, 228, 190)), "texto": (30, 27, 75), "destaque": (225, 29, 72), "destaque_txt": (255, 255, 255)},
    {"fundo": ((14, 165, 233), (3, 105, 161)), "texto": (255, 255, 255), "destaque": (255, 255, 255), "destaque_txt": (3, 105, 161)},
]


def tema_oferta(oferta: dict) -> dict:
    import zlib
    return PALETAS_OFERTA[zlib.crc32(str(oferta.get("id", oferta.get("nome", ""))).encode()) % len(PALETAS_OFERTA)]


def post_oferta(oferta: dict, canal: str) -> bytes:
    """Post de feed 1080x1350 ('Achado do dia')."""
    tema = tema_oferta(oferta)
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


# Capas do carrossel diário: cor e frase mudam a cada dia (dono, 28/10: "o feed tá ficando tudo igual")
CAPAS_TOP = [
    ("achadinhos", "TOP 5", "DO PAPA HOJE", "Só marca boa, com desconto de verdade"),
    ("tech", "5 ACHADOS", "QUE VALEM O PIX", "Preço conferido na loja, nada inventado"),
    ("marcas", "O PAPA", "SEPAROU 5", "Original, de loja confiável"),
    ("vermelho", "ACHOU,", "POSTOU", "Os 5 descontos mais fortes do dia"),
    ("achadinhos", "GARIMPO", "DO DIA", "5 coisas boas pagando menos"),
    ("tech", "SEM", "CILADA", "5 ofertas de marca que o Papa aprovou"),
    ("marcas", "5 MOTIVOS", "PRA ABRIR O PIX", "Achados de marca, preço de verdade"),
]
TEMAS["vermelho"] = {"fundo": ((255, 77, 94), (159, 18, 57)), "texto": (255, 255, 255), "destaque": (255, 255, 255),
                     "destaque_txt": (159, 18, 57), "canal": "t.me/papagarimpouofertas"}


def capa_top5(variante: int = 0) -> bytes:
    nome_tema, l1, l2, sub = CAPAS_TOP[variante % len(CAPAS_TOP)]
    tema = TEMAS[nome_tema]
    img = _gradiente(1080, 1350, *tema["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_selo(440), (310, 140))
    _centro(d, 660, l1, _fonte(150 if len(l1) > 6 else 170), tema["texto"])
    _centro(d, 850, l2, _fonte(90), tema["texto"])
    _centro(d, 1010, sub, _fonte(46, "Bold"), (255, 255, 255) if nome_tema != "vermelho" else (255, 230, 150))
    _centro(d, 1160, "arrasta pro lado →", _fonte(56, "Bold"), tema["texto"])
    return _jpeg(img)


# ---------------------------------------------------------------------------
# Peças do banco de conteúdo (conteudo.py): cada layout tem cara própria,
# para o perfil não parecer o mesmo post repetido.
# ---------------------------------------------------------------------------
ESTILOS = {
    "dica": {"fundo": ((30, 27, 75), (12, 11, 38)), "titulo": (255, 255, 255), "card": (255, 255, 255),
             "card_txt": (30, 27, 75), "selo_bg": (255, 176, 0), "selo_txt": (30, 27, 75), "rodape": (255, 176, 0)},
    "meme": {"fundo": ((18, 18, 18), (0, 0, 0)), "titulo": (255, 255, 255), "card": None,
             "card_txt": (245, 197, 66), "selo_bg": None, "selo_txt": None, "rodape": (160, 160, 160)},
    "checklist": {"fundo": ((255, 248, 232), (255, 236, 200)), "titulo": (30, 27, 75), "card": None,
                  "card_txt": (30, 27, 75), "selo_bg": (30, 27, 75), "selo_txt": (255, 255, 255), "rodape": (30, 27, 75)},
    "frase": {"fundo": ((42, 42, 42), (0, 0, 0)), "titulo": (245, 197, 66), "card": None,
              "card_txt": (255, 255, 255), "selo_bg": None, "selo_txt": None, "rodape": (245, 197, 66)},
    "mito": {"fundo": ((237, 242, 255), (210, 222, 255)), "titulo": (30, 27, 75), "card": (255, 255, 255),
             "card_txt": (30, 27, 75), "selo_bg": (30, 27, 75), "selo_txt": (255, 255, 255), "rodape": (30, 27, 75)},
    "contagem": {"fundo": ((225, 29, 72), (120, 10, 40)), "titulo": (255, 255, 255), "card": None,
                 "card_txt": (255, 255, 255), "selo_bg": (0, 0, 0), "selo_txt": (255, 255, 255), "rodape": (255, 220, 120)},
}


# Variações de cor por layout (escolhida pelo id da peça: fixa para a peça, variada no perfil)
VARIANTES = {
    "dica": [{}, {"fundo": ((0, 92, 75), (0, 48, 40)), "selo_bg": (255, 210, 63), "rodape": (255, 210, 63)},
             {"fundo": ((88, 28, 135), (40, 10, 70)), "selo_bg": (255, 122, 0), "selo_txt": (255, 255, 255),
              "rodape": (255, 176, 0)}],
    "meme": [{}, {"fundo": ((255, 176, 0), (242, 92, 0)), "titulo": (30, 27, 75), "card_txt": (255, 255, 255),
                  "rodape": (30, 27, 75)}],
    "frase": [{}, {"fundo": ((14, 116, 144), (8, 51, 68)), "titulo": (255, 255, 255), "card_txt": (186, 230, 253),
                   "rodape": (186, 230, 253)}],
    "checklist": [{}, {"fundo": ((220, 252, 231), (187, 247, 208)), "selo_bg": (22, 101, 52)}],
}


def _estilo(p: dict) -> dict:
    e = dict(ESTILOS[p["layout"]])
    var = VARIANTES.get(p["layout"])
    if var:
        e.update(var[sum(map(ord, p["id"])) % len(var)])
    return e


def mosaico(linhas_meio=("ACHADOS DE MARCA", "COM DESCONTO", "DE VERDADE")) -> list[bytes]:
    """Painel de 3 posts que formam uma imagem só no perfil (esquerda, meio, direita).
    Publicar na ordem direita → meio → esquerda, para ficar certo na grade."""
    W, H = 3240, 1350
    img = _gradiente(W, H, (255, 176, 0), (242, 92, 0)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle((2160, 0, W, H), fill=(30, 27, 75))
    img.alpha_composite(_selo(760), (150, 260))
    _centro(d, 1110, "O PAPA GARIMPOU", _fonte(92), (30, 27, 75), w=2160 - 1080)  # centrado no 1º quadro
    y = 380
    for linha in linhas_meio:
        x = 1080 + (1080 - d.textlength(linha, font=_fonte(96))) / 2
        d.text((x, y), linha, font=_fonte(96), fill=(30, 27, 75))
        y += 116
    x = 1080 + (1080 - d.textlength("Só loja oficial. Nada de réplica.", font=_fonte(52, "Bold"))) / 2
    d.text((x, y + 40), "Só loja oficial. Nada de réplica.", font=_fonte(52, "Bold"), fill=(255, 255, 255))
    for k, (linha, tam, cor) in enumerate((("TELEGRAM", 120, (255, 176, 0)), ("GRÁTIS", 120, (255, 255, 255)),
                                           ("@papagarimpou", 70, (255, 255, 255)), ("link na bio", 56, (255, 176, 0)))):
        f = _fonte(tam)
        d.text((2160 + (1080 - d.textlength(linha, font=f)) / 2, 380 + k * 150), linha, font=f, fill=cor)
    return [_jpeg(img.crop((i * 1080, 0, (i + 1) * 1080, H))) for i in range(3)]


def _pill(d, y, texto, bg, cor, tam=46, w=1080):
    f = _fonte(tam)
    largura = d.textlength(texto, font=f) + 70
    x = (w - largura) / 2
    d.rounded_rectangle((x, y, x + largura, y + tam + 34), radius=(tam + 34) // 2, fill=bg)
    d.text((x + 35, y + 10), texto, font=f, fill=cor)


def peca(p: dict, story: bool = True) -> bytes:
    """Arte de uma peça do banco: story 1080x1920 ou feed 1080x1350."""
    H = 1920 if story else 1350
    e = _estilo(p)
    img = _gradiente(1080, H, *e["fundo"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    topo = 270 if story else 80          # zona segura do story
    lay = p["layout"]
    y = topo
    if lay in ("meme", "frase"):
        lado = 420 if story else 300
        if lay == "meme":
            for linha in p["titulo"]:
                _centro(d, y, linha, _fonte(100 if story else 88), e["titulo"])
                y += 110 if story else 96
            y += 30
            img.alpha_composite(_selo(lado), ((1080 - lado - 16) // 2, y))
            y += lado + 60
            for linha in p["corpo"]:
                _centro(d, y, linha, _fonte(70 if story else 60), e["card_txt"])
                y += 82 if story else 70
        else:
            img.alpha_composite(_selo(lado), ((1080 - lado - 16) // 2, y))
            y += lado + 70
            for linha in p["titulo"]:
                _centro(d, y, linha, _fonte(96 if story else 84), e["titulo"])
                y += 108 if story else 94
            y += 30
            for linha in p["corpo"]:
                _centro(d, y, linha, _fonte(58 if story else 52, "Bold"), e["card_txt"])
                y += 72 if story else 64
    elif lay == "contagem":
        _pill(d, y, "BLACK FRIDAY DO PAPA", e["selo_bg"], e["selo_txt"])
        y += 140
        grande = _fonte(520 if story else 400) if p["titulo"][0].isdigit() else _fonte(170)
        _centro(d, y, p["titulo"][0], grande, e["titulo"])
        y += (600 if story else 450) if p["titulo"][0].isdigit() else 230
        for linha in p["corpo"]:
            _centro(d, y, linha, _fonte(58, "Bold"), e["card_txt"])
            y += 74
        lado = 230
        img.alpha_composite(_selo(lado), ((1080 - lado - 16) // 2, H - (640 if story else 300)))
    else:   # dica, checklist, mito
        rotulo = "MITO OU VERDADE?" if lay == "mito" else p.get("selo", "DICA DO PAPA")
        _pill(d, y, rotulo, e["selo_bg"], e["selo_txt"])
        y += 140
        for linha in p["titulo"]:
            _centro(d, y, linha, _fonte(92 if story else 80), e["titulo"])
            y += 104 if story else 90
        y += 40
        if lay == "mito":
            verdade = p["veredito"] == "VERDADE"
            _pill(d, y, p["veredito"], (22, 163, 74) if verdade else (225, 29, 72), (255, 255, 255), tam=80)
            y += 160
        if lay == "checklist":
            for item in p["corpo"]:
                d.ellipse((150, y, 220, y + 70), fill=(22, 163, 74))
                d.line((168, y + 36, 182, y + 50, 204, y + 22), fill=(255, 255, 255), width=9)
                d.text((250, y - 2), item, font=_fonte(58, "Bold"), fill=e["card_txt"])
                y += 105
        else:
            linhas = p["corpo"]
            alto = len(linhas) * 70 + 70
            d.rounded_rectangle((90, y, 990, y + alto), radius=44, fill=e["card"])
            yy = y + 35
            for linha in linhas:
                _centro(d, yy, linha, _fonte(54, "Bold"), e["card_txt"])
                yy += 70
            y += alto
        lado = 200 if story else 150
        img.alpha_composite(_selo(lado), ((1080 - lado - 16) // 2, min(y + 50, H - (560 if story else 230))))
    rod = H - (330 if story else 70)
    _centro(d, rod, "Achados grátis no Telegram: @papagarimpou", _fonte(42, "SemiBold"), e["rodape"])
    return _jpeg(img)
