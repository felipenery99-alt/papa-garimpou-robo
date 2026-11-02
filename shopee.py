"""Cliente da API oficial de afiliados da Shopee (Brasil).

Doc oficial: painel de afiliado Shopee → Open API. Autenticação:
  Authorization: SHA256 Credential={AppId}, Timestamp={ts}, Signature={sha256(AppId+ts+payload+Secret)}
O campo offerLink já vem como link de afiliado da conta dona do AppId.

ATENÇÃO: nomes de campos conferidos de memória — validar com a doc assim que a
conta for aprovada (rodar `python principal.py --testar-shopee`).
"""
import hashlib
import json
import os
import time

import requests

URL = "https://open-api.affiliate.shopee.com.br/graphql"

QUERY = """
query($keyword:String,$page:Int,$limit:Int){
  productOfferV2(keyword:$keyword, sortType:2, page:$page, limit:$limit, listType:0){
    nodes{
      itemId productName shopName shopType
      price priceMin priceMax priceDiscountRate
      sales ratingStar commissionRate
      imageUrl offerLink productLink
    }
    pageInfo{ page limit hasNextPage }
  }
}
"""


def _assinar(payload: str) -> dict:
    app_id = os.environ["SHOPEE_APP_ID"]
    secret = os.environ["SHOPEE_SECRET"]
    ts = str(int(time.time()))
    assinatura = hashlib.sha256(f"{app_id}{ts}{payload}{secret}".encode()).hexdigest()
    return {
        "Authorization": f"SHA256 Credential={app_id}, Timestamp={ts}, Signature={assinatura}",
        "Content-Type": "application/json",
    }


class LimiteShopee(RuntimeError):
    """10030 'Rate limit exceeded' mesmo depois de esperar: o resto da execução não chama mais a API."""


# 02/11: com 3 chamadas por termo (01/11) + busca extra de canal parado, a API respondeu 10030 e o garimpo
# do canal inteiro caía ("Não postei"). Agora: intervalo mínimo entre chamadas, espera crescente no 10030 e,
# se persistir, trava a API até o fim da execução (o robô segue com o que já está na fila).
INTERVALO_S = 0.6
ESPERAS_10030 = (10, 25, 60)
_ultima = [0.0]
LIMITE_ATINGIDO = [False]


def _chamar(payload: str) -> dict:
    if LIMITE_ATINGIDO[0]:
        raise LimiteShopee("limite da API atingido nesta execução")
    for espera in (*ESPERAS_10030, None):
        pausa = INTERVALO_S - (time.time() - _ultima[0])
        if pausa > 0:
            time.sleep(pausa)
        _ultima[0] = time.time()
        r = requests.post(URL, data=payload, headers=_assinar(payload), timeout=40)
        r.raise_for_status()
        dados = r.json()
        erros = dados.get("errors") or []
        if not any((e.get("extensions") or {}).get("code") == 10030 for e in erros):
            if erros:
                raise RuntimeError(f"Shopee API: {erros}")
            return dados
        if espera is None:
            LIMITE_ATINGIDO[0] = True
            raise LimiteShopee("Shopee API: 10030 Rate limit exceeded (após esperar)")
        print(f"[shopee] limite de chamadas (10030), esperando {espera}s")
        time.sleep(espera)


def _pagina(termo: str, pagina: int, limite: int) -> list[dict]:
    payload = json.dumps({"query": QUERY, "variables": {"keyword": termo, "page": pagina, "limit": limite}},
                         separators=(",", ":"))
    dados = _chamar(payload)
    return [_normalizar(n) for n in dados["data"]["productOfferV2"]["nodes"]]


