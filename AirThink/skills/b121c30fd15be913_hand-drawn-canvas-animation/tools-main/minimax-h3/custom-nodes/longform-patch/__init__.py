"""Two inputs the H3 Multishot samplers need to run a Turbo chain.

Patches ComfyUI-H3-Multishot in memory at startup. Nothing on disk is modified,
so the patch survives updates to that pack instead of being overwritten by them.

What it adds to both H3MultishotSampler and H3MultishotSampler + Memory:

  sampler_opt (SAMPLER)
      The pack builds its sampler from a NAME out of comfy.samplers.KSampler, so
      a SAMPLER produced by another node cannot be used. MiniMax H3 runs video
      and audio on two different flow schedules and the 4-step Turbo distill
      ships its own sampler that handles that; a stock sampler over-steps the
      audio at 4 steps and breaks it. Connect the Turbo sampler here and the
      chain runs at 4 steps instead of 20.

  evict_text_encoder (BOOLEAN, default True)
      Before every shot the pack pushes the text encoder to CPU and calls
      free_memory(90% of the default device). On a single card that is the whole
      point: it stops the DiT loading partially and streaming weights from RAM.
      On a multi-GPU split it is harmful - if the DiT lives on cuda:0/cuda:1 and
      the encoder on cuda:2/cuda:3 they never compete, and the purge evicts the
      DiT itself, which then reloads every shot. Turn it off there.

Measured on 4x RTX 3090: with the Turbo sampler connected, a 4-shot 40s clip at
1344x768 renders in 44 minutes instead of roughly three hours at 20 steps.
"""
import logging
import sys

log = logging.getLogger("H3MultishotPatch")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

PACK_FILE = "h3_multishot_utils.py"

EXTRA_INPUTS = {
    "sampler_opt": ("SAMPLER", {
        "tooltip": "Optional SAMPLER from another node. Overrides sampler_name "
                   "when connected. Required for the H3 Turbo 4-step distill, "
                   "whose sampler drives video and audio on their separate flow "
                   "schedules."}),
    "evict_text_encoder": ("BOOLEAN", {
        "default": True,
        "tooltip": "Push the text encoder to CPU and purge VRAM before each "
                   "shot. Keep ON for a single card. Turn OFF on a multi-GPU "
                   "split where the encoder and the DiT sit on different cards, "
                   "otherwise the purge evicts the DiT and it reloads per shot."}),
}


def _patch_input_types(cls):
    original = cls.INPUT_TYPES.__func__

    def INPUT_TYPES(_cls):
        spec = original(_cls)
        spec.setdefault("optional", {}).update(EXTRA_INPUTS)
        return spec

    cls.INPUT_TYPES = classmethod(INPUT_TYPES)


def _called_from_pack():
    """True when the immediate caller is the multishot pack itself.

    The eviction has to be suppressed only where the pack asks for it. ComfyUI
    and ComfyUI-MultiGPU call free_memory for their own memory management during
    the same run, and those calls must go through untouched - MultiGPU reads the
    return value, so a blanket stub also breaks it with len(None).
    """
    try:
        return sys._getframe(2).f_code.co_filename.endswith(PACK_FILE)
    except ValueError:                            # pragma: no cover
        return False


def _patch_run(cls):
    original = getattr(cls, cls.FUNCTION)

    def run(self, *args, sampler_opt=None, evict_text_encoder=True, **kwargs):
        from comfy_extras import nodes_custom_sampler as ncs
        import comfy.model_management as mm

        keep_sampler = ncs.KSamplerSelect.get_sampler
        keep_free = mm.free_memory
        clip = kwargs.get("clip") or (args[1] if len(args) > 1 else None)
        keep_to = getattr(clip.patcher.model, "to", None) if clip is not None else None

        if sampler_opt is not None:
            # the node asks for a sampler by name exactly once per run
            ncs.KSamplerSelect.get_sampler = lambda _self, _name: (sampler_opt,)
            log.info("[H3MultishotPatch] using the connected SAMPLER")

        if not evict_text_encoder:
            def guarded_free_memory(*a, **kw):
                if _called_from_pack():
                    return []                     # same shape the real one returns
                return keep_free(*a, **kw)

            mm.free_memory = guarded_free_memory
            if keep_to is not None:
                model = clip.patcher.model
                model.to = lambda *a, **kw: model if _called_from_pack() else keep_to(*a, **kw)
            log.info("[H3MultishotPatch] eviction suppressed for the chain "
                     "(multi-GPU split); ignore the pack's 'TE evicted' line")
        try:
            return original(self, *args, **kwargs)
        finally:
            ncs.KSamplerSelect.get_sampler = keep_sampler
            mm.free_memory = keep_free
            if keep_to is not None:
                try:
                    del clip.patcher.model.to      # drop the instance attribute
                except AttributeError:
                    clip.patcher.model.to = keep_to

    setattr(cls, cls.FUNCTION, run)


def _apply():
    try:
        from nodes import NODE_CLASS_MAPPINGS as ALL
    except Exception as e:                        # pragma: no cover
        log.error("[H3MultishotPatch] cannot reach the node registry: %s", e)
        return

    targets = [n for n in ("H3MultishotSampler", "H3MultishotMemorySampler")
               if n in ALL]
    if not targets:
        log.warning("[H3MultishotPatch] ComfyUI-H3-Multishot is not installed, "
                    "or it loaded after this patch. Nothing to do.")
        return

    for name in targets:
        cls = ALL[name]
        if getattr(cls, "_h3_patched", False):
            continue
        _patch_input_types(cls)
        _patch_run(cls)
        cls._h3_patched = True
        log.info("[H3MultishotPatch] %s: added sampler_opt and "
                 "evict_text_encoder", name)


_apply()
