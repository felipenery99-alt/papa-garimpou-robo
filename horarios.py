"""Sorteia os horários do dia (fixos para a data, diferentes a cada dia)."""
import random
from datetime import date, datetime, time, timedelta

import config


def _minutos(hm):
    return hm[0] * 60 + hm[1]


def agenda_do_dia(dia: date) -> dict[str, list[time]]:
    """10 horários por canal, 08–22h, minutos quebrados, ≥45 min de intervalo,
    mais peso nos picos e sem dois canais no mesmo minuto."""
    rnd = random.Random(f"papa-{dia.isoformat()}")
    ini, fim = _minutos(config.JANELA_INICIO), _minutos(config.JANELA_FIM)
    picos = [(_minutos(a), _minutos(b)) for a, b in config.PICOS]
    usados: set[int] = set()
    agenda = {}
    for canal in config.CANAIS:
        for _ in range(500):
            slots = []
            while len(slots) < config.POSTS_POR_CANAL_DIA * 6:
                m = rnd.randint(ini, fim - 1)
                if m % 30 == 0:
                    continue  # nada de :00 e :30
                peso = 3 if any(a <= m < b for a, b in picos) else 1
                if rnd.random() < peso / 3:
                    slots.append(m)
            # garante um post de manhã cedo (08:05–09:40) para não perder o começo do dia
            manha = [m for m in range(ini + 5, ini + 100) if m % 30 and m not in usados]
            escolhidos: list[int] = [rnd.choice(manha)]
            for m in sorted(set(slots), key=lambda _: rnd.random()):
                if m in usados:
                    continue
                if all(abs(m - e) >= config.INTERVALO_MIN_MIN for e in escolhidos):
                    escolhidos.append(m)
                if len(escolhidos) == config.POSTS_POR_CANAL_DIA:
                    break
            if len(escolhidos) == config.POSTS_POR_CANAL_DIA:
                break
        escolhidos.sort()
        usados.update(escolhidos)
        agenda[canal] = [time(m // 60, m % 60) for m in escolhidos]
    return agenda


def vencidos(agenda: dict[str, list[time]], agora: datetime, feitos: set[str], tolerancia_min=55):
    """Horários que já chegaram (até `tolerancia_min` de atraso) e ainda não foram postados."""
    saida = []
    for canal, horarios in agenda.items():
        for h in horarios:
            chave = f"{agora.date().isoformat()} {canal} {h.strftime('%H:%M')}"
            momento = datetime.combine(agora.date(), h, tzinfo=agora.tzinfo)
            if chave not in feitos and momento <= agora <= momento + timedelta(minutes=tolerancia_min):
                saida.append((canal, chave))
    return saida
