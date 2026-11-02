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
    dia["convites_story"] = {n: len(c["entradas"]) for n, c in h.get("convites_story", {}).items()}
    dia["telegram_membros"] = {c: telegram.membros(d) for c, d in {**config.CANAIS, "geral": config.GERAL}.items()}
    dia["instagram_feito"] = [f[11:] for f in h.get("ig_feitos", []) if f.startswith(hoje)]
    dia["shopee_ligada"] = bool(os.environ.get("SHOPEE_APP_ID"))
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


def garimpar_todas(canal: str, fonte, h: dict, agora: datetime, termos: list[str] | None = None) -> list[dict]:
    """Todas as ofertas boas e não postadas de todas as buscas do canal, melhores primeiro.
    Sem cota: o único filtro é a qualidade (regra do dono: achou coisa boa, posta)."""
    reprovados = {}
    boas = {}
    for termo in termos or config.BUSCAS[canal]:
        try:
            ofertas = fonte(termo)
        except Exception as e:
            raise RuntimeError(f"busca '{termo}' falhou: {e}") from e
        for o in ofertas:
            ok, motivo = qualidade.avaliar(o, canal)
            if ok and not ja_postado_recente(h, o["id"], agora, o.get("nome", "")):
                boas[o["id"]] = o
            elif not ok:
                reprovados[motivo] = reprovados.get(motivo, 0) + 1
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


def publicar_menus(h: dict, telegram) -> None:
    feitos = h.setdefault("menus_fixados", [])
    for destino in [*config.CANAIS.values(), config.GERAL]:
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
    return [o for o in lista if o.get("canal") in config.CANAIS and o.get("dia", "") >= limite
            and not (o.get("valida_ate") and o["valida_ate"] < agora.isoformat())]


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


def ate_proxima_execucao(agora: datetime) -> datetime:
    """A fila corre até 3 min antes da próxima execução do robo.yml (nunca depois das 22h)."""
    fim = agora.replace(hour=config.JANELA_FIM[0], minute=config.JANELA_FIM[1], second=0, microsecond=0)
    for hm in config.EXECUCOES:
        prox = agora.replace(hour=int(hm[:2]), minute=int(hm[3:]), second=0, microsecond=0)
        if prox > agora + timedelta(minutes=5):
            fim = min(fim, prox - timedelta(minutes=3))
            break
    return min(fim, agora + timedelta(minutes=45))


def soltar_fila(h: dict, telegram, limite: datetime) -> int:
    """Posta uma oferta por vez, alternando os canais de nicho (cada uma também vai para o
    canal geral), com intervalo sorteado. O que sobrar fica na fila para a próxima execução."""
    import os
    import random
    import time as _time
    erros = 0
    vez = 0
    if h.get("fila") and not os.environ.get("PAPA_SEM_ATRASO"):
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
            h.setdefault("ofertas_dia", []).append({**oferta, "canal": canal, "dia": hoje})
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
    print(f"fila: {len(h.get('fila', []))} oferta(s) esperando a próxima execução")
    return erros


LEGENDA_CTA = ("\n\nComenta QUERO que o Papa te manda o link no direct 💎\n"
               "Achou coisa boa de marca, o Papa posta na hora. Só loja oficial, grátis no Telegram.\n"
               "Comenta CANAIS que eu te mando os 4 canais no direct 📲\n\n"
               "#publi link de afiliado")


