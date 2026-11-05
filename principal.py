"""Robô do Papa Garimpou — 20 execuções por dia (GitHub Actions), com fila contínua entre elas.

Em cada execução: vê se algum horário sorteado do dia chegou; se sim, garimpa,
filtra (marca boa, loja oficial, nota, vendas, desconto), escolhe a melhor oferta
ainda não postada nos últimos 7 dias, aplica o selo do Papa e posta no canal.

Uso:
  python principal.py                 # execução normal (precisa dos segredos)
  python principal.py --ensaio        # usa ofertas de exemplo, não posta nada
  python principal.py --agenda        # mostra os horários de hoje
  python principal.py --testar-shopee # testa a API da Shopee sem postar
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import config
import post
import conteudo
import qualidade

PASTA = Path(__file__).parent
HIST = PASTA / "dados" / "historico.json"
FUSO = ZoneInfo(config.FUSO)


def carregar_hist() -> dict:
    if HIST.exists():
        return json.loads(HIST.read_text(encoding="utf-8"))
    return {"slots_feitos": [], "postados": {}}


def salvar_hist(h: dict) -> None:
    limite = (datetime.now(FUSO) - timedelta(days=30)).date().isoformat()
    h["slots_feitos"] = [s for s in h["slots_feitos"] if s[:10] >= limite]
    h["postados"] = {k: v for k, v in h["postados"].items() if v[:10] >= limite}
    dois_dias = (datetime.now(FUSO) - timedelta(days=2)).date().isoformat()
    h["ofertas_dia"] = [o for o in h.get("ofertas_dia", []) if o.get("dia", "") >= dois_dias]
    HIST.parent.mkdir(exist_ok=True)
    HIST.write_text(json.dumps(h, ensure_ascii=False, indent=1), encoding="utf-8")


RELATORIO = PASTA / "dados" / "relatorio.json"


def gravar_relatorio(h: dict, agora: datetime) -> None:
    """Resumo do dia para o 'CEO do Papa' (rotina na nuvem) analisar e decidir.
    Só números e textos de erro — nunca tokens."""
    import os
    import telegram
    hoje = agora.date().isoformat()
    rel = json.loads(RELATORIO.read_text(encoding="utf-8")) if RELATORIO.exists() else {}
    dia = rel.setdefault(hoje, {"erros": []})
    dia["ultima_execucao"] = agora.strftime("%H:%M")
    dia["execucoes"] = dia.get("execucoes", 0) + 1
    dia["telegram_posts"] = {c: sum(1 for s in h["slots_feitos"] if s.startswith(f"{hoje} {c}")) for c in config.CANAIS}
    dia["ultimo_post"] = ultimo_post(h, agora)
    if h.get("ultimo_garimpo"):
        dia["ultimo_garimpo"] = datetime.fromisoformat(h["ultimo_garimpo"]).strftime("%d/%m %H:%M")
    dia["convites_story"] = {n: len(c["entradas"]) for n, c in h.get("convites_story", {}).items()}
    dia["telegram_membros"] = {c: telegram.membros(d) for c, d in {**config.CANAIS, "geral": config.GERAL}.items()}
    dia["instagram_feito"] = [f[11:] for f in h.get("ig_feitos", []) if f.startswith(hoje)]
    dia["shopee_ligada"] = bool(os.environ.get("SHOPEE_APP_ID"))
    if OFICIAL_SHOPEE:   # ofertas únicas de loja oficial vistas no dia, pelo último motivo
        ids = {**dia.get("shopee_oficial_ids", {}), **OFICIAL_SHOPEE}
        dia["shopee_oficial_ids"] = ids
        resumo = {}
        for m in ids.values():
            resumo[m] = resumo.get(m, 0) + 1
        dia["shopee_oficial"] = dict(sorted(resumo.items(), key=lambda x: -x[1]))
    for d in rel:   # a lista de ids só serve para o dia corrente; nos dias fechados fica só o resumo
        if d != hoje:
            rel[d].pop("shopee_oficial_ids", None)
    if os.environ.get("META_TOKEN"):
        try:
            import instagram
            dia["instagram"] = instagram.metricas()
            dia["instagram"]["stories_ativos"] = instagram.stories_ativos()
        except Exception as e:
            dia["instagram"] = {"erro": str(e)[:200]}
    dia["erros"] = (dia.get("erros", []) + telegram.ERROS)[-30:]
    for velho in sorted(rel)[:-14]:
        rel.pop(velho)
    RELATORIO.write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")


def chave_nome(nome: str) -> str:
    """Nome do produto sem acento/pontuação/espaço: o mesmo produto em outra cor/tamanho tem outro
    código (ASIN/MLB), mas o mesmo nome. 30/10: a Tech T-shirt Insider Gola U saiu 2x (B0BFT7XG6C e B0CCSLRZ19)."""
    import unicodedata
    n = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", n)


def ja_postado_recente(h: dict, oferta_id: str, agora: datetime, nome: str = "") -> bool:
    limite = agora - timedelta(days=config.NAO_REPETIR_DIAS)
    if nome and any(o.get("dia", "") >= limite.date().isoformat() and chave_nome(o.get("nome", "")) == chave_nome(nome)
                    for o in h.get("ofertas_dia", [])):
        return True   # cobre o que foi postado antes de existir postados_nome
    for quando in (h["postados"].get(oferta_id), h.get("postados_nome", {}).get(chave_nome(nome)) if nome else None):
        if quando and datetime.fromisoformat(quando) > limite:
            return True
    return False


# 04/11 (dono: "somente loja oficial sempre"): antes de mexer em qualquer limite, medir quantas ofertas de
# LOJA OFICIAL da Shopee caem e por quê (e quantas ficam perto do limite). Vai para relatorio.json por dia.
OFICIAL_SHOPEE: dict = {}


def _motivo_oficial(o: dict, canal: str, ok: bool, motivo: str) -> str:
    if ok:
        return "aprovada"
    if motivo.startswith("poucas vendas"):
        minimo = qualidade.vendas_minimas(o)
        return f"vendas perto ({minimo // 2}+)" if (o.get("vendas") or 0) >= minimo / 2 else "vendas longe"
    if motivo.startswith("desconto"):
        minimo = config.DESCONTO_MINIMO if canal == "marcas" else config.DESCONTO_MINIMO_ACHADINHOS
        return "desconto perto (até 10 pts)" if (o.get("desconto") or 0) >= minimo - 10 else "desconto longe"
    if motivo.startswith("nota"):
        return "nota"
    return "outro: " + re.sub(r"\(.*?\)|\d+", "", motivo).strip()[:40]


def garimpar_todas(canal: str, fonte, h: dict, agora: datetime, termos: list[str] | None = None) -> list[dict]:
    """Todas as ofertas boas e não postadas de todas as buscas do canal, melhores primeiro.
    Sem cota: o único filtro é a qualidade (regra do dono: achou coisa boa, posta)."""
    reprovados = {}
    boas = {}
    lista = termos or config.BUSCAS[canal]
    falhas = []
    for termo in lista:
        try:
            ofertas = fonte(termo)
        except Exception as e:
            # 02/11: uma busca que falha (ex.: limite 10030) não derruba mais o garimpo do canal inteiro
            falhas.append(f"'{termo}': {e}")
            if "limite" in str(e).lower() or "10030" in str(e):
                break   # API travada nesta execução: segue com o que já achou
            continue
        for o in ofertas:
            ok, motivo = qualidade.avaliar(o, canal)
            if str(o.get("id", "")).startswith("shopee") and o.get("loja_oficial"):
                OFICIAL_SHOPEE[o["id"]] = _motivo_oficial(o, canal, ok, motivo)
            if ok and not ja_postado_recente(h, o["id"], agora, o.get("nome", "")):
                boas[o["id"]] = o
            elif not ok:
                reprovados[motivo] = reprovados.get(motivo, 0) + 1
    if falhas:
        print(f"[{canal}] {len(falhas)} busca(s) falharam; sigo com o que achei. Ex.: {falhas[0][:150]}")
        if len(falhas) == len(lista) and not boas:
            raise RuntimeError(f"todas as buscas falharam: {falhas[0][:200]}")
    if not boas:
        print(f"[{canal}] nenhuma oferta boa. Reprovações: {reprovados}")
    # Variedade: no máximo MAX_MESMA_MARCA_DIA ofertas da mesma marca por dia no canal
    hoje = agora.date().isoformat()
    por_marca = {}
    for o in h.get("ofertas_dia", []) + h.get("fila", []):
        if o.get("canal") == canal and (o.get("dia", hoje) == hoje):
            m = qualidade.marca_da_oferta(o, canal)
            por_marca[m] = por_marca.get(m, 0) + 1
    # Perfume de marca (01/11): prioridade fixa (entra na frente), no máximo MAX_PERFUME_DIA somando os canais
    perfumes = sum(1 for o in h.get("ofertas_dia", []) + h.get("fila", [])
                   if o.get("dia", hoje) == hoje and qualidade.eh_perfume(o))
    escolhidas = []
    for o in sorted(boas.values(), key=lambda o: (qualidade.eh_perfume(o), qualidade.pontuar(o)), reverse=True):
        m = qualidade.marca_da_oferta(o, canal)
        if por_marca.get(m, 0) >= config.MAX_MESMA_MARCA_DIA:
            continue
        if qualidade.eh_perfume(o):
            if perfumes >= config.MAX_PERFUME_DIA and agora.weekday() != config.BLOCO_PERFUME[0]:
                continue
            perfumes += 1
        por_marca[m] = por_marca.get(m, 0) + 1
        escolhidas.append(o)
    return escolhidas


def garimpar(canal: str, fonte, h: dict, agora: datetime, rodada: int = 0) -> dict | None:
    todas = garimpar_todas(canal, fonte, h, agora)
    return todas[0] if todas else None


MANUAIS = Path(__file__).parent / "ofertas_manuais.json"

# Menu fixado com botões para os outros canais (dono, 28/10). Mudar a versão faz o robô postar de novo.
MENU_VERSAO = "v1"
MENU_CANAIS = [
    ("🛒 Achadinhos: casa, cozinha, beleza", "https://t.me/papagarimpou"),
    ("👕 Marcas: roupa, tênis e esporte", "https://t.me/papagarimpoumarcas"),
    ("📱 Tech: eletrônicos e games", "https://t.me/papagarimpoutech"),
    ("💎 Todas as ofertas num lugar só", "https://t.me/papagarimpouofertas"),
]


BOAS_VINDAS_VERSAO = "bv1"   # mudar a versão faz o robô postar e fixar de novo
BOAS_VINDAS = ("💎 Bem-vindo ao Papa Garimpou!\n"
               "Aqui o Papa só posta coisa boa: marca conhecida, loja oficial e desconto de verdade, conferido na hora. "
               "Nada de réplica, nada de preço inventado.\n\n"
               "📢 Neste canal sai TUDO. Prefere só um assunto?\n"
               "🏠 Achadinhos (casa, cozinha, beleza): t.me/papagarimpou\n"
               "👟 Marcas (tênis, roupa, perfume, academia): t.me/papagarimpoumarcas\n"
               "🎮 Tech (games, TV, fone, celular): t.me/papagarimpoutech\n\n"
               "⚡ Todo dia tem oferta que sai primeiro aqui no Telegram, antes do Instagram.\n"
               "🔔 Ative as notificações: oferta boa acaba rápido.")


def publicar_menus(h: dict, telegram) -> None:
    feitos = h.setdefault("menus_fixados", [])
    # 05/11 (CEO, via PG · Telegram): no canal geral a mensagem fixada é a de boas-vindas, no lugar do menu
    chave = f"{BOAS_VINDAS_VERSAO} {config.GERAL}"
    if chave not in feitos:
        try:
            telegram.postar_texto_fixado(config.GERAL, BOAS_VINDAS)
            feitos.append(chave)
            salvar_hist(h)
        except Exception as e:
            telegram.avisar_dono(f"boas-vindas fixada em {config.GERAL} falhou: {e}")
    for destino in config.CANAIS.values():
        chave = f"{MENU_VERSAO} {destino}"
        if chave in feitos:
            continue
        outros = [(t, u) for t, u in MENU_CANAIS if not u.endswith("/" + destino.lstrip("@"))]
        try:
            telegram.postar_menu_fixado(destino, "💎 Os canais do Papa: toque e entre (é grátis) 👇", outros)
            feitos.append(chave)
            salvar_hist(h)
        except Exception as e:
            telegram.avisar_dono(f"menu fixado em {destino} falhou: {e}")


def pede_pro_papa_semanal(h: dict, telegram, agora: datetime) -> None:
    """02/11 (Telegram/Instagram): toda segunda à noite, convite "Pede pro Papa" nos 4 canais, fixado ~36 h
    (até quarta de manhã). Ao desafixar, o menu fixado antes volta ao topo sozinho."""
    fix = h.get("pede_fixados")
    if fix and agora.isoformat() >= fix["ate"]:
        for destino, mid in fix["msgs"].items():
            try:
                telegram.desafixar(destino, mid)
            except Exception as e:
                print(f"[pede] desafixar {destino}: {e}")
        h.pop("pede_fixados")
    semana = "%d-%02d" % agora.isocalendar()[:2]
    ini, fim = config.PEDE_SEMANAL_JANELA
    if agora.weekday() != config.PEDE_SEMANAL_DIA or not (ini <= f"{agora:%H:%M}" <= fim) \
            or h.get("pede_semana") == semana:
        return
    h["pede_semana"] = semana
    msgs = {}
    for destino in [*config.CANAIS.values(), config.GERAL]:
        try:
            msgs[destino] = telegram.postar_texto_fixado(destino, config.PEDE_SEMANAL_TEXTO)
        except Exception as e:
            telegram.avisar_dono(f"Pede pro Papa em {destino} falhou: {e}")
    h["pede_fixados"] = {"ate": (agora + timedelta(hours=36)).isoformat(), "msgs": msgs}
    salvar_hist(h)
    print(f"[pede] convite semanal fixado em {len(msgs)} canal(is)")


PEDIDOS = Path(__file__).parent / "pedidos_atendidos.json"


def carregar_pedidos(agora: datetime) -> list[dict]:
    """Pedidos do direct atendidos (gravados pela sessão Instagram), no formato de ofertas_manuais.json;
    valem até `valida_ate` ou, sem ela, por 2 dias a partir de `dia`."""
    if not PEDIDOS.exists():
        return []
    try:
        lista = json.loads(PEDIDOS.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"pedidos_atendidos.json inválido: {e}")
        return []
    limite = (agora - timedelta(days=2)).date().isoformat()
    validos = [o for o in lista if o.get("canal") in config.CANAIS and o.get("dia", "") >= limite
               and not (o.get("valida_ate") and o["valida_ate"] < agora.isoformat())]
    for o in validos:
        # 05/11: "proc-AAAAMMDD-N" = procura da semana. No Telegram vai a linha 💡 com o motivo
        # (campo "produto" = nome curto; sem ele, as 4 primeiras palavras do nome)
        if o["id"].startswith("proc-") and not o.get("extra"):
            produto = o.get("produto") or " ".join(o.get("nome", "").split()[:4])
            o["extra"] = f"Muita gente procurando {produto} essa semana… o Papa garimpou"
    return validos


def carregar_manuais(h: dict, agora: datetime) -> list[dict]:
    """Ofertas conferidas à mão (Amazon, Magalu, Awin): entram na fila enquanto não forem postadas
    e não passarem da validade (`valida_ate`, ISO). Canal desconhecido é ignorado."""
    lista = carregar_pedidos(agora)   # pedido atendido também vai para a fila do canal
    if MANUAIS.exists():
        try:
            lista += json.loads(MANUAIS.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ofertas_manuais.json inválido: {e}")
    boas = []
    for o in lista:
        if o.get("canal") not in config.CANAIS or o["id"] in h.get("postados", {}):
            continue
        if o.get("valida_ate") and o["valida_ate"] < agora.isoformat():
            continue
        # "nao_antes" (01/11): só entra na fila quando faltar menos de 1 h (esta execução alcança o horário);
        # na fila, soltar_fila segura o item até a hora. Antes disso fica no arquivo, sem descartar.
        if o.get("nao_antes") and o["nao_antes"] > (agora + timedelta(hours=1)).isoformat():
            continue
        boas.append(o)
    return boas


def entrar_na_fila(h: dict, canal: str, ofertas: list[dict], agora: datetime) -> None:
    """Põe as ofertas novas na fila (sem duplicar) e tira as que ficaram velhas."""
    corte = (agora - timedelta(hours=config.FILA_VALIDADE_H)).isoformat()
    fila = [f for f in h.get("fila", []) if f["entrou"] >= corte]
    na_fila = {f["id"] for f in fila}
    fila += [{**o, "canal": canal, "entrou": agora.isoformat()} for o in ofertas if o["id"] not in na_fila]
    h["fila"] = fila


def ultimo_post(h: dict, agora: datetime) -> dict:
    """Hora (HH:MM) do último post de hoje em cada canal de nicho; None se ainda não postou hoje."""
    hoje = agora.date().isoformat()
    ult = {c: None for c in config.CANAIS}
    for s in h.get("slots_feitos", []):
        partes = s.split(" ")
        if len(partes) >= 3 and partes[0] == hoje and partes[1] in ult:
            ult[partes[1]] = max(ult[partes[1]] or "", partes[2])
    return ult


def minutos_parado(h: dict, canal: str, agora: datetime) -> float:
    """Minutos desde o último post do canal; antes do 1º post do dia conta a partir das 8h."""
    hm = ultimo_post(h, agora)[canal]
    base = agora.replace(hour=int(hm[:2]), minute=int(hm[3:]), second=0, microsecond=0) if hm else         agora.replace(hour=config.JANELA_INICIO[0], minute=config.JANELA_INICIO[1], second=0, microsecond=0)
    return (agora - base).total_seconds() / 60


def conferir_oferta(o: dict, agora: datetime) -> dict | None:
    """Oferta ainda no ar e no preço? Shopee: consulta a API de novo (preço/desconto atuais, mesmas regras
    de qualidade). Fila manual (Amazon etc.): vale enquanto estiver em ofertas_manuais.json e na validade.
    O resto fica de fora (na dúvida, não entra no ranking)."""
    import os
    if o["id"].startswith("shopee-"):
        if not os.environ.get("SHOPEE_APP_ID"):
            return None
        import shopee
        try:
            achados = [n for n in shopee._pagina(o["nome"][:60], 1, 20) if n["id"] == o["id"]]
        except Exception:
            return None
        if not achados:
            return None
        novo = {**o, **achados[0], "canal": o["canal"]}
        return novo if qualidade.avaliar(novo, o["canal"])[0] else None
    man = {m["id"]: m for m in (json.loads(MANUAIS.read_text(encoding="utf-8")) if MANUAIS.exists() else [])}
    m = man.get(o["id"])
    if not m or (m.get("valida_ate") and m["valida_ate"] < agora.isoformat()):
        return None
    return {**o, **m}


def ranking_semana(h: dict, agora: datetime, n: int) -> list[dict]:
    """Maiores descontos reais dos últimos 7 dias que continuam válidos (um por produto)."""
    semana = (agora - timedelta(days=7)).date().isoformat()
    por_id = {}
    for o in sorted(h.get("ofertas_dia", []), key=lambda o: o.get("dia", "")):
        if o.get("dia", "") >= semana and o.get("preco_antigo") and o.get("link") and o.get("imagem"):
            por_id[o["id"]] = o
    vistos, saida = set(), []
    for o in sorted(por_id.values(), key=lambda o: o.get("desconto") or 0, reverse=True):
        if chave_nome(o.get("nome", "")) in vistos:
            continue
        ok = conferir_oferta(o, agora)
        if ok and ok.get("preco_antigo") and ok["preco_antigo"] > ok["preco"]:
            vistos.add(chave_nome(o.get("nome", "")))
            saida.append(ok)
        if len(saida) == n:
            break
    return sorted(saida, key=lambda o: o.get("desconto") or 0, reverse=True)


def top10_semana(h: dict, telegram, agora: datetime) -> None:
    """01/11 (Central, formato do concorrente): sábado 20h30, TOP 10 GARIMPOS DA SEMANA no canal geral,
    contagem #10 → #1, 1 post a cada ~3 min. É recap: pode repetir item dos últimos 7 dias."""
    import os
    import time as _time
    hoje = agora.date().isoformat()
    ini, fim = config.TOP10_JANELA
    if agora.weekday() != config.TOP10_DIA_SEMANA or not (ini <= f"{agora:%H:%M}" <= fim) \
            or h.get("top10_dia") == hoje:
        return
    h["top10_dia"] = hoje
    salvar_hist(h)   # marca antes: se o job cair no meio, não recomeça a contagem do zero
    itens = ranking_semana(h, agora, 10)
    if len(itens) < 5:
        telegram.avisar_dono(f"Top 10 da semana: só {len(itens)} oferta(s) ainda válida(s); não postei.")
        return
    for pos in range(len(itens), 0, -1):
        o = itens[pos - 1]
        topo = f"🏆 TOP {len(itens)} GARIMPOS DA SEMANA · #{pos}\n🔁 ainda no preço\n\n"
        try:
            telegram.postar_foto(config.GERAL, post.foto_com_selo(o["imagem"]), topo + post.legenda(o, o["canal"]))
            print(f"[top10] #{pos} {o['nome'][:50]}")
        except Exception as e:
            telegram.avisar_dono(f"Top 10 #{pos} falhou: {e}")
        if pos > 1 and not os.environ.get("PAPA_SEM_ATRASO"):
            _time.sleep(config.TOP10_INTERVALO_MIN * 60)


