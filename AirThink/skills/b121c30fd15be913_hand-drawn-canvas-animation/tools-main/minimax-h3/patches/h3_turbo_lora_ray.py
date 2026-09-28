"""Турбо-LoRA MiniMax H3 для Ray-воркеров Raylight.

Зачем это нужно. RayLoraLoader отдаёт LoRA стандартным загрузчикам ComfyUI, а
они на этой LoRA грузят ноль ключей: её имена (blocks.0.attn.qkv_proj.lora_A.weight)
не совпадают с картой, которую строит model_lora_keys_unet. Родная нода
MiniMaxH3TurboLoRA не «грузит LoRA» в обычном смысле — она строит карту имён
руками и раскладывает веса по модулям сама. Здесь та же раскладка, вынесенная
в отдельный модуль, чтобы её можно было позвать из воркера.

Раскладка идёт двумя путями, потому что база бывает двух видов:

  backbone (208 модулей: attn.qkv_proj, attn.out_proj, mlp.fc1, mlp.fc2)
      применяется в рантайме через bypass-инъекцию ComfyUI: out = base(x) + lora(x).
      Веса не трогаются вовсе, что и нужно на квантованной базе (в int8 дельта
      частично округлилась бы при обратном квантовании) и на FSDP, где параметры
      разрезаны между картами и лежат как DTensor.

  adaln (51 модуль: blocks.N.adaln_proj.linear и final_layer.adaln_proj.linear)
      на pruned-базе патчем веса не ложится в принципе: обновление живёт в
      2688-мерном пространстве silu(t_emb), а pruned-чекпойнт схлопнул это в
      8-мерную кривую (adaln_t_table), так что у линейного слоя вход шириной 8
      против 2688 у LoRA-A. Поэтому оно переинжектится в рантайме: общий
      silu(t_emb) интерполируется из приложенной к ноде сетки, а forward каждой
      adaln-проекции добавляет B @ A @ silu(t_emb).

Совместимость с Raylight проверена по его исходникам:
  * USP подменяет block.attn.forward своим usp_attn_forward, но внутри зовёт
    self.qkv_proj(x) и self.out_proj(...) как модули — bypass-хуки на них живут.
  * FSDP2 (fully_shard) не переименовывает и не пересобирает дерево модулей,
    поэтому ссылки, взятые до шардинга, остаются валидными.
  * инъекции и object-патчи применяет базовый ModelPatcher.patch_model, который
    FSDPModelPatcher не переопределяет (он переопределяет только load).

Источник раскладки: custom_nodes/ComfyUI-MiniMax-H3-Turbo/__init__.py
"""

import math
import os

import torch
import torch.nn.functional as F

import comfy.lora
import comfy.patcher_extension
import comfy.utils
import comfy.weight_adapter

SHIFT_V, SHIFT_A = 12.0, 3.0

# сетка silu(t_emb) лежит рядом с родной нодой; путь можно переопределить
GRID_ENV = "H3_TURBO_GRID"
GRID_CANDIDATES = (
    "/mnt/nvme2/engines/ComfyUI-raylight/custom_nodes/ComfyUI-MiniMax-H3-Turbo/h3_silu_temb_grid.safetensors",
    "/mnt/nvme2/engines/ComfyUI/custom_nodes/ComfyUI-MiniMax-H3-Turbo/h3_silu_temb_grid.safetensors",
)


def _time_shift_sigma(sigma, fr, to):
    base = sigma / (fr + sigma * (1.0 - fr))
    return to * base / (1.0 + (to - 1.0) * base)


_EGRID = None


def _grid_path():
    p = os.environ.get(GRID_ENV)
    if p and os.path.exists(p):
        return p
    for c in GRID_CANDIDATES:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(
        "не найдена сетка h3_silu_temb_grid.safetensors, укажи путь в %s" % GRID_ENV)


def _egrid():
    global _EGRID
    if _EGRID is None:
        _EGRID = comfy.utils.load_torch_file(_grid_path())["silu_t_emb_grid"]  # [1025, 2688]
    return _EGRID


def _unique_t(timestep, shift_v, shift_a, has_vis_cond):
    sv = float((timestep.flatten()[0] / 1000.0).clamp(min=1e-6))
    t_v = 1.0 - sv
    t_a = 1.0 - _time_shift_sigma(sv, shift_v, shift_a)
    s = {t_v, t_a}
    if has_vis_cond:
        s.add(max(t_v, 0.999))
    return sorted(s)


def _interp_egrid(unique_t, E, device, dtype):
    E = E.to(device)
    n = E.shape[0]
    rows = []
    for t in unique_t:
        pos = min(max(t, 0.0), 1.0) * (n - 1)
        i0 = min(int(math.floor(pos)), n - 2)
        rows.append(torch.lerp(E[i0].float(), E[i0 + 1].float(), pos - i0))
    return torch.stack(rows).to(dtype)                                   # [M, 2688]