def buscar(termo: str, limite: int = 50) -> list[dict]:
    """01/11: com a regra "Shopee só loja oficial" a 1ª página (30 itens) quase não tinha Mall e os canais
    ficaram horas sem post. Agora: 2 páginas do termo + 1 página de "<termo> oficial", sem repetir item."""
    vistos, saida = set(), []
    for t, pg in ((termo, 1), (termo, 2), (f"{termo} oficial", 1)):
        try:
            itens = _pagina(t, pg, limite)
        except Exception:
            if not saida and pg == 1 and t == termo:
                raise   # a busca principal falhou: deixa o robô avisar
            continue
        for o in itens:
            if o["id"] not in vistos:
                vistos.add(o["id"])
                saida.append(o)
    return saida



def buscar_fundo(termo: str, limite: int = 50) -> list[dict]:
    """Canal parado (01/11): páginas 3 e 4 do termo, que a busca normal não alcança."""
    saida = []
    for pg in (3, 4):
        try:
            saida += _pagina(termo, pg, limite)
        except Exception:
            break
    return saida

def _normalizar(n: dict) -> dict:
    preco = float(n.get("priceMin") or n.get("price") or 0)
    desconto = int(n.get("priceDiscountRate") or 0)
    antigo = round(preco / (1 - desconto / 100), 2) if 0 < desconto < 100 else None
    return {
        "id": f"shopee-{n.get('itemId')}",
        "plataforma": "Shopee",
        "nome": n.get("productName", ""),
        "loja": n.get("shopName", ""),
        # shopType: 1 = Shopee Mall (loja oficial). Validar na doc.
        "loja_oficial": str(n.get("shopType")) in ("1", "[1]") or "mall" in str(n.get("shopType", "")).lower(),
        "preco": preco,
        "preco_antigo": antigo,
        "desconto": desconto,
        "vendas": int(n.get("sales") or 0),
        "nota": float(n.get("ratingStar") or 0),
        "comissao_pct": round(float(n.get("commissionRate") or 0) * 100, 1),
        "imagem": n.get("imageUrl"),
        "link": n.get("offerLink"),
    }


# 01/11 (dono: "eu recebo notificação por venda?"): relatório de conversões da Open API.
# 1ª versão usava variáveis $ini:Int64 e a API respondeu "wrong type" (10010): os valores vão
# escritos direto na consulta, como nos exemplos da doc. Se a completa falhar, tenta a mínima.
CAMPOS_VENDAS = ("conversionId purchaseTime totalCommission "
                 "orders{ orderId orderStatus items{ itemName itemTotalCommission } }")
CAMPOS_VENDAS_MIN = "conversionId purchaseTime totalCommission"


def _query_vendas(campos: str, ini: int, fim: int, scroll: str | None) -> str:
    args = f"purchaseTimeStart:{ini}, purchaseTimeEnd:{fim}, limit:100"
    if scroll:
        args += f", scrollId:{json.dumps(scroll)}"
    return f"{{ conversionReport({args}){{ nodes{{ {campos} }} pageInfo{{ hasNextPage scrollId }} }} }}"


def vendas(desde: int, ate: int | None = None) -> list[dict]:
    """Conversões (vendas com comissão) entre os timestamps `desde` e `ate`."""
    ate = ate or int(time.time())
    ultimo_erro = None
    for campos in (CAMPOS_VENDAS, CAMPOS_VENDAS_MIN):
        saida, scroll = [], None
        try:
            for _ in range(10):
                payload = json.dumps({"query": _query_vendas(campos, desde, ate, scroll)}, separators=(",", ":"))
                dados = _chamar(payload)
                rep = dados["data"]["conversionReport"]
                for n in rep.get("nodes") or []:
                    itens = [i.get("itemName", "") for o in (n.get("orders") or []) for i in (o.get("items") or [])]
                    saida.append({"id": str(n.get("conversionId")), "quando": n.get("purchaseTime"),
                                  "comissao": float(n.get("totalCommission") or 0), "itens": itens})
                info = rep.get("pageInfo") or {}
                if not info.get("hasNextPage"):
                    return saida
                scroll = info.get("scrollId")
            return saida
        except Exception as e:
            ultimo_erro = e
    raise RuntimeError(f"relatório de vendas da Shopee: {ultimo_erro}")