def em_bloco_perfume(agora: datetime) -> bool:
    dia, ini, fim = config.BLOCO_PERFUME
    return agora.weekday() == dia and ini <= f"{agora:%H:%M}" < fim


def socorrer_parados(h: dict, telegram, buscar_fundo, agora: datetime) -> None:
    """01/11 (31/10 o Tech ficou 19 h e o Marcas 15 h sem post): canal parado há mais de
    CANAL_PARADO_MIN e sem item na fila → busca extra na Shopee; se nem assim, avisa o dono
    uma vez por período (manhã/tarde/noite), em vez de ficar calado."""
    import random
    ini = agora.replace(hour=config.JANELA_INICIO[0], minute=config.JANELA_INICIO[1], second=0, microsecond=0)
    fim = agora.replace(hour=config.JANELA_FIM[0], minute=config.JANELA_FIM[1], second=0, microsecond=0)
    if not (ini <= agora <= fim):
        return
    for canal in config.CANAIS:
        # 03/11: Achadinhos ficou 6 h sem post e esta trava não deixou rastro no log; agora diz o que viu
        print(f"[parado] {canal}: {minutos_parado(h, canal, agora):.0f} min sem post, "
              f"{sum(1 for f in h.get('fila', []) if f['canal'] == canal)} na fila")
        if any(f["canal"] == canal for f in h.get("fila", [])) or minutos_parado(h, canal, agora) < config.CANAL_PARADO_MIN:
            continue
        if buscar_fundo:
            termos = random.sample(config.BUSCAS[canal], min(config.BUSCA_EXTRA_TERMOS, len(config.BUSCAS[canal])))
            try:
                entrar_na_fila(h, canal, garimpar_todas(canal, buscar_fundo, h, agora, termos), agora)
            except Exception as e:
                print(f"[parado] busca extra de {canal} falhou: {e}")
            if any(f["canal"] == canal for f in h.get("fila", [])):
                print(f"[parado] {canal}: busca extra achou oferta")
                continue
        periodo = "manhã" if agora.hour < 12 else ("tarde" if agora.hour < 18 else "noite")
        chave = f"{agora.date().isoformat()} {periodo} {canal}"
        avisos = h.setdefault("avisos_parado", [])
        if chave not in avisos:
            avisos.append(chave)
            h["avisos_parado"] = avisos[-30:]
            telegram.avisar_dono(f"canal {canal} sem oferta na fila há {minutos_parado(h, canal, agora):.0f} min "
                                 f"(busca extra também não achou). Abastecer ofertas_manuais.json.")


