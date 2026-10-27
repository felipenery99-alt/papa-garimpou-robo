"""Filtro de qualidade: só passa oferta boa e de marca boa."""
import unicodedata

import config


def _norm(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode()
    return f" {txt.lower()} "


def marca_da_oferta(oferta: dict, canal: str) -> str | None:
    """Devolve a marca boa encontrada no nome/loja, ou None."""
    lista = config.MARCAS_MARCAS if canal == "marcas" else config.MARCAS_ACHADINHOS
    texto = _norm(f"{oferta.get('nome', '')} {oferta.get('loja', '')}")
    for marca in sorted(lista, key=len, reverse=True):
        if _norm(marca).strip() and f" {_norm(marca).strip()} " in texto:
            return marca
    return None


def avaliar(oferta: dict, canal: str) -> tuple[bool, str]:
    """(aprovada, motivo). Critério de dono: na dúvida, reprova."""
    nome = _norm(oferta.get("nome", ""))
    for p in config.PALAVRAS_PROIBIDAS:
        if _norm(p).strip() in nome:
            return False, f"palavra proibida: {p}"
    if not marca_da_oferta(oferta, canal):
        return False, "marca fora da lista boa"
    if canal == "marcas" and not oferta.get("loja_oficial"):
        return False, "canal Marcas exige loja oficial"
    if (oferta.get("nota") or 0) < config.NOTA_MINIMA:
        return False, f"nota {oferta.get('nota')} < {config.NOTA_MINIMA}"
    if (oferta.get("vendas") or 0) < config.VENDAS_MINIMAS:
        return False, f"poucas vendas ({oferta.get('vendas')})"
    minimo = config.DESCONTO_MINIMO if canal == "marcas" else config.DESCONTO_MINIMO_ACHADINHOS
    if (oferta.get("desconto") or 0) < minimo:
        return False, f"desconto {oferta.get('desconto')}% < {minimo}%"
    if not oferta.get("link") or not oferta.get("imagem"):
        return False, "sem link de afiliado ou sem foto"
    return True, "ok"


def pontuar(oferta: dict) -> float:
    """Ordena as aprovadas: desconto, comissão, prova social."""
    return (
        (oferta.get("desconto") or 0) * 1.0
        + (oferta.get("comissao_pct") or 0) * 2.0
        + min((oferta.get("vendas") or 0) / 1000, 20)
        + ((oferta.get("nota") or 0) - 4.5) * 10
    )
