"""Турбо-сэмплер H3, пригодный для отправки в Ray-воркеры.

Родная нода отдаёт KSAMPLER с функцией из модуля, чьё имя содержит дефисы, и
pickle не может импортировать его на стороне воркера. Здесь та же функция
берётся из site-packages модуля h3_turbo_ray, поэтому распаковка проходит.
"""
import comfy.samplers
import h3_turbo_ray


class H3TurboSamplerRay:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("SAMPLER",)
    FUNCTION = "get_sampler"
    CATEGORY = "MiniMaxH3Turbo"
    DESCRIPTION = ("4-шаговый сэмплер H3 Turbo для Raylight: то же поведение, "
                   "что у родной ноды, но функция лежит в импортируемом модуле, "
                   "поэтому переживает отправку в Ray-воркер.")

    def get_sampler(self):
        return (comfy.samplers.KSAMPLER(h3_turbo_ray.turbo_sampler),)


NODE_CLASS_MAPPINGS = {"H3TurboSamplerRay": H3TurboSamplerRay}
NODE_DISPLAY_NAME_MAPPINGS = {"H3TurboSamplerRay": "H3 Turbo Sampler (Ray)"}
