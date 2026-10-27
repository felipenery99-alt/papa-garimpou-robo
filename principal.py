"""Robô do Papa Garimpou — roda a cada 15 min (GitHub Actions).

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
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import config
import horarios
import post
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
    dia["telegram_membros"] = {c: telegram.membros(d) for c, d in config.CANAIS.items()}
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


def ja_postado_recente(h: dict, oferta_id: str, agora: datetime) -> bool:
    quando = h["postados"].get(oferta_id)
    if not quando:
        return False
    return datetime.fromisoformat(quando) > agora - timedelta(days=config.NAO_REPETIR_DIAS)


def garimpar(canal: str, fonte, h: dict, agora: datetime, rodada: int) -> dict | None:
    termos = config.BUSCAS[canal]
    inicio = rodada % len(termos)
    reprovados = {}
    for termo in termos[inicio:] + termos[:inicio]:
        try:
            ofertas = fonte(termo)
        except Exception as e:
            raise RuntimeError(f"busca '{termo}' falhou: {e}") from e
        boas = []
        for o in ofertas:
            ok, motivo = qualidade.avaliar(o, canal)
            if ok and not ja_postado_recente(h, o["id"], agora):
                boas.append(o)
            elif not ok:
                reprovados[motivo] = reprovados.get(motivo, 0) + 1
        if boas:
            return max(boas, key=qualidade.pontuar)
    print(f"[{canal}] nenhuma oferta boa. Reprovações: {reprovados}")
    return None


LEGENDA_CTA = ("\n\nComenta QUERO que o Papa te manda o link no direct 💎\n"
               "Todo dia 20 achados de marca boa, só loja oficial, grátis no Telegram (link na bio).\n\n"
               "#publi link de afiliado")


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
    for hora, tipo in config.INSTAGRAM_AGENDA:
        chave = f"{hoje} {hora} {tipo}"
        hh, mm = map(int, hora.split(":"))
        momento = agora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if chave in feitos or not (momento <= agora <= momento + timedelta(minutes=50)):
            continue
        try:
            if tipo == "story_convite":
                instagram.story(artes.story_convite(), f"{tag}-convite-{hh}.jpg")
            elif tipo == "story_oferta":
                if not ofertas:
                    # sem oferta: story fixo do Papa (gira entre os modelos), nunca deixa buraco
                    n = h.get("ig_giro", 0)
                    h["ig_giro"] = n + 1
                    instagram.story(artes.story_institucional(n % 3), f"{tag}-fixo-{hh}.jpg")
                else:
                    o = ofertas.pop(0)
                    instagram.story(artes.story_oferta(o, o["canal"]), f"{tag}-story-{o['id']}.jpg")
                    usadas.append(o["id"])
            elif tipo == "post_achado":
                if not ofertas:
                    # feed todo dia: sem oferta, entra o post fixo do dia
                    if not any(f.startswith(hoje) and ("feed" in f) for f in feitos):
                        i = agora.toordinal() % 3
                        instagram.foto(artes.feed_institucional(i), f"{tag}-feed-fixo.jpg",
                                       artes.LEGENDAS_INSTITUCIONAIS[i] + LEGENDA_CTA)
                        feitos.append(f"{hoje} feed")
                    feitos.append(chave)
                    continue
                o = max(ofertas, key=qualidade.pontuar)
                ofertas.remove(o)
                leg = f"😎💎 Achado do dia: {o['nome']}\n\nDe {post._brl(o['preco_antigo'])} por {post._brl(o['preco'])} ({o['desconto']}% OFF)" if o.get("preco_antigo") else f"😎💎 Achado do dia: {o['nome']} por {post._brl(o['preco'])}"
                instagram.foto(artes.post_oferta(o, o["canal"]), f"{tag}-post-{o['id']}.jpg", leg + LEGENDA_CTA)
                usadas.append(o["id"])
            elif tipo == "carrossel_top5":
                top = sorted(h.get("ofertas_dia", []), key=qualidade.pontuar, reverse=True)
                top = [o for o in top if o.get("dia") == hoje][:5]
                if len(top) < 3:
                    feitos.append(chave)
                    continue
                slides = [artes.capa_top5()] + [artes.post_oferta(o, o["canal"]) for o in top]
                lista = "\n".join(f"{i+1}. {o['nome'][:60]} — {post._brl(o['preco'])}" for i, o in enumerate(top))
                instagram.carrossel(slides, f"{tag}-top5", "😎💎 TOP 5 do Papa hoje\n\n" + lista + LEGENDA_CTA)
            if tipo in ("post_achado", "carrossel_top5"):
                feitos.append(f"{hoje} feed")
            feitos.append(chave)
            print(f"[ig] publicado {chave}")
        except instagram.ContaErrada as e:
            telegram.avisar_felipe(f"INSTAGRAM BLOQUEADO (conta errada): {e}")
            return
        except Exception as e:
            telegram.avisar_felipe(f"Instagram {chave} falhou: {e}. Não publiquei.")
            feitos.append(chave)
    # Vigia: sempre pelo menos 3 stories no ar
    try:
        ativos = instagram.stories_ativos()
        faltam = max(0, config.STORIES_MINIMOS - ativos)
        for k in range(min(faltam, 3)):
            n = h.get("ig_giro", 0)
            h["ig_giro"] = n + 1
            instagram.story(artes.story_institucional(n % 4 - 1), f"{tag}-vigia-{agora:%H%M}-{k}.jpg")
        if faltam:
            print(f"[ig] vigia: havia {ativos} stories no ar, publiquei {min(faltam, 3)}")
    except Exception as e:
        print(f"[ig] vigia de stories: {e}")
    try:
        resp = instagram.responder_comentarios(set(h.setdefault("ig_comentarios", [])))
        h["ig_comentarios"] += resp
        if resp:
            print(f"[ig] respondi {len(resp)} comentário(s)")
    except Exception as e:
        print(f"[ig] comentários: {e}")
    instagram.limpar_midia(hoje)
    h["ig_feitos"] = [f for f in feitos if f[:10] >= (agora.date() - timedelta(days=3)).isoformat()]
    h["ig_ofertas_usadas"] = usadas[-200:]


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
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    agora = datetime.now(FUSO)
    agenda = horarios.agenda_do_dia(agora.date())

    if args.agenda:
        for canal, hs in agenda.items():
            print(canal, " ".join(x.strftime("%H:%M") for x in hs))
        return 0

    if args.story_teste:
        # Publica agora o story convite (teste real da cadeia Instagram) e responde comentários.
        import artes
        import instagram
        sid = instagram.story(artes.story_convite(), f"{agora:%Y%m%d}-convite-teste.jpg")
        print("story publicado:", sid)
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
        for canal, destino in config.CANAIS.items():
            m = requests.get(f"{api}/getChatMember", params={"chat_id": destino, "user_id": bot_id}, timeout=30).json()
            r = m.get("result", {})
            print(f"{canal} {destino}: status={r.get('status')} pode_postar={r.get('can_post_messages')} {'' if m.get('ok') else m}")
        up = requests.get(f"{api}/getUpdates", timeout=30).json()
        privados = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
                    for u in up.get("result", []) if u.get("message", {}).get("chat", {}).get("type") == "private"}
        print("chats privados com o bot (para ALERTA_CHAT_ID):", privados or "nenhum — mande /start para o bot")
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
    import random
    h = carregar_hist()
    hoje = agora.date().isoformat()
    try:
        rodar_instagram(h, agora)
    except Exception as e:
        telegram.avisar_felipe(f"Instagram: erro geral {e}")
    if not (os.environ.get("SHOPEE_APP_ID") and os.environ.get("SHOPEE_SECRET") and os.environ.get("TELEGRAM_BOT_TOKEN")):
        print("chaves da Shopee ainda não configuradas — Telegram em espera, nada postado")
        salvar_hist(h)
        gravar_relatorio(h, agora)
        return 0
    # Cada execução (20 por dia, horários no robo.yml) posta em 1 canal: o que tiver
    # menos posts hoje (empate = sorteio). Assim cada canal fica com 10 horários próprios.
    contagem = {c: sum(1 for s in h["slots_feitos"] if s.startswith(f"{hoje} {c}")) for c in config.CANAIS}
    abertos = [c for c, n in contagem.items() if n < config.POSTS_POR_CANAL_DIA]
    if not abertos:
        print("cota do dia já cumprida")
        salvar_hist(h)
        gravar_relatorio(h, agora)
        return 0
    menor = min(contagem[c] for c in abertos)
    canal_da_vez = random.choice([c for c in abertos if contagem[c] == menor])
    pendentes = [(canal_da_vez, f"{hoje} {canal_da_vez} {agora:%H:%M}")]
    erros = 0
    for canal, chave in pendentes:
        try:
            oferta = garimpar(canal, shopee.buscar, h, agora, len(h["slots_feitos"]))
            if not oferta:
                telegram.avisar_felipe(f"sem oferta boa para {canal} em {chave}; pulei o horário.")
            else:
                telegram.postar_foto(config.CANAIS[canal], post.foto_com_selo(oferta["imagem"]),
                                     post.legenda(oferta, canal))
                h["postados"][oferta["id"]] = agora.isoformat()
                h.setdefault("ofertas_dia", []).append({**oferta, "canal": canal, "dia": hoje})
                print(f"postado {chave}: {oferta['nome'][:60]}")
            h["slots_feitos"].append(chave)
        except telegram.DestinoProibido as e:
            telegram.avisar_felipe(f"BLOQUEADO destino errado: {e}")
            erros += 1
        except Exception as e:
            telegram.avisar_felipe(f"erro em {chave}: {e}. Não postei.")
            h["slots_feitos"].append(chave)
            erros += 1
    salvar_hist(h)
    gravar_relatorio(h, agora)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