def _make_adaln_forward(base, a, b, shared):
    """Замена AdalnProj.forward, ставится object-патчем на сам атрибут .forward.

    Патчится именно атрибут, а не модуль целиком: обёртка-модуль добавила бы в
    дерево параметров лишний путь (.base.linear.weight), который стриминговый
    загрузчик ComfyUI записывает в свой бэкап и на выгрузке пытается вернуть по
    этому пути — а object-патч к тому моменту уже вернул обычный AdalnProj, и
    восстановление падает. a и b держатся простыми захваченными тензорами и в
    дерево не попадают; приведение к device/dtype идёт на каждый вызов, что
    заодно покрывает случай, когда проекция считается на GPU, а веса LoRA лежат
    на CPU."""

    def forward(t_emb):
        x = base.linear(F.silu(t_emb) if base.apply_silu else t_emb)
        st = shared.get("silu_temb")
        if st is not None:
            av = a.to(x.device, x.dtype)
            bv = b.to(x.device, x.dtype)
            sv = st.to(x.device, x.dtype)
            x = x + (bv @ (av @ sv.T)).T                                 # [M, out]
        x = x.view(x.shape[0] * base.modalities, base.expand * base.hidden)
        return x.chunk(base.expand, dim=-1)

    return forward


class _FrugalLoRA(comfy.weight_adapter.LoRAAdapter):
    """Bypass-адаптер с экономным сложением.

    Штатный bypass считает g(base_out + h(x)); у LoRA h(x) заводит проекцию
    полного размера дважды (out и out * scale), а внешнее сложение — третий раз,
    то есть на каждом обойдённом слое транзитом висит ~3 его выхода. На down-
    проекции MLP (fc2, выход = hidden, при последовательности под 46k токенов)
    это около 1.5 ГБ лишнего пика на блок. Накопление up(down(x))*scale прямо в
    base_out оставляет один временный тензор вместо трёх. base_out — свежий
    выход модуля, так что сложение на месте безопасно. Численно результат тот же.
    Только Linear (все модули этой LoRA линейные), остальное падает на штатный
    путь."""

    def bypass_forward(self, org_forward, x, *args, **kwargs):
        base_out = org_forward(x, *args, **kwargs)
        if getattr(self, "is_conv", False):
            return super().bypass_forward(org_forward, x, *args, **kwargs)
        up, down, alpha = self.weights[0], self.weights[1], self.weights[2]
        rank = down.shape[0]
        scale = (alpha / rank if alpha is not None else 1.0) * getattr(self, "multiplier", 1.0)
        down = down.to(dtype=x.dtype)
        up = up.to(dtype=x.dtype)
        return base_out.add_(F.linear(F.linear(x, down), up), alpha=scale)


def _apply_bypass_lora(patcher, lora, modules, strength):
    """Низкоранговое обновление в рантайме: out = base(x) + lora(x). Веса не
    трогаются, поэтому квантование базы и шардинг FSDP ему безразличны. Карта
    имён строится вручную, потому что штатный model_lora_keys_unet именования
    этой LoRA не знает."""
    key_map = {m: "diffusion_model.{}.weight".format(m) for m in modules}
    loaded = comfy.lora.load_lora(lora, key_map, log_missing=False)
    manager = comfy.weight_adapter.BypassInjectionManager()
    sd_keys = set(patcher.model.state_dict().keys())
    n = 0
    missing = []
    for key, adapter in loaded.items():
        if key not in sd_keys:
            missing.append(key)
            continue
        if isinstance(adapter, comfy.weight_adapter.LoRAAdapter):
            adapter = _FrugalLoRA(adapter.loaded_keys, adapter.weights)
        elif not isinstance(adapter, comfy.weight_adapter.WeightAdapterBase):
            continue
        manager.add_adapter(key, adapter, strength=strength)
        n += 1
    injections = manager.create_injections(patcher.model)
    hooks = manager.get_hook_count()
    if hooks > 0:
        patcher.set_injections("bypass_lora", injections)
    return n, hooks, missing


def _apply_merge_lora(patcher, lora, modules, strength):
    """Путь для тесной памяти: дельта вплавляется в веса (тот же add_patches,
    который зовёт штатный load_lora_for_models). Дешевле всего по пику, но на
    квантованной базе часть обновления теряется при обратном квантовании, а на
    FSDP патч должен лечь на DTensor-шард — поэтому по умолчанию не он."""
    key_map = {m: "diffusion_model.{}.weight".format(m) for m in modules}
    loaded = comfy.lora.load_lora(lora, key_map, log_missing=False)
    n = len(patcher.add_patches(loaded, strength))
    return n, n, []