def ultimo_garimpo() -> datetime | None:
    """Hora do último commit "Garimpo ..." em ofertas_manuais.json (rotina do app no PC).
    Vem da API do GitHub porque o checkout do Actions é raso (sem histórico)."""
    import os
    import requests
    repo = os.environ.get("GITHUB_REPOSITORY", "felipenery99-alt/papa-garimpou-robo")
    cab = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}
    r = requests.get(f"https://api.github.com/repos/{repo}/commits", headers=cab, timeout=30,
                     params={"path": "ofertas_manuais.json", "per_page": 20})
    r.raise_for_status()
    for c in r.json():
        if c["commit"]["message"].lower().startswith("garimpo"):
            return datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00")).astimezone(FUSO)
    return None


def vigiar(h: dict, telegram, agora: datetime, ult_garimpo: datetime | None) -> None:
    """03/11 (dono): vigia de inatividade. Garimpo velho ou canal sem oferta na fila → aviso; canal sem post
    há VIGIA_POST_H → aviso. Cada tipo no máximo 1 vez a cada VIGIA_REPETIR_H (gravado no histórico)."""
    ini, fim = config.VIGIA_JANELA
    if not (ini <= f"{agora:%H:%M}" < fim):
        return

    def pode(chave: str) -> bool:
        ult = h.get(chave)
        return not ult or agora - datetime.fromisoformat(ult) >= timedelta(hours=config.VIGIA_REPETIR_H)

    # válidas = ainda não postadas e dentro da validade
    na_fila = {c: sum(1 for f in h.get("fila", []) if f.get("canal") == c
                      and not (f.get("valida_ate") and f["valida_ate"] < agora.isoformat())
                      and not ja_postado_recente(h, f["id"], agora, f.get("nome", "")))
               for c in config.CANAIS}
    vazios = [c for c, n in na_fila.items() if n == 0]
    # 03/11 18h59 alarme falso: a rotina não garimpa (nem faz commit) com a fila cheia. Commit velho só é
    # problema se algum canal tiver menos de VIGIA_FILA_MIN ofertas válidas.
    poucos = [c for c, n in na_fila.items() if n < config.VIGIA_FILA_MIN]
    velho = (ult_garimpo is None or agora - ult_garimpo > timedelta(hours=config.VIGIA_GARIMPO_H)) and bool(poucos)
    print(f"[vigia] último garimpo {ult_garimpo:%d/%m %H:%M}" if ult_garimpo else "[vigia] último garimpo: não achei",
          f"| fila válida {na_fila}")
    if (velho or vazios) and pode("vigia_aviso_garimpo"):
        desde = "?" if not ult_garimpo else (f"{ult_garimpo:%H:%M}" if ult_garimpo.date() == agora.date()
                                             else f"{ult_garimpo:%d/%m %H:%M}")
        topo = (f"⚠️ Garimpo parado desde {desde}" if velho else f"⚠️ Fila vazia ({', '.join(vazios)}), último garimpo {desde}")
        detalhe = ("\nPouca oferta na fila: " + ", ".join(f"{c} {na_fila[c]}" for c in poucos) + ".") if velho else ""
        telegram.avisar_dono(f"{topo} — abrir o app Claude e conferir as rotinas{detalhe}", prefixo=False)
        h["vigia_aviso_garimpo"] = agora.isoformat()
    sem_post = {c: m for c in config.CANAIS if (m := minutos_parado(h, c, agora)) > config.VIGIA_POST_H * 60}
    if sem_post and pode("vigia_aviso_post"):
        lista = ", ".join(f"{c} {m / 60:.0f} h" for c, m in sem_post.items())
        telegram.avisar_dono(f"⚠️ Canal sem post: {lista} — abrir o app Claude e conferir as rotinas", prefixo=False)
        h["vigia_aviso_post"] = agora.isoformat()


