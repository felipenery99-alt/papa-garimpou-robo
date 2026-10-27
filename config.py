"""Configuração do robô do Papa Garimpou. Regras de negócio ficam aqui, não espalhadas pelo código."""

# ---------------------------------------------------------------------------
# DESTINOS PERMITIDOS — trava de segurança. O robô recusa postar em qualquer
# outro lugar, mesmo que um segredo/variável aponte para outro chat.
# ---------------------------------------------------------------------------
CANAIS = {
    "achadinhos": "@papagarimpou",
    "marcas": "@papagarimpoumarcas",
}
DESTINOS_PERMITIDOS = frozenset(CANAIS.values())

# Único Instagram permitido. Antes de qualquer post no Instagram, conferir que a
# conta logada é exatamente esta; se não for, NÃO postar e avisar.
INSTAGRAM_PERMITIDO = "papa.garimpou"

# Agenda diária do Instagram (horário de Brasília, "HH:MM", tipo). Cada tarefa roda na
# primeira execução do robô depois do horário (até 50 min). Escolhidos logo antes das
# execuções do robo.yml. Total: 8 stories + 2 posts por dia.
STORIES_MINIMOS = 3   # o robô nunca deixa menos de 3 stories no ar (regra do Felipe)
INSTAGRAM_AGENDA = [
    ("08:45", "story_oferta"), ("10:20", "story_oferta"), ("11:50", "carrossel_top5"),
    ("12:15", "story_oferta"), ("13:20", "story_convite"), ("15:00", "story_oferta"),
    ("18:05", "story_oferta"), ("19:15", "post_achado"), ("20:35", "story_oferta"),
    ("21:20", "story_convite"),
]

# ---------------------------------------------------------------------------
# RITMO
# ---------------------------------------------------------------------------
POSTS_POR_CANAL_DIA = 10
JANELA_INICIO = (8, 0)    # 08:00
JANELA_FIM = (22, 0)      # 22:00
INTERVALO_MIN_MIN = 45    # mínimo entre posts do mesmo canal
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
]

MARCAS_MARCAS = [
    "lacoste", "tommy hilfiger", "tommy", "calvin klein", "hugo boss", "boss", "ralph lauren",
    "polo ralph lauren", "insider", "reserva", "hering", "lupo", "nike", "adidas", "puma",
    "olympikus", "mizuno", "asics", "new balance", "fila", "under armour", "kappa", "oakley",
    "growth", "max titanium", "integralmédica", "integralmedica", "dux", "probiótica",
    "probiotica", "black skull", "blenderbottle", "garmin", "mormaii", "speedo", "colcci",
    "aramis", "richards", "levi's", "levis", "ellus", "osklen", "diesel", "armani",
    "emporio armani", "guess", "dudalina", "vr", "foxton", "selene", "mash", "zorba",
]

# Palavras que denunciam produto ruim / réplica → descarte imediato
PALAVRAS_PROIBIDAS = [
    "réplica", "replica", "inspirada", "inspirado", "similar", "tipo original", "1ª linha",
    "primeira linha", "aaa", "importada premium", "genérico", "generico", "sem marca",
    "tailandesa", "paralela",
]

# Termos de busca por canal (rotacionados a cada execução)
BUSCAS = {
    "marcas": [
        "cueca lupo", "cueca calvin klein", "camisa polo lacoste", "camiseta básica hering",
        "camiseta insider tech", "camisa polo tommy hilfiger", "camiseta reserva",
        "cueca boxer puma", "tênis corrida mizuno", "tênis olympikus", "tênis asics",
        "creatina growth", "whey protein max titanium", "coqueteleira blenderbottle",
        "óculos oakley", "camiseta dry fit nike", "meia nike", "camisa polo hugo boss",
    ],
    "achadinhos": [
        "fone jbl", "air fryer mondial", "aspirador wap", "mouse logitech", "carregador anker",
        "power bank baseus", "panela tramontina", "liquidificador oster", "ssd kingston",
        "caixa de som jbl", "aparador philips", "secador taiff", "escova oral-b",
        "kit ferramentas bosch", "smartwatch xiaomi", "cafeteira electrolux",
    ],
}
