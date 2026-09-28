"""Две ноды, которых не хватает стеку Raylight для работы с MiniMax H3.

H3Resolution — пресеты кадра вместо селектора в мегапикселях. H3 считает по
короткой стороне 768 и требует кратности 32, так что осмысленных вариантов
немного и их проще выбрать из списка, чем подбирать числом.

H3MultishotRay — цепочка шотов из одного скрипта. Модель упирается в 362 кадра
за генерацию (около 15 секунд), дальше только цепочкой: последний кадр шота
уходит keyframe'ом в следующий. Нода с боевого стека это умеет, но работает с
обычной моделью, а в Raylight модель разложена по воркерам и наружу торчит
RAY_ACTORS — поэтому цикл собран здесь заново поверх ray-вызова.

Против ручной сборки из отдельных нод даёт три вещи: любое число шотов вместо
жёстко зашитых в граф, срезку 1/24 секунды звука вместе с дублирующим кадром
(иначе звук уползает от видео на каждом стыке) и кроссфейд на склейке.
"""

import torch

import comfy.model_management
import nodes
from comfy_extras.nodes_audio import vae_decode_audio
from comfy_extras.nodes_minimax_h3 import MiniMaxH3ImageToVideo

FPS = 24.0
SEPARATOR = "---"

# кратно 32, короткая сторона 768 — родной холст H3
PRESETS = {
    "Горизонт 16:9 — 1344x768 (максимум)": (1344, 768),
    "Горизонт 16:9 — 1152x640": (1152, 640),
    "Горизонт 16:9 — 864x480 (быстро)": (864, 480),
    "Горизонт 4:3 — 1024x768": (1024, 768),
    "Вертикаль 9:16 — 768x1344 (Shorts, Reels)": (768, 1344),
    "Вертикаль 9:16 — 640x1152": (640, 1152),
    "Вертикаль 9:16 — 480x864 (быстро)": (480, 864),
    "Вертикаль 3:4 — 768x1024": (768, 1024),
    "Квадрат 1:1 — 768x768": (768, 768),
}


class H3Resolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"preset": (list(PRESETS.keys()),)}}

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "pick"
    CATEGORY = "MiniMaxH3Ray"
    DESCRIPTION = "Размер кадра под MiniMax H3: горизонт, вертикаль, квадрат."

    def pick(self, preset):
        w, h = PRESETS[preset]
        return (w, h)


def _seconds_to_frames(seconds):
    """Сетка модели: 17k+5 кадров при 24 fps, потолок 362."""
    n = max(5, round(seconds * FPS))
    n = n + (5 - (n % 17)) % 17
    return min(n, 362)


class H3Frames:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"seconds": ("FLOAT", {
            "default": 5.0, "min": 0.2, "max": 15.1, "step": 0.1,
            "tooltip": "Длительность клипа. 15 = потолок модели, 362 кадра."})}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("length",)
    FUNCTION = "calc"
    CATEGORY = "MiniMaxH3Ray"
    DESCRIPTION = ("Секунды в кадры по сетке модели 17k+5 при 24 fps. "
                   "Потолок 362 кадра за генерацию.")

    def calc(self, seconds):
        return (_seconds_to_frames(seconds),)


def _decode_video(vae, samples):
    # H3 держит видео и звук в одном вложенном латенте, картинка — первая часть.
    # Штатная VAEDecode делает ровно это, и без распаковки VAE падает на
    # NestedTensor.
    latent = samples["samples"]
    if latent.is_nested:
        latent = latent.unbind()[0]
    images = vae.decode(latent)
    if len(images.shape) == 5:
        images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
    return images


def _join_audio(chunks, sample_rate, crossfade_ms=40.0):
    """Сшивает куски встык с коротким кроссфейдом.

    Без него на стыке слышен щелчок: два шота считались независимо, и фаза на
    границе не совпадает. Кроссфейд короткий, чтобы не съесть звук события,
    попавшего ровно на склейку.
    """
    if len(chunks) == 1:
        return chunks[0]
    n = int(sample_rate * crossfade_ms / 1000.0)
    out = chunks[0]
    for nxt in chunks[1:]:
        k = min(n, out.shape[-1], nxt.shape[-1])
        if k <= 0:
            out = torch.cat([out, nxt], dim=-1)
            continue
        ramp = torch.linspace(0.0, 1.0, k, device=out.device, dtype=out.dtype)
        head, tail = out[..., :-k], out[..., -k:]
        blend = tail * (1.0 - ramp) + nxt[..., :k] * ramp
        out = torch.cat([head, blend, nxt[..., k:]], dim=-1)
    return out


