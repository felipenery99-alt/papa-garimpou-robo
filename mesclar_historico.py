"""Junta o histórico desta execução com o que já está no GitHub, sem perder o que a outra gravou.
Uso: python mesclar_historico.py nosso.json remoto.json saida.json
(29/10: o push com "vale a versão desta execução" apagava os posts da execução anterior e o robô repostava.)"""
import json
import sys


def mesclar(nosso: dict, remoto: dict) -> dict:
    out = dict(remoto)
    out.update(nosso)
    for k in ("slots_feitos", "ig_feitos", "ig_ofertas_usadas", "ig_comentarios", "menus_fixados"):
        out[k] = list(dict.fromkeys(remoto.get(k, []) + nosso.get(k, [])))
    for k in ("postados", "postados_nome", "pecas_usadas"):
        out[k] = {**remoto.get(k, {}), **nosso.get(k, {})}
    for k in ("pecas_dia", "feed_dia"):
        a, b = remoto.get(k, {}), nosso.get(k, {})
        out[k] = {d: max(a.get(d, 0), b.get(d, 0)) for d in {**a, **b}}
    por_id = {o["id"]: o for o in remoto.get("ofertas_dia", [])}
    por_id.update({o["id"]: o for o in nosso.get("ofertas_dia", [])})
    out["ofertas_dia"] = list(por_id.values())
    if "ig_giro" in remoto or "ig_giro" in nosso:
        out["ig_giro"] = max(remoto.get("ig_giro", 0), nosso.get("ig_giro", 0))
    # a fila desta execução não pode trazer de volta o que a outra já postou
    out["fila"] = [o for o in nosso.get("fila", []) if o.get("id") not in out.get("postados", {})]
    return out


if __name__ == "__main__":
    nosso = json.load(open(sys.argv[1], encoding="utf-8"))
    remoto = json.load(open(sys.argv[2], encoding="utf-8"))
    json.dump(mesclar(nosso, remoto), open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