def ate_proxima_execucao(agora: datetime) -> datetime:
    """A fila corre até FILA_JANELA_MIN depois do início da execução (nunca depois das 22h).
    05/11: antes parava 3 min antes do próximo horário do robo.yml. Mas o cron do GitHub falha e quem dispara
    é o guardião, ~10 min depois do horário; com Instagram + garimpo (~15 min) sobravam ~15 min de fila =
    ~3 posts e buraco de 30 min. Agora corre até perto do timeout do job; a execução seguinte espera na
    fila do concurrency e começa logo depois, então os posts saem contínuos."""
    fim = agora.replace(hour=config.JANELA_FIM[0], minute=config.JANELA_FIM[1], second=0, microsecond=0)
    return min(fim, agora + timedelta(minutes=config.FILA_JANELA_MIN))


def soltar_fila(h: dict, telegram, limite: datetime, atraso: bool = True) -> int:
    """Posta uma oferta por vez, alternando os canais de nicho (cada uma também vai para o
    canal geral), com intervalo sorteado. O que sobrar fica na fila para a próxima execução."""
    import os
    import random
    import time as _time
    erros = 0
    vez = 0
    if atraso and h.get("fila") and not os.environ.get("PAPA_SEM_ATRASO"):
        # 1º post não sai no minuto exato da execução (dono, 28/10: horários aleatórios)
        _time.sleep(random.uniform(*config.ATRASO_INICIAL_MIN) * 60)
    while h.get("fila"):
        agora = datetime.now(FUSO)
        # 01/11 (Telegram): item com "nao_antes" fica na fila sem sair até esse horário
        pode = [f for f in h["fila"] if not f.get("nao_antes") or f["nao_antes"] <= agora.isoformat()]
        if not pode:
            print("fila: só itens com nao_antes no futuro, esperam")
            break
        canais = [c for c in config.CANAIS if any(f["canal"] == c for f in pode)]
        # 01/11: canal parado há mais de CANAL_PARADO_MIN passa na frente (o mais parado primeiro)
        parados = sorted((c for c in canais if minutos_parado(h, c, agora) >= config.CANAL_PARADO_MIN),
                         key=lambda c: -minutos_parado(h, c, agora))
        canal = parados[0] if parados else canais[vez % len(canais)]
        vez += 1
        # 30/10: execução atrasada do GitHub postou às 3h12. Fora da janela (8h–22h) não posta; a fila espera.
        ini = agora.replace(hour=config.JANELA_INICIO[0], minute=config.JANELA_INICIO[1], second=0, microsecond=0)
        fim = agora.replace(hour=config.JANELA_FIM[0], minute=config.JANELA_FIM[1], second=0, microsecond=0)
        if not (ini <= agora <= fim):
            print("fora da janela 8h–22h: fila guardada para depois")
            break
        # DOMINGO DO PERFUME (10h–13h): no canal, o perfume do bloco (nao_antes) e depois qualquer perfume
        # passam na frente; os outros nichos seguem no ritmo normal
        do_canal = [f for f in pode if f["canal"] == canal]
        if em_bloco_perfume(agora):
            do_canal.sort(key=lambda f: (not f.get("nao_antes"), not qualidade.eh_perfume(f)))
        oferta = do_canal[0]
        h["fila"].remove(oferta)
        if ja_postado_recente(h, oferta["id"], agora, oferta.get("nome", "")):
            continue
        hoje = agora.date().isoformat()
        chave = f"{hoje} {canal} {agora:%H:%M} {oferta['id']}"
        try:
            foto, leg = post.foto_com_selo(oferta["imagem"]), post.legenda(oferta, canal)
            telegram.postar_foto(config.CANAIS[canal], foto, leg)
            try:   # cópia no canal geral; se falhar, não atrapalha o canal do nicho
                telegram.postar_foto(config.GERAL, foto, leg)
            except Exception as e:
                telegram.avisar_dono(f"canal geral não recebeu {oferta['id']}: {e}")
            h["postados"][oferta["id"]] = agora.isoformat()
            h.setdefault("postados_nome", {})[chave_nome(oferta["nome"])] = agora.isoformat()
            registro = {**oferta, "canal": canal, "dia": hoje}
            if "so_telegram_ate" in oferta:
                # 05/11 (CEO): oferta forte do dia sai primeiro só no Telegram; o Instagram só pode usar 2 h depois
                # do post (ou depois da hora marcada, se for mais tarde)
                registro["so_telegram_ate"] = max(str(oferta.get("so_telegram_ate") or ""),
                                                  (agora + timedelta(hours=2)).isoformat())
            h.setdefault("ofertas_dia", []).append(registro)
            h["slots_feitos"].append(chave)
            salvar_hist(h)   # grava a cada post: se o job cair, não repete
            print(f"postado {chave}: {oferta['nome'][:60]}")
        except telegram.DestinoProibido as e:
            telegram.avisar_dono(f"BLOQUEADO destino errado: {e}")
            return erros + 1
        except Exception as e:
            telegram.avisar_dono(f"erro em {chave}: {e}. Não postei.")
            erros += 1
            if erros >= 3:
                return erros
        espera = random.uniform(*config.intervalo_posts(datetime.now(FUSO).hour)) * 60
        if not h["fila"] or datetime.now(FUSO) + timedelta(seconds=espera) > limite:
            break
        _time.sleep(espera)
        # 05/11: a execução agora dura ~45 min; horário do Instagram que vence no meio da fila sai na hora,
        # em vez de esperar a próxima execução (que podia passar da janela de 50 min e perder o horário)
        agora_ig = datetime.now(FUSO)
        if instagram_vencido(h, agora_ig):
            try:
                # aqui a própria fila cuida do ritmo: sem post extra entre as peças
                gancho, ENTRE_TAREFAS[0] = ENTRE_TAREFAS[0], (lambda: None)
                try:
                    rodar_instagram(h, agora_ig)
                finally:
                    ENTRE_TAREFAS[0] = gancho
            except Exception as e:
                telegram.avisar_dono(f"Instagram: erro geral {e}")
    print(f"fila: {len(h.get('fila', []))} oferta(s) esperando a próxima execução")
    return erros


# 04/11 (Central): TODO Reel (de ofertas ou do banco de dicas) sai com a chamada para seguir na legenda
SIGA_REEL = "\n\n👉 Siga @papa.garimpou pra não perder"
# 05/11 (CEO): seguidor do Instagram não vira membro do Telegram. Fecho único: comentar TELEGRAM → convite no direct
# (link "ig-dm"). Sem hashtag; o aviso de publicidade fica em texto.
LEGENDA_CTA = ("\n\nQuer as ofertas antes de todo mundo? Comenta TELEGRAM que o Papa te manda o convite no direct 💎\n\n"
               "Publi · link de afiliado")


def reels_do_banco(h: dict, agora: datetime) -> tuple[list[bytes], str]:
    """Reels sem oferta: capa + 3 peças de pilares diferentes do banco + convite."""
    import artes
    pcs = conteudo.escolher(h, agora.date(), n=3)
    quadros = [artes.capa_reel(("O PAPA", "ENSINA"), "3 coisas antes de comprar")] + [artes.peca(p) for p in pcs]
    quadros.append(artes.story_convite())
    leg = "😎💎 " + " / ".join(p["titulo"][0].title() for p in pcs) + "\n\n" + pcs[0]["legenda"].replace("😎💎 ", "")
    return quadros, leg + SIGA_REEL + LEGENDA_CTA


def post_do_banco(h: dict, agora: datetime, chave: str) -> None:
    """Post de feed com peça do banco de conteúdo (até 2 por dia quando não há ofertas)."""
    import artes
    import instagram
    hoje = agora.date().isoformat()
    cont = h.setdefault("feed_dia", {})
    if cont.get(hoje, 0) >= 2:
        return
    for pc in conteudo.escolher(h, agora.date(), para_story=False):
        instagram.foto(artes.peca(pc, story=False), f"{agora:%Y%m%d}-feed-{pc['id']}.jpg", pc["legenda"] + LEGENDA_CTA)
        h["feed_dia"] = {hoje: cont.get(hoje, 0) + 1}
        h.setdefault("ig_feitos", []).append(f"{hoje} feed")
        print(f"[ig] publicado {chave} (post do banco {pc['id']})")


INTERATIVOS = PASTA / "dados" / "interativos-hoje.json"


def registrar_interativo(agora: datetime, tipo: str, ofertas: list[dict]) -> None:
    """dados/interativos-hoje.json: o que saiu em cada story interativo do dia (a sessão Instagram
    usa para responder os directs com produto, preço e link)."""
    hoje = agora.date().isoformat()
    reg = json.loads(INTERATIVOS.read_text(encoding="utf-8")) if INTERATIVOS.exists() else {}
    if reg.get("dia") != hoje:
        reg = {"dia": hoje, "itens": []}
    reg["itens"].append({"tipo": tipo, "hora": f"{agora:%H:%M}", "produtos": [
        {k: o.get(k) for k in ("nome", "preco_antigo", "preco", "desconto", "link", "loja", "canal")} for o in ofertas]})
    INTERATIVOS.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


