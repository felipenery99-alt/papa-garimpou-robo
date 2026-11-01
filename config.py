"""Configuração do robô do Papa Garimpou. Regras de negócio ficam aqui, não espalhadas pelo código."""

# ---------------------------------------------------------------------------
# DESTINOS PERMITIDOS — trava de segurança. O robô recusa postar em qualquer
# outro lugar, mesmo que um segredo/variável aponte para outro chat.
# ---------------------------------------------------------------------------
CANAIS = {
    "achadinhos": "@papagarimpou",
    "marcas": "@papagarimpoumarcas",
    # 28/10: canal de eletrônicos e games (Amazon e Magalu são fortes aqui). Regras de qualidade = achadinhos.
    "tech": "@papagarimpoutech",
}
# Canal "tudo em um" (27/10): recebe uma cópia de toda oferta postada nos canais de nicho,
# para quem quer tudo sem entrar em vários canais.
GERAL = "@papagarimpouofertas"
DESTINOS_PERMITIDOS = frozenset([*CANAIS.values(), GERAL])

# Único Instagram permitido. Antes de qualquer post no Instagram, conferir que a
# conta logada é exatamente esta; se não for, NÃO postar e avisar.
INSTAGRAM_PERMITIDO = "papa.garimpou"

# Agenda diária do Instagram (horário de Brasília, "HH:MM", tipo). Cada tarefa roda na
# primeira execução do robô depois do horário (até 50 min). Escolhidos logo antes das
# execuções do robo.yml. Total: ~25 stories (2 deles com os 4 melhores achados) + Reels (só com ofertas) + 2 posts por dia.
STORIES_MINIMOS = 3   # o robô nunca deixa menos de 3 stories no ar (regra do dono)
INSTAGRAM_AGENDA = [
    ("08:45", "story_oferta"), ("10:20", "story_oferta"), ("11:50", "carrossel_top5"),
    # 01/11 (Central): interativos "responde no direct" no lugar de story de oferta comum —
    # adivinha o preço 15h (resposta ~1 h depois), A ou B 18h05; às quintas o post das 19h15 vira o carrossel salvável
    ("12:15", "story_top4"), ("13:20", "story_convite"), ("15:00", "adivinha"), ("17:30", "reels"),
    ("18:05", "a_ou_b"), ("19:15", "post_achado"), ("20:35", "story_top4"),
    ("21:20", "story_convite"),  # 29/10: 2º convite no pico da noite (Telegram parado em 2 membros/canal)
    # 29/10, dono: "alimentar o feed" — mais 4 posts de achado (sem oferta, sai peça do banco)
    ("09:35", "post_achado"), ("14:25", "post_achado"), ("16:55", "post_achado"), ("20:50", "post_achado"),
    # 30/10 (CEO): Reels é o que alcança quem ainda não segue. 3 por dia nos picos, cada um com ofertas diferentes.
    ("12:40", "reels"), ("21:05", "reels"),
]

# Dono, 28/10: "o Will posta 20 stories por dia pelo menos". Além da agenda acima, cada
# execução do robo.yml publica 1 story (oferta do dia; sem oferta, peça do banco) → ~25/dia.
INSTAGRAM_AGENDA += [("16:05", "adivinha_resposta")]   # 15:51 virou a resposta do adivinha
INSTAGRAM_AGENDA += [(hm, "story_oferta") for hm in [
    "08:07", "08:52", "09:38", "10:24", "11:11", "11:56", "12:19", "12:47", "13:22", "14:08",
    "15:03", "16:44", "17:36", "18:09", "18:42", "19:17", "20:03", "20:38", "21:24"]]

# Carrossel "salvável" semanal (quinta, 19h15): 5 melhores de marca até R$ X, girando a categoria.
# (nome na capa, palavras que o nome do produto precisa ter, teto de preço)
SALVAVEIS = [
    ("fones de ouvido", ("fone", "headset", "buds"), 300),
    ("air fryers", ("air fryer", "airfryer", "fritadeira"), 600),
    ("tênis de corrida", ("tênis", "tenis"), 500),
]
SALVAVEL_DIA_SEMANA = 3   # quinta

# ---------------------------------------------------------------------------
# RITMO
# ---------------------------------------------------------------------------
# Sem cota diária (dono, 27/10): toda oferta boa encontrada é postada na hora.