def _inject_adaln_egrid(patcher, dm, lora, adaln, strength):
    """Только для pruned-базы: обновление adaln живёт в 2688-мерном silu(t_emb),
    который pruned-чекпойнт схлопнул в кривую, так что ни адаптером, ни патчем
    веса оно не ложится. Переинжектим в рантайме: общий silu(t_emb) на каждый
    forward интерполируется из сетки, а forward каждой adaln-проекции добавляет
    B @ A @ silu(t_emb). По памяти это ничто (M <= 3 строк), поэтому работает
    одинаково в обоих режимах."""
    E = _egrid()
    shared = {"silu_temb": None}
    shift_v = float(getattr(dm, "sigma_shift_video", SHIFT_V))
    shift_a = float(getattr(dm, "sigma_shift_audio", SHIFT_A))

    def wrap(executor, *args, **kwargs):
        ts = args[1] if len(args) > 1 else kwargs.get("timestep")
        ctx = args[2] if len(args) > 2 else kwargs.get("context")
        payload = kwargs.get("minimax_payload") or {}
        has_vc = bool(payload.get("keyframes") or payload.get("refs"))
        us = _unique_t(ts, shift_v, shift_a, has_vc)
        shared["silu_temb"] = _interp_egrid(us, E, ctx.device, ctx.dtype)
        return executor(*args, **kwargs)

    patcher.add_wrapper_with_key(
        comfy.patcher_extension.WrappersMP.DIFFUSION_MODEL, "h3turbo", wrap)
    n = 0
    for name in adaln:                        # name = "....adaln_proj.linear"
        a = lora[name + ".lora_A.weight"]
        b = lora[name + ".lora_B.weight"] * strength
        key = "diffusion_model." + name.rsplit(".linear", 1)[0]
        patcher.add_object_patch(
            key + ".forward",
            _make_adaln_forward(patcher.get_model_object(key), a, b, shared))
        n += 1
    return n


def is_h3_turbo_lora(lora_sd):
    """Опознаём LoRA по её собственным именам, а не по метаданным: adaln_proj в
    паре с lora_A/lora_B встречается только у неё."""
    has_pair = any(k.endswith(".lora_A.weight") for k in lora_sd) and \
        any(k.endswith(".lora_B.weight") for k in lora_sd)
    has_adaln = any("adaln_proj" in k for k in lora_sd)
    has_blocks = any(k.startswith("blocks.") and "qkv_proj" in k for k in lora_sd)
    return has_pair and (has_adaln or has_blocks)


def is_h3_model(patcher):
    dm = getattr(getattr(patcher, "model", None), "diffusion_model", None)
    return dm is not None and hasattr(dm, "sigma_shift_video")


def apply(patcher, lora_sd, strength, low_vram=False, tag=""):
    """Точка входа: раскладывает турбо-LoRA по модулям уже загруженной модели.

    Патчер меняется на месте (в воркере это либо свежая FSDP-модель, либо клон
    закешированной базы, так что общий с кешем nn.Module не страдает — трогаются
    только словари самого патчера).
    """
    dm = patcher.model.diffusion_model
    pruned = bool(getattr(dm, "use_adaln_curves", False))
    modules = sorted({k.rsplit(".lora_", 1)[0] for k in lora_sd})
    mode = "merge" if low_vram else "bypass"

    # на pruned-базе adaln всегда идёт отдельным путём независимо от режима,
    # остальное — backbone
    if pruned:
        backbone = [m for m in modules if "adaln_proj" not in m]
        adaln = [m for m in modules if "adaln_proj" in m]
    else:
        backbone, adaln = modules, []

    apply_fn = _apply_merge_lora if low_vram else _apply_bypass_lora
    n, hooks, missing = apply_fn(patcher, lora_sd, backbone, strength)
    n_adaln = _inject_adaln_egrid(patcher, dm, lora_sd, adaln, strength) if (pruned and adaln) else 0

    base = "pruned" if pruned else "full"
    detail = ("%d весов пропатчено" % n) if low_vram else ("%d адаптеров, %d хуков" % (n, hooks))
    extra = (" + %d adaln в рантайме" % n_adaln) if n_adaln else ""
    print("[H3TurboRay%s] база %s [%s]: strength=%s | %d backbone-модулей, %s%s"
          % (tag, base, mode, strength, len(backbone), detail, extra), flush=True)
    if missing:
        print("[H3TurboRay%s] ВНИМАНИЕ: %d ключей нет в state_dict модели, первый: %s"
              % (tag, len(missing), missing[0]), flush=True)
    if n == 0:
        raise RuntimeError(
            "H3-турбо LoRA не легла ни на один модуль — раскладка не совпала с моделью")
    return patcher