def publicar_interativo(tipo: str, h: dict, agora: datetime, tag: str, ofertas: list[dict], usadas: list) -> bool:
    """01/11 (Central): stories "responde no direct" (a Business Suite não tem enquete/pergunta).
    Devolve False quando não há oferta que sirva; aí o horário vira story de oferta comum."""
    import artes
    import instagram
    hoje = agora.date().isoformat()
    if tipo == "adivinha":
        boas = [o for o in ofertas if o.get("imagem") and o.get("preco_antigo") and (o.get("desconto") or 0) >= 20]
        if not boas:
            return False
        o = max(boas, key=lambda o: o["desconto"])
        instagram.story(artes.story_adivinha(o), f"{tag}-adivinha-{o['id']}.jpg")
        h["adivinha"] = {"dia": hoje, "oferta": o}
    elif tipo == "adivinha_resposta":
        o = (h.get("adivinha") or {}).get("oferta")
        if not o or h["adivinha"].get("dia") != hoje:
            return False
        instagram.story(artes.story_oferta(o, o["canal"], selo="RESPOSTA DO ADIVINHA"), f"{tag}-resposta-{o['id']}.jpg")
    elif tipo == "a_ou_b":
        por_canal = {}
        for o in ofertas:
            if o.get("imagem"):
                por_canal.setdefault(o["canal"], []).append(o)
        pares = [sorted(v, key=qualidade.pontuar, reverse=True)[:2] for v in por_canal.values() if len(v) >= 2]
        if not pares:
            return False
        o = max(pares, key=lambda p: sum(qualidade.pontuar(x) for x in p))
        instagram.story(artes.story_a_ou_b(*o), f"{tag}-aoub-{o[0]['id']}.jpg")
        o = list(o)
    else:
        return False
    escolhidas = o if isinstance(o, list) else [o]
    for x in escolhidas:
        if x in ofertas:
            ofertas.remove(x)
            usadas.append(x["id"])
    registrar_interativo(agora, tipo, escolhidas)
    return True


def publicar_salvavel(h: dict, agora: datetime, tag: str) -> bool:
    """Carrossel semanal "salvável": 5 melhores <categoria> de marca até R$ X (ofertas reais dos últimos
    7 dias + fila manual), girando a categoria. Quem comenta QUERO recebe os 5 links no direct."""
    import artes
    import instagram
    semana = (agora - timedelta(days=7)).date().isoformat()
    pool = [o for o in h.get("ofertas_dia", []) if o.get("dia", "") >= semana and liberada_ig(o, agora)] \
        + [o for o in carregar_manuais(h, agora) if "so_telegram_ate" not in o]
    n = len(config.SALVAVEIS)
    for k in range(n):
        cat, palavras, teto = config.SALVAVEIS[(agora.isocalendar()[1] + k) % n]
        vistos, top = set(), []
        for o in sorted(pool, key=lambda o: o.get("desconto") or 0, reverse=True):
            nome = (o.get("nome") or "").lower()
            if o.get("imagem") and o.get("link") and o["preco"] <= teto and any(p in nome for p in palavras) \
                    and chave_nome(o["nome"]) not in vistos:
                vistos.add(chave_nome(o["nome"]))
                top.append(o)
        if len(top) < 5:
            continue
        top = top[:5]
        lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}" for i, o in enumerate(top))
        leg = (f"😎💎 Os 5 melhores {cat} de marca até R$ {teto}\n\n{lista}\n\nSalva esse post pra não perder.\n"
               "Comenta QUERO que eu mando os links 💎\n\nPubli · link de afiliado")
        slides = [artes.capa_salvavel(cat, teto)] + [artes.post_oferta(o, o["canal"]) for o in top]
        mid = instagram.carrossel(slides, f"{tag}-salvavel", leg)
        dm = f"Oi! Aqui é o Papa 😎💎\n\nOs 5 melhores {cat} até R$ {teto}:\n\n" + "\n\n".join(
            f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}\n{o['link']}" for i, o in enumerate(top))
        h.setdefault("ig_dm_links", {})[mid] = dm + "\n\nPreço pode mudar a qualquer momento. Publi · link de afiliado"
        registrar_interativo(agora, "carrossel_salvavel", top)
        return True
    return False


SELO_PRIMEIRO = "SAIU PRIMEIRO NO TELEGRAM"


def liberada_ig(o: dict, agora: datetime) -> bool:
    """05/11 (CEO): oferta com "so_telegram_ate" só vai ao Instagram depois dessa hora."""
    return not o.get("so_telegram_ate") or str(o["so_telegram_ate"]) <= agora.isoformat()


ENTRE_TAREFAS = [lambda: None]   # main põe aqui o "solta 1 post se já deu o intervalo"


def instagram_vencido(h: dict, agora: datetime) -> bool:
    """Algum horário da agenda do Instagram já venceu (até 50 min) e ainda não saiu hoje?"""
    import os
    if not os.environ.get("META_TOKEN"):
        return False
    feitos = set(h.get("ig_feitos", []))
    for hora, tipo in config.INSTAGRAM_AGENDA:
        hh, mm = map(int, hora.split(":"))
        momento = agora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if momento <= agora <= momento + timedelta(minutes=50) and f"{agora.date().isoformat()} {hora} {tipo}" not in feitos:
            return True
    return False