JANELA_INICIO = (8, 0)    # 08:00
JANELA_FIM = (22, 0)      # 22:00
# Fila contínua (28/10, dono: "o cara manda coisa a cada 10 minutos"): cada execução garimpa,
# põe as ofertas boas numa fila e solta UMA de cada vez, alternando os canais de nicho, até
# perto da próxima execução. Cada nicho recebe ~1 a cada 15 min; o canal geral, ~1 a cada 7.
INTERVALO_POSTS_MIN = (6, 8)   # minutos entre um post e o próximo (sorteado, alternando canais)
# Meta do dono (28/10): 40–50 posts de manhã (8h–12h) e 50–60 à tarde/noite (12h–22h), em horários
# irregulares para não parecer robô: faixas largas (média ~5,5 e ~11 min) e atraso aleatório no 1º post.
INTERVALO_MANHA_MIN = (3, 8)
INTERVALO_TARDE_MIN = (6, 16)
ATRASO_INICIAL_MIN = (0.5, 4)


def intervalo_posts(hora: int) -> tuple[float, float]:
    return INTERVALO_MANHA_MIN if hora < 12 else INTERVALO_TARDE_MIN
CANAL_PARADO_MIN = 50          # 01/11 (meta do dono: nenhum canal >1 h sem post 8h–22h): passou disso, o canal tem prioridade
BUSCA_EXTRA_TERMOS = 4         # canal parado e sem item na fila: busca extra (páginas 3–4) em N termos sorteados do nicho
FILA_VALIDADE_H = 4            # oferta parada na fila há mais que isso sai (o preço pode ter mudado)
# Horários das execuções do robo.yml em Brasília (para a fila parar antes da próxima)
EXECUCOES = ["08:07", "08:52", "09:38", "10:24", "11:11", "11:56", "12:19", "12:47", "13:22", "14:08",
             "15:03", "16:44", "17:36", "18:09", "18:42", "19:17", "20:03", "20:38", "21:24"]
FUSO = "America/Sao_Paulo"
# Picos (peso maior no sorteio): almoço, fim de tarde, noite
PICOS = [((12, 0), (13, 30)), ((18, 0), (19, 30)), ((20, 30), (22, 0))]
NAO_REPETIR_DIAS = 7

# ---------------------------------------------------------------------------
# QUALIDADE — "nada de coisa ruim, só coisa boa e de marca boa"
# ---------------------------------------------------------------------------
NOTA_MINIMA = 4.6
VENDAS_MINIMAS = 500
DESCONTO_MINIMO = 25          # % (marcas premium raramente passam de 40%)
DESCONTO_MINIMO_ACHADINHOS = 30

MARCAS_ACHADINHOS = [
    "samsung", "apple", "xiaomi", "redmi", "jbl", "sony", "philips", "mondial", "electrolux",
    "britania", "britânia", "arno", "oster", "tramontina", "wap", "bosch", "makita",
    "black+decker", "black decker", "logitech", "anker", "baseus", "l'oréal", "loreal",
    "natura", "boticário", "boticario", "nivea", "gillette", "oral-b", "brastemp", "consul",
    "lenovo", "dell", "motorola", "lg", "multilaser pro", "positivo", "cadence", "elgin",
    "panasonic", "intelbras", "tp-link", "kingston", "sandisk", "edifier", "havit",
    "rayovac", "duracell", "3m", "stanley", "vonder", "tefal", "rochedo", "oxford",
    "dove", "rexona", "colgate", "sensodyne", "wella", "elseve", "salon line", "eudora",
    "taiff", "microsoft", "xbox", "playstation", "kindle", "echo dot", "amazon",
]

MARCAS_MARCAS = [
    "lacoste", "tommy hilfiger", "tommy", "calvin klein", "hugo boss", "boss", "ralph lauren",
    "polo ralph lauren", "insider", "reserva", "hering", "lupo", "nike", "adidas", "puma",
    "olympikus", "mizuno", "asics", "new balance", "fila", "under armour", "kappa", "oakley",
    "growth", "max titanium", "integralmédica", "integralmedica", "dux", "probiótica",
    "probiotica", "black skull", "blenderbottle", "garmin", "mormaii", "speedo", "colcci",
    "aramis", "richards", "levi's", "levis", "ellus", "osklen", "diesel", "armani",
    "emporio armani", "guess", "dudalina", "vr collezioni", "foxton", "selene", "mash", "zorba",
    # 01/11 (Telegram): perfume de marca nacional, só loja oficial
    "o boticário", "boticário", "boticario", "natura", "eudora",
]

