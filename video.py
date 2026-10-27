"""Reels do Papa Garimpou: junta as artes (1080x1920) num vídeo curto com música própria.

A música é sintetizada aqui mesmo (batida simples em 120 bpm), então não tem direito
autoral de ninguém. O ffmpeg vem do pacote imageio-ffmpeg (funciona no Windows e no Actions).
"""
import io
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

TAXA = 44100
BPM = 120


def _nota(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def musica(segundos: float) -> bytes:
    """Loop animado e original: bumbo nos tempos, chimbal no contratempo, baixo e arpejo (Dó–Lá m–Fá–Sol)."""
    batida = 60 / BPM
    acordes = [(130.81, (261.63, 329.63, 392.00)), (110.00, (220.00, 261.63, 329.63)),
               (87.31, (174.61, 220.00, 261.63)), (98.00, (196.00, 246.94, 293.66))]
    n = int(segundos * TAXA)
    amostras = bytearray()
    for i in range(n):
        t = i / TAXA
        pos = t % batida                      # posição dentro do tempo
        compasso = int(t / (batida * 4)) % 4
        baixo, arpejo = acordes[compasso]
        v = 0.0
        if pos < 0.12:                        # bumbo
            v += 0.9 * math.exp(-pos * 30) * _nota(55 + 90 * math.exp(-pos * 40), pos)
        meio = (t + batida / 2) % batida
        if meio < 0.03:                       # chimbal (ruído curto, determinístico)
            v += 0.15 * math.exp(-meio * 150) * math.sin(i * 12.9898) * 1.0
        v += 0.25 * _nota(baixo, t) * (0.6 + 0.4 * math.exp(-pos * 6))
        passo = int(t / (batida / 2)) % 3      # arpejo em colcheias
        dentro = t % (batida / 2)
        v += 0.18 * math.exp(-dentro * 7) * _nota(arpejo[passo] * 2, t)
        fade = min(1.0, t / 0.3, (segundos - t) / 0.8)
        amostras += struct.pack("<h", int(max(-1, min(1, v * 0.6 * fade)) * 32000))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(bytes(amostras))
    return out.getvalue()


def reel(quadros: list[bytes], segundos_por_quadro: float = 2.6, transicao: float = 0.4) -> bytes:
    """Monta o MP4 (H.264 + AAC, 1080x1920, 30 fps) com as artes deslizando para o lado.
    Os quadros são compostos aqui (Pillow) e enviados ao ffmpeg, então serve qualquer versão dele."""
    if len(quadros) < 2:
        raise ValueError("Reels precisa de pelo menos 2 quadros")
    fps, w, h = 30, 1080, 1920
    imgs = [Image.open(io.BytesIO(q)).convert("RGB").resize((w, h)) for q in quadros]
    parado = int((segundos_por_quadro - transicao) * fps)
    passos = int(transicao * fps)
    total = (len(imgs) * parado + (len(imgs) - 1) * passos) / fps
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        (pasta / "musica.wav").write_bytes(musica(total + 0.5))
        saida = pasta / "reel.mp4"
        gravador = imageio_ffmpeg.write_frames(
            str(saida), (w, h), fps=fps, codec="libx264", quality=None, bitrate=None, macro_block_size=8,
            pix_fmt_out="yuv420p", audio_path=str(pasta / "musica.wav"), audio_codec="aac",
            output_params=["-crf", "23", "-preset", "medium", "-shortest", "-movflags", "+faststart"])
        gravador.send(None)
        for i, img in enumerate(imgs):
            dados = img.tobytes()
            for _ in range(parado):
                gravador.send(dados)
            if i + 1 < len(imgs):
                for k in range(1, passos + 1):
                    x = int(w * (1 - (1 - k / passos) ** 2))   # desliza com freio no fim
                    quadro = Image.new("RGB", (w, h))
                    quadro.paste(img, (-x, 0))
                    quadro.paste(imgs[i + 1], (w - x, 0))
                    gravador.send(quadro.tobytes())
        gravador.close()
        return saida.read_bytes()