def rodar_instagram(h: dict, agora: datetime) -> None:
    """Executa as tarefas do Instagram que venceram e responde comentários."""
    import os
    if not os.environ.get("META_TOKEN"):
        return
    import artes
    import instagram
    import telegram
    hoje = agora.date().isoformat()
    tag = agora.strftime("%Y%m%d")
    feitos = h.setdefault("ig_feitos", [])
    usadas = h.setdefault("ig_ofertas_usadas", [])
    ofertas = [o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o["id"] not in usadas
               and liberada_ig(o, agora)]
    # a que saiu primeiro no Telegram, quando libera, é a próxima do Instagram (com o selo)
    ofertas.sort(key=lambda o: "so_telegram_ate" not in o)
    # Carrossel especial escolhido à mão (ex.: post para impulsionar): sai uma vez, na primeira execução
    esp_arq = Path(__file__).parent / "instagram_especial.json"
    if esp_arq.exists():
        esp = json.loads(esp_arq.read_text(encoding="utf-8"))
        if f"especial {esp['id']}" not in feitos:
            try:
                por_id = {o["id"]: o for o in h.get("ofertas_dia", [])}
                por_id.update({o["id"]: o for o in json.loads(MANUAIS.read_text(encoding="utf-8"))})
                top = [por_id[i] for i in esp["ids"] if i in por_id]
                slides = [artes.capa_top5(agora.timetuple().tm_yday)] + [artes.post_oferta(o, o["canal"]) for o in top]
                # "colaboradores" (opcional): post Collab, ex. ["achadinhosdos.universo"]
                instagram.carrossel(slides, f"{tag}-{esp['id']}", esp["legenda"], esp.get("colaboradores"))
                print(f"[ig] carrossel especial {esp['id']} publicado")
            except Exception as e:
                telegram.avisar_dono(f"Instagram: carrossel especial {esp['id']} falhou: {e}")
            feitos.append(f"especial {esp['id']}")
    # Parcerias de divulgação (troca de story com outro perfil): cada uma sai uma vez, no story e no Telegram
    parc_arq = Path(__file__).parent / "parcerias.json"
    if parc_arq.exists():
        for p in json.loads(parc_arq.read_text(encoding="utf-8")):
            if f"parceria {p['id']}" in feitos:
                continue
            try:
                arte = artes.story_parceria(p["arroba"], p["assuntos"])
                instagram.story(arte, f"{tag}-parceria-{p['id']}.jpg")
                telegram.postar_foto(config.CANAIS["achadinhos"], arte, p["telegram"])
                print(f"[ig] parceria {p['id']} publicada")
            except Exception as e:
                telegram.avisar_dono(f"Instagram: parceria {p['id']} falhou: {e}")
            feitos.append(f"parceria {p['id']}")
    # Stories de ocasião (ex.: agradecer 100 seguidores): cada um sai uma vez, a partir de "desde".
    # Com "diario" (ex.: PEDE PRO PAPA), sai 1x por dia entre "hora_ini" e "hora_fim", girando "paletas".
    esp_st = Path(__file__).parent / "stories_especiais.json"
    if esp_st.exists():
        for e in json.loads(esp_st.read_text(encoding="utf-8")):
            chave_e = f"story especial {e['id']}" + (f" {hoje}" if e.get("diario") else "")
            if chave_e in feitos or agora.isoformat() < e.get("desde", ""):
                continue
            if e.get("diario") and not (e.get("hora_ini", "00:00") <= f"{agora:%H:%M}" <= e.get("hora_fim", "23:59")):
                continue
            if "dias_semana" in e and agora.weekday() not in e["dias_semana"]:   # 0 = segunda … 6 = domingo
                continue
            paletas = e.get("paletas") or [e.get("paleta", 0)]
            try:
                arte = artes.story_especial(e["titulo"], e["linhas"], paletas[agora.toordinal() % len(paletas)],
                                            e.get("botao", "LINK NA BIO"))
                instagram.story(arte, f"{tag}-especial-{e['id']}.jpg")
                print(f"[ig] story especial {e['id']} publicado")
            except Exception as ex:
                telegram.avisar_dono(f"Instagram: story especial {e['id']} falhou: {ex}")
            feitos.append(chave_e)
    # PEDIDO ATENDIDO (01/11): a sessão Instagram grava em pedidos_atendidos.json o produto que um seguidor
    # pediu no direct; sai 1 story com o selo (sem nome de quem pediu) e a oferta entra na fila do canal.
    for o in carregar_pedidos(agora):
        if f"pedido {o['id']}" in feitos:
            continue
        try:
            # 05/11: "proc-" = procura da semana (ninguém pediu no direct): selo próprio, nunca "PEDIDO ATENDIDO"
            selo = "PROCURA DA SEMANA" if o["id"].startswith("proc-") else "PEDIDO ATENDIDO"
            instagram.story(artes.story_oferta(o, o["canal"], selo=selo), f"{tag}-pedido-{o['id']}.jpg")
            print(f"[ig] pedido atendido {o['id']} publicado")
        except Exception as ex:
            telegram.avisar_dono(f"Instagram: pedido atendido {o['id']} falhou: {ex}")
        feitos.append(f"pedido {o['id']}")
    for hora, tipo in config.INSTAGRAM_AGENDA:
        chave = f"{hoje} {hora} {tipo}"
        hh, mm = map(int, hora.split(":"))
        momento = agora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if chave in feitos or not (momento <= agora <= momento + timedelta(minutes=50)):
            continue
        ENTRE_TAREFAS[0]()   # 05/11: solta 1 post do Telegram entre as peças do Instagram, se já deu o intervalo
        try:
            if tipo in ("adivinha", "adivinha_resposta", "a_ou_b"):
                if publicar_interativo(tipo, h, agora, tag, ofertas, usadas):
                    feitos.append(chave)
                    print(f"[ig] publicado {chave}")
                    continue
                tipo = "story_oferta"   # sem oferta que sirva: story de oferta comum no lugar
            # 01/11 (Central): sábado, o post das 19h15 vira o carrossel Top 5 da semana (chama para o Top 10)
            if tipo == "post_achado" and hora == "19:15" and agora.weekday() == config.TOP10_DIA_SEMANA:
                top = ranking_semana(h, agora, 5)
                if len(top) >= 3:
                    slides = [artes.capa_semana(len(top))] + [artes.post_oferta(o, o["canal"]) for o in top]
                    lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])} ({o['desconto']}% OFF)"
                                      for i, o in enumerate(top))
                    instagram.carrossel(slides, f"{tag}-top5-semana", "😎💎 Top 5 da semana do Papa\n\n" + lista
                                        + "\n\nHoje 20h30 tem o TOP 10 completo no Telegram (link na bio)." + LEGENDA_CTA)
                    feitos += [f"{hoje} feed", chave]
                    print(f"[ig] publicado {chave} (top 5 da semana)")
                    continue
            if tipo == "post_achado" and hora == "19:15" and agora.weekday() == config.SALVAVEL_DIA_SEMANA \
                    and publicar_salvavel(h, agora, tag):
                feitos += [f"{hoje} feed", chave]
                print(f"[ig] publicado {chave} (carrossel salvável)")
                continue
            if tipo == "story_convite":
                # 30/10 (dono aprovou): lista de espera da Black Friday — de 01/11 até 27/11 o convite da tarde
                # vira contagem regressiva para entrar no canal antes do dia
                bf = (datetime(2026, 11, 27, tzinfo=agora.tzinfo).date() - agora.date()).days
                if 0 <= bf <= 27 and hh < 18:
                    instagram.story(artes.story_blackfriday(bf), f"{tag}-blackfriday-{hh}.jpg")
                else:
                    instagram.story(artes.story_convite(), f"{tag}-convite-{hh}.jpg")
            elif tipo == "story_top4" and len([o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje
                                               and liberada_ig(o, agora)]) >= 4:
                # 4 melhores achados do dia num story só (maior desconto primeiro); preço sempre o real
                top = sorted((o for o in h["ofertas_dia"] if o.get("dia") == hoje),
                             key=lambda o: (o.get("desconto") or 0, qualidade.pontuar(o)), reverse=True)[:4]
                instagram.story(artes.story_top4(top), f"{tag}-top4-{hh}.jpg")
            elif tipo in ("story_oferta", "story_top4"):
                if not ofertas:
                    # sem oferta: peça do banco de conteúdo (tema diferente, sem repetir), até 3 por dia
                    cont = h.setdefault("pecas_dia", {})
                    if cont.get(hoje, 0) >= conteudo.PECAS_STORY_DIA:
                        feitos.append(chave)
                        continue
                    h["pecas_dia"] = {hoje: cont.get(hoje, 0) + 1}
                    for pc in conteudo.escolher(h, agora.date()):
                        instagram.story(artes.peca(pc), f"{tag}-{pc['id']}.jpg")
                else:
                    o = ofertas.pop(0)
                    instagram.story(artes.story_oferta(o, o["canal"], selo=SELO_PRIMEIRO if "so_telegram_ate" in o else ""),
                                    f"{tag}-story-{o['id']}.jpg")
                    usadas.append(o["id"])
            elif tipo == "post_achado":
                if not ofertas:
                    post_do_banco(h, agora, chave)
                    feitos.append(chave)
                    continue
                o = max(ofertas, key=qualidade.pontuar)
                ofertas.remove(o)
                leg = f"😎💎 Achado do dia: {o['nome']}\n\nDe {post._brl(o['preco_antigo'])} por {post._brl(o['preco'])} ({o['desconto']}% OFF)" if o.get("preco_antigo") else f"😎💎 Achado do dia: {o['nome']} por {post._brl(o['preco'])}"
                if "so_telegram_ate" in o:
                    leg = "⚡ Saiu primeiro no Telegram.\n\n" + leg
                instagram.foto(artes.post_oferta(o, o["canal"]), f"{tag}-post-{o['id']}.jpg", leg + LEGENDA_CTA)
                usadas.append(o["id"])
            elif tipo == "reels":
                import video
                # 30/10: até 3 Reels/dia; cada um usa ofertas que ainda não saíram em Reels hoje
                ja = set(h.setdefault("ig_reels_ofertas", {}).get(hoje, []))
                top = sorted((o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o["id"] not in ja
                              and liberada_ig(o, agora)),
                             key=qualidade.pontuar, reverse=True)[:5]
                if len(top) >= 3:
                    # 04/11 (Instagram atrasado na meta): a capa genérica "ACHADOS DO PAPA" não prende quem
                    # rola o feed. Capa com o maior desconto REAL do lote (vem da loja) e chamada para seguir.
                    maior = max(int(o.get("desconto") or 0) for o in top)
                    if maior >= 20:
                        capa = artes.capa_reel((f"ATÉ {maior}% OFF", "EM MARCA BOA"),
                                               f"{len(top)} achados de hoje · segue o Papa")
                        topo = f"😎💎 Até {maior}% OFF em marca boa: os {len(top)} achados do Papa hoje"
                    else:
                        capa = artes.capa_reel(("ACHADOS", "DO PAPA"), "Os melhores de hoje")
                        topo = "😎💎 Os achados do Papa hoje"
                    quadros = ([capa] + [artes.story_oferta(o, o["canal"]) for o in top] + [artes.story_convite()])
                    lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}" for i, o in enumerate(top))
                    leg = (topo + "\n\n" + lista
                           + SIGA_REEL + LEGENDA_CTA)
                    h["ig_reels_ofertas"][hoje] = list(ja | {o["id"] for o in top})
                else:
                    # sem oferta nova suficiente: Reels de dica do banco (alcance não pode parar)
                    quadros, leg = reels_do_banco(h, agora)
                instagram.reels(video.reel(quadros), leg)
                h["ig_ultimo_reel"] = agora.isoformat()
            elif tipo == "carrossel_top5":
                top = sorted(h.get("ofertas_dia", []), key=qualidade.pontuar, reverse=True)
                top = [o for o in top if o.get("dia") == hoje and liberada_ig(o, agora)][:5]
                if len(top) < 3:
                    post_do_banco(h, agora, chave)   # sem ofertas: post do banco no lugar do carrossel
                    feitos.append(chave)
                    continue
                slides = [artes.capa_top5(agora.timetuple().tm_yday)] + [artes.post_oferta(o, o["canal"]) for o in top]
                lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}" for i, o in enumerate(top))
                instagram.carrossel(slides, f"{tag}-top5", "😎💎 TOP 5 do Papa hoje\n\n" + lista + LEGENDA_CTA)
            if tipo in ("post_achado", "carrossel_top5", "reels"):
                feitos.append(f"{hoje} feed")
            feitos.append(chave)
            print(f"[ig] publicado {chave}")
        except instagram.ContaErrada as e:
            telegram.avisar_dono(f"INSTAGRAM BLOQUEADO (conta errada): {e}")
            return
        except Exception as e:
            telegram.avisar_dono(f"Instagram {chave} falhou: {e}. Não publiquei.")
            feitos.append(chave)
    # Vigia: sempre pelo menos 3 stories no ar
    try:
        ativos = instagram.stories_ativos()
        faltam = max(0, config.STORIES_MINIMOS - ativos)
        for k in range(min(faltam, 3)):
            pcs = conteudo.escolher(h, agora.date())
            img = artes.peca(pcs[0]) if pcs else artes.story_convite()
            instagram.story(img, f"{tag}-vigia-{agora:%H%M}-{k}.jpg")
        if faltam:
            print(f"[ig] vigia: havia {ativos} stories no ar, publiquei {min(faltam, 3)}")
    except Exception as e:
        print(f"[ig] vigia de stories: {e}")
    try:
        resp = instagram.responder_comentarios(set(h.setdefault("ig_comentarios", [])), h.get("ig_dm_links"))
        h["ig_comentarios"] += resp
        if resp:
            print(f"[ig] respondi {len(resp)} comentário(s)")
    except Exception as e:
        print(f"[ig] comentários: {e}")
    instagram.limpar_midia(hoje)
    h["ig_feitos"] = [f for f in feitos if f[:10] >= (agora.date() - timedelta(days=3)).isoformat()]
    h["ig_ofertas_usadas"] = usadas[-200:]