class H3MultishotRay:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ray_actors": ("RAY_ACTORS",),
                "clip": ("CLIP",),
                "vae_video": ("VAE",),
                "vae_audio": ("VAE",),
                "sampler": ("SAMPLER",),
                "sigmas": ("SIGMAS",),
                "script": ("STRING", {
                    "multiline": True,
                    "default": "первый шот\n\n---\n\nвторой шот",
                    "tooltip": "Промпты шотов, разделённые строкой ---. "
                               "Сколько кусков, столько и шотов."}),
                "seconds_per_shot": ("FLOAT", {
                    "default": 5.0, "min": 0.2, "max": 15.1, "step": 0.1,
                    "tooltip": "Длительность ОДНОГО шота. 15 = потолок модели, "
                               "362 кадра."}),
                "width": ("INT", {"default": 1344, "min": 32, "max": 4096, "step": 32}),
                "height": ("INT", {"default": 768, "min": 32, "max": 4096, "step": 32}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                                 "control_after_generate": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "INT", "STRING")
    RETURN_NAMES = ("images", "audio", "shots", "info")
    FUNCTION = "run"
    CATEGORY = "MiniMaxH3Ray"
    DESCRIPTION = ("Цепочка шотов из одного скрипта: последний кадр шота "
                   "становится первым кадром следующего.")

    def run(self, ray_actors, clip, vae_video, vae_audio, sampler, sigmas,
            script, seconds_per_shot, width, height, seed):
        import ray
        from raylight.comfy_extra_dist.nodes_custom_sampler import _make_ray_guider

        shots = [s.strip() for s in script.split(SEPARATOR) if s.strip()]
        if not shots:
            raise ValueError("скрипт пустой: нужен хотя бы один промпт")
        length = _seconds_to_frames(seconds_per_shot)
        workers = ray_actors["workers"]

        frames, audio_chunks, sample_rate = [], [], None
        prev_last = None
        for i, prompt in enumerate(shots):
            print("[H3Multishot] шот %d из %d, %d кадров, сид %d"
                  % (i + 1, len(shots), length, seed + i), flush=True)

            out = MiniMaxH3ImageToVideo.execute(
                clip=clip, vae=vae_video, prompt=prompt,
                width=width, height=height, length=length,
                first_frame=prev_last)
            cond, latent = out[0], out[1]

            guider = _make_ray_guider(ray_actors, "basic", positive=cond)
            futures = [a.custom_sampler_advanced.remote(
                True, seed + i, guider, sampler, sigmas, latent) for a in workers]
            sampled = ray.get(futures)[0][0]

            img = _decode_video(vae_video, sampled)
            aud = vae_decode_audio(vae_audio, sampled)
            wave, sample_rate = aud["waveform"], aud["sample_rate"]

            if i > 0:
                # первый кадр этого шота — тот самый keyframe, то есть дубль
                # последнего кадра предыдущего; вместе с ним режем и его звук,
                # иначе дорожка убегает от картинки на кадр за каждый стык
                img = img[1:]
                cut = int(round(sample_rate / FPS))
                wave = wave[..., cut:]

            frames.append(img)
            audio_chunks.append(wave)
            prev_last = img[-1:]
            comfy.model_management.soft_empty_cache()

        images = torch.cat(frames, dim=0)
        waveform = _join_audio(audio_chunks, sample_rate)
        info = ("%d шот(ов) по %d кадров, итого %d кадров = %.2f с при %dx%d"
                % (len(shots), length, images.shape[0], images.shape[0] / FPS,
                   width, height))
        print("[H3Multishot] " + info, flush=True)
        return (images, {"waveform": waveform, "sample_rate": sample_rate},
                len(shots), info)


NODE_CLASS_MAPPINGS = {
    "H3Resolution": H3Resolution,
    "H3Frames": H3Frames,
    "H3MultishotRay": H3MultishotRay,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "H3Resolution": "H3: размер кадра",
    "H3Frames": "H3: длительность",
    "H3MultishotRay": "H3: цепочка шотов (Ray)",
}