# Palavras que denunciam produto ruim / réplica → descarte imediato
PALAVRAS_PROIBIDAS = [
    "réplica", "replica", "inspirada", "inspirado", "similar", "tipo original", "1ª linha",
    "primeira linha", "aaa", "importada premium", "genérico", "generico", "sem marca",
    "tailandesa", "paralela",
    # 30/10: peça "compatível com Philips/Taiff/Tramontina" não é da marca, só usa o nome dela
    "compatível", "compativel", "universal", "vários modelos", "varios modelos", "serve em",
    # 01/11: perfume falsificado/contratipo
    "contratipo", "importado árabe", "importado arabe",
]
# 01/11: perfume árabe é o mais falsificado; essas marcas só pela Amazon.com.br, NUNCA pela Shopee
MARCAS_PROIBIDAS_SHOPEE = ["lattafa", "armaf", "al wataniah"]
# Perfume de marca (01/11, Telegram): prioridade fixa, no máximo 4 por dia somando os canais
PALAVRAS_PERFUME = ["perfume", "colônia", "colonia", "deo parfum", "eau de", "desodorante colônia"]
MAX_PERFUME_DIA = 4
# Máximo de ofertas da mesma marca por dia em cada canal (30/10: saíram 4 secadores Taiff seguidos)
MAX_MESMA_MARCA_DIA = 2

# Termos de busca por canal (rotacionados a cada execução)
BUSCAS = {
    "marcas": [
        "cueca lupo", "cueca calvin klein", "camisa polo lacoste", "camiseta básica hering",
        "camiseta insider tech", "camisa polo tommy hilfiger", "camiseta reserva",
        "cueca boxer puma", "tênis corrida mizuno", "tênis olympikus", "tênis asics",
        "creatina growth", "whey protein max titanium", "coqueteleira blenderbottle",
        "óculos oakley", "camiseta dry fit nike", "meia nike", "camisa polo hugo boss",
        # lote 28/10: mais buscas = fila cheia o dia todo
        "tênis nike", "tênis adidas", "tênis puma", "tênis new balance", "chinelo nike",
        "bermuda nike", "shorts adidas", "jaqueta adidas", "moletom nike", "mochila nike",
        "boné nike", "camiseta adidas", "legging lupo", "top fitness lupo", "meia lupo",
        "cueca tommy hilfiger", "camiseta calvin klein", "camisa polo ralph lauren",
        "camiseta levis", "relógio garmin", "sunga speedo", "whey growth", "creatina max titanium",
        "pré treino integralmedica", "barra de proteína", "garrafa térmica stanley",
        "malbec boticário", "kaiak natura", "egeo boticário",   # 01/11: perfume masculino de marca
    ],
    "tech": [
        "fone jbl", "mouse logitech", "carregador anker", "power bank baseus", "ssd kingston",
        "caixa de som jbl", "smartwatch xiaomi", "fone samsung galaxy buds", "redmi buds",
        "caixa de som jbl go", "fone sony", "teclado logitech", "headset logitech", "webcam logitech",
        "pendrive sandisk", "cartão de memória sandisk", "roteador tp-link", "carregador baseus",
        "cabo usb c anker", "smart tv samsung", "monitor lg", "notebook lenovo",
        "headset jbl quantum", "controle xbox", "controle playstation", "kindle", "echo dot",
        "celular samsung galaxy", "celular motorola", "tablet samsung",
    ],
    "achadinhos": [
        "air fryer mondial", "aspirador wap", "panela tramontina", "liquidificador oster",
        "aparador philips", "secador taiff", "escova oral-b", "kit ferramentas bosch",
        "cafeteira electrolux", "câmera intelbras",
        "furadeira bosch", "parafusadeira black decker", "jogo de panelas tramontina",
        "faqueiro tramontina", "batedeira mondial", "ventilador mondial", "sanduicheira britania",
        "chapinha taiff", "barbeador philips", "perfume o boticário", "perfume natura", "perfume eudora", "kit natura",
        "protetor solar nivea", "escova elétrica oral-b", "creme wella",
    ],
}