CONVITE_STORY = PASTA / "dados" / "convite-story.txt"
CONVITES = PASTA / "dados" / "convites.json"
CONVITES_ORIGEM = ("ig-bio", "ig-story", "ig-dm")


STORY_LINK = PASTA / "dados" / "story-link.txt"


def preparar_story_link(h: dict, agora: datetime) -> None:
    """01/11 (Central): 1 arte por dia para o story com adesivo de link, que a sessão Instagram publica
    à mão entre 20h30 e 22h. Sai na 1ª execução depois das 17h: oferta real mais forte do dia
    (maior % OFF com "de" da loja, mínimo 20%) ou a peça "por que seguir o Papa".
    Grava "URL | AAAA-MM-DD" em dados/story-link.txt."""
    import os
    hoje = agora.date().isoformat()
    if not config.STORY_LINK_ATIVO or agora.hour < 17 or h.get("story_link_dia") == hoje \
            or not os.environ.get("META_TOKEN"):
        return
    import artes
    import instagram
    fortes = [o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o.get("preco_antigo") and liberada_ig(o, agora)
              and (o.get("desconto") or 0) >= 20 and o.get("imagem")]
    # sábado: o story com link chama para o TOP 10 da semana (sessão Instagram, 01/11)
    arte = artes.story_link(None, top10=True) if agora.weekday() == config.TOP10_DIA_SEMANA else None
    for o in ([] if arte else sorted(fortes, key=lambda o: o["desconto"], reverse=True)[:3]):
        try:
            arte = artes.story_link(o)
            break
        except Exception as e:   # foto que não baixa: tenta a próxima
            print(f"[story-link] {o['id']}: {e}")
    try:
        url = instagram.hospedar(f"{agora:%Y%m%d}-story-link.jpg", arte or artes.story_link(None))
        try:   # 3ª coluna: cópia no fbcdn, que a Business Suite deixa baixar (raw.githubusercontent não)
            fb = " | " + instagram.foto_fbcdn(url)
        except Exception as e:
            fb = ""
            print(f"[story-link] fbcdn falhou: {e}")
        STORY_LINK.write_text(f"{url} | {hoje}{fb}\n", encoding="utf-8")
        h["story_link_dia"] = hoje
        print(f"[story-link] {url}")
    except Exception as e:
        print(f"[story-link] falhou: {e}")


def convites_story(h: dict, telegram, agora: datetime) -> None:
    """01/11 (Central: medir membros por story): 1 link de convite por dia para o canal geral,
    nome "story-AAAAMMDD", gravado em dados/convite-story.txt para a sessão Instagram usar,
    e contagem de quem entrou por cada link (chat_member do getUpdates)."""
    conv = h.setdefault("convites_story", {})
    # 05/11 (CEO): links fixos por origem do Instagram (bio, story, direct) no canal geral, criados uma vez;
    # ficam em dados/convites.json e o "ig-story" vai para convite-story.txt (substitui o link diário).
    nome = "ig-story"
    for n in CONVITES_ORIGEM:
        if n not in conv:
            try:
                conv[n] = {"link": telegram.criar_convite(config.GERAL, n), "entradas": []}
            except Exception as e:
                if h.get("convite_erro") != agora.date().isoformat():
                    h["convite_erro"] = agora.date().isoformat()
                    telegram.avisar_dono(f"não consegui criar o convite {n} em {config.GERAL}: {e} "
                                         "(o robô precisa da permissão 'Convidar usuários' no canal)")
    if all(n in conv for n in CONVITES_ORIGEM):
        CONVITES.write_text(json.dumps({n: conv[n]["link"] for n in CONVITES_ORIGEM}, ensure_ascii=False, indent=1),
                            encoding="utf-8")
        CONVITE_STORY.write_text(f"{nome} {conv[nome]['link']}\n", encoding="utf-8")
    try:
        novas, h["tg_offset"] = telegram.entradas_por_convite(h.get("tg_offset"))
    except Exception as e:
        print(f"[convites] {e}")
        return
    import hashlib
    for canal, link, uid in novas:
        # o histórico fica no repositório público: só um hash curto do id, para não contar a mesma pessoa 2x
        chave = hashlib.sha256(f"papa{uid}".encode()).hexdigest()[:10]
        if canal == config.GERAL and link in conv and chave not in conv[link]["entradas"]:
            conv[link]["entradas"].append(chave)
    for velho in sorted(n for n in conv if n not in CONVITES_ORIGEM)[:-30]:
        conv.pop(velho)
    print(f"[convites] {nome}: {len(conv.get(nome, {}).get('entradas', []))} entrada(s) hoje")


RESUMO_DONO = Path(__file__).parent / "dados" / "resumo_dono.json"