def reels_do_banco(h: dict, agora: datetime) -> tuple[list[bytes], str]:
    """Reels sem oferta: capa + 3 peças de pilares diferentes do banco + convite."""
    import artes
    pcs = conteudo.escolher(h, agora.date(), n=3)
    quadros = [artes.capa_reel(("O PAPA", "ENSINA"), "3 coisas antes de comprar")] + [artes.peca(p) for p in pcs]
    quadros.append(artes.story_convite())
    leg = "😎💎 " + " / ".join(p["titulo"][0].title() for p in pcs) + "\n\n" + pcs[0]["legenda"].replace("😎💎 ", "")
    return quadros, leg + LEGENDA_CTA


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
    pool = [o for o in h.get("ofertas_dia", []) if o.get("dia", "") >= semana] + carregar_manuais(h, agora)
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
               "Comenta QUERO que eu mando os links 💎\n\n#publi link de afiliado")
        slides = [artes.capa_salvavel(cat, teto)] + [artes.post_oferta(o, o["canal"]) for o in top]
        mid = instagram.carrossel(slides, f"{tag}-salvavel", leg)
        dm = f"Oi! Aqui é o Papa 😎💎\n\nOs 5 melhores {cat} até R$ {teto}:\n\n" + "\n\n".join(
            f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}\n{o['link']}" for i, o in enumerate(top))
        h.setdefault("ig_dm_links", {})[mid] = dm + "\n\nPreço pode mudar a qualquer momento. #publi link de afiliado"
        registrar_interativo(agora, "carrossel_salvavel", top)
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
    ofertas = [o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o["id"] not in usadas]
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
            instagram.story(artes.story_oferta(o, o["canal"], selo="PEDIDO ATENDIDO"), f"{tag}-pedido-{o['id']}.jpg")
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
            elif tipo == "story_top4" and len([o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje]) >= 4:
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
                    instagram.story(artes.story_oferta(o, o["canal"]), f"{tag}-story-{o['id']}.jpg")
                    usadas.append(o["id"])
            elif tipo == "post_achado":
                if not ofertas:
                    post_do_banco(h, agora, chave)
                    feitos.append(chave)
                    continue
                o = max(ofertas, key=qualidade.pontuar)
                ofertas.remove(o)
                leg = f"😎💎 Achado do dia: {o['nome']}\n\nDe {post._brl(o['preco_antigo'])} por {post._brl(o['preco'])} ({o['desconto']}% OFF)" if o.get("preco_antigo") else f"😎💎 Achado do dia: {o['nome']} por {post._brl(o['preco'])}"
                instagram.foto(artes.post_oferta(o, o["canal"]), f"{tag}-post-{o['id']}.jpg", leg + LEGENDA_CTA)
                usadas.append(o["id"])
            elif tipo == "reels":
                import video
                # 30/10: até 3 Reels/dia; cada um usa ofertas que ainda não saíram em Reels hoje
                ja = set(h.setdefault("ig_reels_ofertas", {}).get(hoje, []))
                top = sorted((o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o["id"] not in ja),
                             key=qualidade.pontuar, reverse=True)[:5]
                if len(top) >= 3:
                    quadros = ([artes.capa_reel(("ACHADOS", "DO PAPA"), "Os melhores de hoje")]
                               + [artes.story_oferta(o, o["canal"]) for o in top] + [artes.story_convite()])
                    lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}" for i, o in enumerate(top))
                    leg = "😎💎 Os achados do Papa hoje\n\n" + lista + LEGENDA_CTA
                    h["ig_reels_ofertas"][hoje] = list(ja | {o["id"] for o in top})
                else:
                    # sem oferta nova suficiente: Reels de dica do banco (alcance não pode parar)
                    quadros, leg = reels_do_banco(h, agora)
                instagram.reels(video.reel(quadros), leg)
                h["ig_ultimo_reel"] = agora.isoformat()
            elif tipo == "carrossel_top5":
                top = sorted(h.get("ofertas_dia", []), key=qualidade.pontuar, reverse=True)
                top = [o for o in top if o.get("dia") == hoje][:5]
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
    fortes = [o for o in h.get("ofertas_dia", []) if o.get("dia") == hoje and o.get("preco_antigo")
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
    nome = f"story-{agora:%Y%m%d}"
    if nome not in conv:
        try:
            conv[nome] = {"link": telegram.criar_convite(config.GERAL, nome), "entradas": []}
            CONVITE_STORY.write_text(f"{nome} {conv[nome]['link']}\n", encoding="utf-8")
        except Exception as e:
            if h.get("convite_erro") != agora.date().isoformat():
                h["convite_erro"] = agora.date().isoformat()
                telegram.avisar_dono(f"não consegui criar o convite {nome} em {config.GERAL}: {e} "
                                     "(o robô precisa da permissão 'Convidar usuários' no canal)")
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
    for velho in sorted(conv)[:-30]:
        conv.pop(velho)
    print(f"[convites] {nome}: {len(conv.get(nome, {}).get('entradas', []))} entrada(s) hoje")


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
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    agora = datetime.now(FUSO)
    if args.agenda:
        # Telegram não tem agenda (posta na hora que acha); só o Instagram tem horários fixos.
        for hora, tipo in config.INSTAGRAM_AGENDA:
            print("instagram", hora, tipo)
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
    try:
        rodar_instagram(h, agora)
    except Exception as e:
        telegram.avisar_dono(f"Instagram: erro geral {e}")
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("TELEGRAM_BOT_TOKEN ausente — nada postado")
        salvar_hist(h)
        gravar_relatorio(h, agora)
        return 0
    # Sem cota diária (dono, 27/10): toda oferta boa entra. Fila contínua (dono, 28/10): em vez de
    # despejar tudo de uma vez, solta uma oferta a cada poucos minutos até perto da próxima execução.
    erros = 0
    publicar_menus(h, telegram)
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
            telegram.avisar_dono(f"garimpo de {canal} falhou: {e}. Não postei.")
            erros += 1
            continue
        entrar_na_fila(h, canal, ofertas, agora)
    convites_story(h, telegram, agora)
    preparar_story_link(h, agora)
    top10_semana(h, telegram, agora)
    socorrer_parados(h, telegram, shopee.buscar_fundo if shopee_ok else None, agora)
    if shopee_ok:
        checar_vendas_shopee(h, telegram, agora)
    erros += soltar_fila(h, telegram, ate_proxima_execucao(agora))
    salvar_hist(h)
    gravar_relatorio(h, agora)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
