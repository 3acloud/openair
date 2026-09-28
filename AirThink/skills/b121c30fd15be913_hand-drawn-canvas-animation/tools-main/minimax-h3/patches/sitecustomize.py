"""Ставит раскладку турбо-LoRA MiniMax H3 в Ray-воркеры Raylight.

Почему файл лежит здесь, а не правкой в custom_nodes/raylight. Ray передаёт
класс актора ссылкой module.qualname и импортирует его в каждом рабочем
процессе заново, поэтому monkey patch, сделанный в главном процессе ComfyUI,
до воркера не доезжает. sitecustomize выполняется модулем site при старте
любого Python из этого venv, включая процессы ray::RayWorker, так что хук
успевает встать до импорта воркера. Правка репозитория raylight при этом не
трогается и переживает его обновление.

Патчится ровно один метод — RayWorker.load_lora. Всё, что не является турбо-
LoRA H3, уходит в оригинал без изменений.

Режим раскладки: H3_TURBO_LORA_MODE=bypass (по умолчанию) либо merge.
Отключить патч целиком: H3_TURBO_LORA_PATCH=0
"""

import importlib.abc
import importlib.util
import os
import sys

_TARGET = "raylight.distributed_worker.ray_worker"


def _patch_ray_worker(module):
    worker_cls = getattr(module, "RayWorker", None)
    if worker_cls is None or getattr(worker_cls, "_h3_turbo_patched", False):
        return

    original = worker_cls.load_lora

    def load_lora(self):
        import comfy.utils as comfy_utils

        import h3_turbo_lora_ray as h3

        tag = " rank %s" % getattr(self, "local_rank", "?")
        low_vram = os.environ.get("H3_TURBO_LORA_MODE", "bypass").lower() == "merge"
        rest = []

        for lora in (self.lora_list or []):
            sd = comfy_utils.load_torch_file(lora["path"], safe_load=True)
            handled = h3.is_h3_turbo_lora(sd) and h3.is_h3_model(self.model)
            if handled:
                self.model = h3.apply(self.model, sd, float(lora["strength_model"]),
                                      low_vram=low_vram, tag=tag)
            else:
                rest.append(lora)
            del sd

        if rest:
            # остальные LoRA отдаём штатному пути, подсунув ему укороченный список
            saved = self.lora_list
            self.lora_list = rest
            try:
                original(self)
            finally:
                self.lora_list = saved

    worker_cls.load_lora = load_lora
    worker_cls._h3_turbo_patched = True
    print("[H3TurboRay] раскладка турбо-LoRA включена (pid %d)" % os.getpid(), flush=True)


class _Loader(importlib.abc.Loader):
    def __init__(self, inner):
        self._inner = inner

    def create_module(self, spec):
        return self._inner.create_module(spec)

    def exec_module(self, module):
        self._inner.exec_module(module)
        try:
            _patch_ray_worker(module)
        except Exception as e:                                    # noqa: BLE001
            print("[H3TurboRay] патч не встал: %r" % (e,), flush=True)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != _TARGET:
            return None
        # снимаем себя на время поиска, иначе уйдём в рекурсию
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        except Exception:                                         # noqa: BLE001
            spec = None
        finally:
            if self not in sys.meta_path:
                sys.meta_path.insert(0, self)
        if spec is None or spec.loader is None:
            return None
        spec.loader = _Loader(spec.loader)
        return spec


if os.environ.get("H3_TURBO_LORA_PATCH", "1") != "0":
    sys.meta_path.insert(0, _Finder())
