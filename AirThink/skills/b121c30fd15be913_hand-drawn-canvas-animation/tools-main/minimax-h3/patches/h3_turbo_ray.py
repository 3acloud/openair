"""Турбо-сэмплер MiniMax H3 в виде обычного импортируемого модуля.

Зачем это нужно. Родная нода ComfyUI-MiniMax-H3-Turbo возвращает
KSAMPLER(_turbo_sampler), где функция живёт в модуле с именем вида
"/path/ComfyUI-MiniMax-H3-Turbo". Ray отправляет SAMPLER в воркеры через pickle,
а pickle сохраняет функцию ссылкой module.qualname и на распаковке пытается
этот модуль импортировать. Имя с дефисами и слэшами импортировать нельзя, и
воркер падает с ModuleNotFoundError.

Здесь те же функции лежат в модуле с нормальным именем, который стоит в
site-packages, поэтому воркер импортирует его без вопросов. Код сэмплера
перенесён дословно, чтобы поведение совпадало с однокарточным прогоном.

Источник: custom_nodes/ComfyUI-MiniMax-H3-Turbo/__init__.py
"""
import math

import torch
from tqdm.auto import trange

SHIFT_V = 12.0
SHIFT_A = 3.0


def _time_shift_sigma(sigma, fr, to):
    base = sigma / (fr + sigma * (1.0 - fr))
    return to * base / (1.0 + (to - 1.0) * base)


def _time_shift_slope(sigma, fr, to):
    base = sigma / (fr + sigma * (1.0 - fr))
    return (to * (1.0 + (fr - 1.0) * base) ** 2) / (fr * (1.0 + (to - 1.0) * base) ** 2)


def _audio_sigma(sv):
    return _time_shift_sigma(sv, SHIFT_V, SHIFT_A)


def _audio_slope(sv):
    return _time_shift_slope(sv, SHIFT_V, SHIFT_A)


def _latent_shapes(model):
    """[video_shape, audio_shape], по которым сэмплер режет плоский латент:
    сначала идёт видео, потом аудио, нужна точка разреза."""
    guider = getattr(model, "inner_model", model)
    conds = getattr(guider, "conds", None)
    if conds:
        for cond_list in conds.values():
            for c in (cond_list or []):
                mc = c.get("model_conds", {}) if isinstance(c, dict) else {}
                if "latent_shapes" in mc:
                    return mc["latent_shapes"].cond
    return None


@torch.no_grad()
def turbo_sampler(model, x, sigmas, extra_args=None, callback=None, disable=None,
                  **kwargs):
    extra_args = {} if extra_args is None else extra_args
    shapes = _latent_shapes(model)
    if not shapes or len(shapes) < 2:
        raise RuntimeError(
            "турбо-сэмплеру нужен видео+аудио латент MiniMax H3 "
            "(выход EmptyMiniMaxH3LatentAV или MiniMaxH3ImageToVideo)")
    v_numel = math.prod(shapes[0][1:])           # плоская упаковка [видео | аудио]
    s_in = x.new_ones([x.shape[0]])
    for i in trange(len(sigmas) - 1, disable=disable):
        sv, sv_n = float(sigmas[i]), float(sigmas[i + 1])
        denoised = model(x, sigmas[i] * s_in, **extra_args)
        out = (x - denoised) / sigmas[i]
        xv, ov = x[..., :v_numel], out[..., :v_numel]
        xa, oa = x[..., v_numel:], out[..., v_numel:]
        xv = xv + (sv_n - sv) * ov               # видео по своей сигме
        sl = _audio_slope(max(sv, 1e-6))
        xa = xa + (_audio_sigma(sv_n) - _audio_sigma(sv)) * (oa / sl)   # аудио по своим часам
        x = torch.cat([xv, xa], dim=-1)
        if callback is not None:
            callback({"i": i, "denoised": denoised, "x": x,
                      "sigma": sigmas[i], "sigma_hat": sigmas[i]})
    return x
