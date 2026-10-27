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


def buscar(termo: str, limite: int = 30) -> list[dict]:
    payload = json.dumps({"query": QUERY, "variables": {"keyword": termo, "page": 1, "limit": limite}},
                         separators=(",", ":"))
    r = requests.post(URL, data=payload, headers=_assinar(payload), timeout=40)
    r.raise_for_status()
    dados = r.json()
    if dados.get("errors"):
        raise RuntimeError(f"Shopee API: {dados['errors']}")
    nos = dados["data"]["productOfferV2"]["nodes"]
    return [_normalizar(n) for n in nos]


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