def enviar_resumo_dono(h: dict, telegram, agora: datetime) -> None:
    """04/11 (dono quer receber TODO DIA o que foi feito): a rotina resultado-diário (22h07–22h20) grava
    dados/resumo_dono.json = {"dia", "texto"}; a execução seguinte manda ao chat do dono uma única vez
    (h["resumo_enviado"]). Vale o resumo de hoje ou de ontem (depois da meia-noite). Fora da janela de posts, de propósito."""
    if not RESUMO_DONO.exists():
        return
    try:
        r = json.loads(RESUMO_DONO.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[resumo] resumo_dono.json inválido: {e}")
        return
    dia, texto = r.get("dia", ""), (r.get("texto") or "").strip()
    ontem = (agora.date() - timedelta(days=1)).isoformat()
    if not texto or dia not in (agora.date().isoformat(), ontem) or h.get("resumo_enviado", "") >= dia:
        return
    if telegram.mensagem_dono(texto):
        h["resumo_enviado"] = dia
        salvar_hist(h)
        print(f"[resumo] resumo de {dia} enviado ao dono")


def checar_vendas_shopee(h: dict, telegram, agora: datetime) -> None:
    """01/11 (dono pediu aviso de venda): olha as conversões dos últimos 3 dias e avisa cada venda
    nova uma vez só no chat de alertas. Erro aqui nunca para a postagem; avisa no máximo 1x por dia."""
    import shopee
    vistas = h.setdefault("vendas_shopee", {})
    try:
        novas = [v for v in shopee.vendas(int(agora.timestamp()) - 3 * 86400) if v["id"] not in vistas]
    except Exception as e:
        dia = agora.date().isoformat()
        if h.get("vendas_shopee_erro") != dia:
            h["vendas_shopee_erro"] = dia
            telegram.avisar_dono(f"não consegui ler as vendas da Shopee hoje: {str(e)[:200]}")
        print(f"[vendas] {e}")
        return
    for v in novas:
        vistas[v["id"]] = agora.isoformat()
        itens = ", ".join(i[:50] for i in v["itens"][:3]) or "produto não informado"
        telegram.avisar_venda(f"💰 VENDA NA SHOPEE! Comissão R$ {v['comissao']:.2f}\n🛒 {itens}")
    print(f"[vendas] Shopee: {len(novas)} venda(s) nova(s)")


def ofertas_exemplo(termo: str) -> list[dict]:
    exemplo = json.loads((PASTA / "dados" / "exemplo_ofertas.json").read_text(encoding="utf-8"))
    return exemplo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensaio", action="store_true")
    ap.add_argument("--agenda", action="store_true")
    ap.add_argument("--testar-shopee", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--story-teste", action="store_true")
    ap.add_argument("--reels-teste", action="store_true")
    ap.add_argument("--mosaico", action="store_true")
    ap.add_argument("--destaques", action="store_true")
    ap.add_argument("--vigia-teste", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    agora = datetime.now(FUSO)
    if args.agenda:
        # Telegram não tem agenda (posta na hora que acha); só o Instagram tem horários fixos.
        for hora, tipo in config.INSTAGRAM_AGENDA:
            print("instagram", hora, tipo)
        return 0

    if args.vigia_teste:
        # Disparo manual (03/11): manda ao dono o aviso do vigia com os dados reais, marcado como teste.
        import telegram
        ult = ultimo_garimpo()
        h = carregar_hist()
        na_fila = {c: sum(1 for f in h.get("fila", []) if f.get("canal") == c) for c in config.CANAIS}
        desde = f"{ult:%d/%m %H:%M}" if ult else "?"
        telegram.avisar_dono(f"🧪 TESTE do vigia (pode ignorar)\n⚠️ Garimpo parado desde {desde} — abrir o app Claude "
                             f"e conferir as rotinas\nFila agora: {na_fila}", prefixo=False)
        return 0

    if args.story_teste:
        # Publica agora o story convite (teste real da cadeia Instagram) e responde comentários.
        import artes
        import instagram
        sid = instagram.story(artes.story_convite(), f"{agora:%Y%m%d}-convite-teste.jpg")
        print("story publicado:", sid)
        return 0

    if args.destaques:
        # 1 story de cada tema (para montar os destaques do perfil), sem repetir peça já usada.
        import artes
        import instagram
        h = carregar_hist()
        usadas = h.setdefault("pecas_usadas", {})
        for pilar in ("anticilada", "dica", "mito", "humor", "bastidor"):
            pc = next(p for p in sorted(conteudo.PECAS, key=lambda p: usadas.get(p["id"], ""))
                      if p["pilar"] == pilar and not p.get("so_feed"))
            usadas[pc["id"]] = agora.date().isoformat()
            print(pilar, instagram.story(artes.peca(pc), f"{agora:%Y%m%d}-destaque-{pc['id']}.jpg"))
            salvar_hist(h)   # grava a cada story: se cair no meio, não repete o que já saiu
        return 0

    if args.mosaico:
        # Painel de 3 posts que formam uma imagem só na grade do perfil (direita primeiro).
        import artes
        import instagram
        partes = artes.mosaico()
        legs = ["😎💎 Telegram grátis: @papagarimpou e @papagarimpoumarcas. Link na bio.",
                "😎💎 Achados de marca com desconto de verdade. Só loja oficial, nada de réplica.",
                "😎💎 Prazer, o Papa. Eu garimpo, você economiza."]
        for i in (2, 1, 0):
            print("mosaico", i, instagram.foto(partes[i], f"{agora:%Y%m%d}-mosaico-{i}.jpg", legs[2 - i] + LEGENDA_CTA))
        return 0

    if args.reels_teste:
        # Publica agora o Reels fixo do Papa (teste real da cadeia de vídeo) e grava no histórico.
        import artes
        import instagram
        import video
        h = carregar_hist()
        quadros, leg = reels_do_banco(h, agora)
        rid = instagram.reels(video.reel(quadros), leg)
        h["ig_ultimo_reel"] = agora.isoformat()
        salvar_hist(h)
        print("reels publicado:", rid)
        return 0

    if args.verificar:
        # Confere o bot sem postar nada: identidade, permissão nos 2 canais e chats privados que deram /start.
        import os
        import requests
        tk = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not tk:
            print("sem TELEGRAM_BOT_TOKEN")
            return 1
        api = f"https://api.telegram.org/bot{tk}"
        eu = requests.get(f"{api}/getMe", timeout=30).json()
        print("bot:", eu.get("ok"), eu.get("result", {}).get("username"))
        bot_id = eu.get("result", {}).get("id")
        for canal, destino in {**config.CANAIS, "geral": config.GERAL}.items():
            m = requests.get(f"{api}/getChatMember", params={"chat_id": destino, "user_id": bot_id}, timeout=30).json()
            r = m.get("result", {})
            print(f"{canal} {destino}: status={r.get('status')} pode_postar={r.get('can_post_messages')} {'' if m.get('ok') else m}")
        up = requests.get(f"{api}/getUpdates", timeout=30).json()
        privados = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
                    for u in up.get("result", []) if u.get("message", {}).get("chat", {}).get("type") == "private"}
        print("chats privados com o bot (para ALERTA_CHAT_ID):", privados or "nenhum — mande /start para o bot")
        alerta = os.environ.get("ALERTA_CHAT_ID", "").strip()
        if alerta:
            r = requests.post(f"{api}/sendMessage", data={"chat_id": alerta, "text":
                              "✅ Robô Papa Garimpou: verificação ok. Se algo der errado, eu te aviso por aqui."}, timeout=30).json()
            print("aviso de teste enviado:", r.get("ok"))
        mt = os.environ.get("META_TOKEN", "")
        if mt:
            g = "https://graph.facebook.com/v21.0"
            me = requests.get(f"{g}/me", params={"access_token": mt}, timeout=30).json()
            print("meta me:", me.get("name"), me.get("id"), me.get("error", {}).get("message", ""))
            contas = requests.get(f"{g}/me/accounts", params={"access_token": mt, "fields": "name,instagram_business_account{id,username}"}, timeout=30).json()
            for p in contas.get("data", []):
                ig = p.get("instagram_business_account") or {}
                print("pagina:", p.get("name"), "| instagram:", ig.get("username"), ig.get("id"))
                if ig.get("id"):
                    lim = requests.get(f"{g}/{ig['id']}/content_publishing_limit", params={"access_token": mt, "fields": "config,quota_usage"}, timeout=30).json()
                    print("limite de publicação:", lim.get("data", lim))
            if contas.get("error"):
                print("erro contas:", contas["error"].get("message"))
        return 0

    if args.testar_shopee:
        import shopee
        for o in shopee.buscar("cueca lupo", 5):
            print(qualidade.avaliar(o, "marcas"), o["nome"][:60], o["preco"], o["desconto"], o["loja_oficial"])
        return 0

    if args.ensaio:
        saida = PASTA / "dados" / "ensaio"
        saida.mkdir(parents=True, exist_ok=True)
        h = {"slots_feitos": [], "postados": {}}
        for canal in config.CANAIS:
            o = garimpar(canal, ofertas_exemplo, h, agora, 0)
            if not o:
                continue
            (saida / f"{canal}.txt").write_text(post.legenda(o, canal), encoding="utf-8")
            try:
                (saida / f"{canal}.jpg").write_bytes(post.foto_com_selo(o["imagem"]))
            except Exception as e:
                print(f"[{canal}] foto não baixou no ensaio: {e}")
            print(f"[{canal}] escolhida: {o['nome']} → {config.CANAIS[canal]} (ensaio, nada postado)")
        return 0

    import os
    import telegram
    import shopee
    h = carregar_hist()
    hoje = agora.date().isoformat()
    # 05/11: Instagram + garimpo levam ~10–15 min antes da fila. Com a fila do run anterior ainda cheia,
    # solta 1 oferta antes e 1 depois do Instagram para não abrir buraco entre uma execução e a seguinte.
    def um_post():
        # 05/11 (run #311): saiu 13h35 colado no 13h34 da execução anterior; respeita o intervalo mínimo
        ult = max((v for v in ultimo_post(h, datetime.now(FUSO)).values() if v), default=None)
        if ult and (datetime.now(FUSO) - datetime.now(FUSO).replace(hour=int(ult[:2]), minute=int(ult[3:]))).total_seconds() \
                < config.intervalo_posts(datetime.now(FUSO).hour)[0] * 60:
            return
        if os.environ.get("TELEGRAM_BOT_TOKEN") and h.get("fila"):
            soltar_fila(h, telegram, datetime.now(FUSO), atraso=False)
    # 05/11 (Central: 1 post a cada 6–8 min o dia todo): também entre as tarefas do Instagram e entre os garimpos
    ENTRE_TAREFAS[0] = um_post
    um_post()
    try:
        rodar_instagram(h, agora)
    except Exception as e:
        telegram.avisar_dono(f"Instagram: erro geral {e}")
    um_post()
    enviar_resumo_dono(h, telegram, agora)
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("TELEGRAM_BOT_TOKEN ausente — nada postado")
        salvar_hist(h)
        gravar_relatorio(h, agora)
        return 0
    # Sem cota diária (dono, 27/10): toda oferta boa entra. Fila contínua (dono, 28/10): em vez de
    # despejar tudo de uma vez, solta uma oferta a cada poucos minutos até perto da próxima execução.
    erros = 0
    publicar_menus(h, telegram)
    pede_pro_papa_semanal(h, telegram, agora)
    # Ofertas garimpadas fora da Shopee (Amazon etc.), conferidas à mão e gravadas em ofertas_manuais.json
    for canal in config.CANAIS:
        entrar_na_fila(h, canal, [o for o in carregar_manuais(h, agora) if o["canal"] == canal], agora)
    shopee_ok = bool(os.environ.get("SHOPEE_APP_ID") and os.environ.get("SHOPEE_SECRET"))
    if not shopee_ok:
        print("chaves da Shopee ainda não configuradas — só ofertas manuais")
    for canal in (config.CANAIS if shopee_ok else []):
        try:
            ofertas = garimpar_todas(canal, shopee.buscar, h, agora)
        except Exception as e:
            telegram.avisar_dono(f"garimpo de {canal} falhou: {e}. A fila que já existe segue saindo.")
            erros += 1
            continue
        entrar_na_fila(h, canal, ofertas, agora)
        um_post()
    convites_story(h, telegram, agora)
    preparar_story_link(h, agora)
    top10_semana(h, telegram, agora)
    socorrer_parados(h, telegram, shopee.buscar_fundo if shopee_ok else None, agora)
    um_post()
    try:   # o vigia nunca derruba o robô
        ult = ultimo_garimpo()
        if ult:
            h["ultimo_garimpo"] = ult.isoformat()
        vigiar(h, telegram, agora, ult)
    except Exception as e:
        print(f"[vigia] falhou: {e}")
    if shopee_ok:
        checar_vendas_shopee(h, telegram, agora)
    erros += soltar_fila(h, telegram, ate_proxima_execucao(agora))
    salvar_hist(h)
    gravar_relatorio(h, agora)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
