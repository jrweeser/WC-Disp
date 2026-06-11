from __future__ import annotations

import io
import threading
from typing import TYPE_CHECKING

import requests
from PIL import Image

if TYPE_CHECKING:
    import customtkinter as ctk

DEFAULT_FLAG_SIZE = (32, 22)


class FlagCache:
    """Downloads and caches country flag images for the UI."""

    _instance: FlagCache | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._images: dict[str, Image.Image] = {}
        self._ctk_images: dict[str, "ctk.CTkImage"] = {}
        self._download_lock = threading.Lock()

    @classmethod
    def get(cls) -> FlagCache:
        with cls._lock:
            if cls._instance is None:
                cls._instance = FlagCache()
            return cls._instance

    def get_pil(self, url: str, size: tuple[int, int] = DEFAULT_FLAG_SIZE) -> Image.Image | None:
        if not url:
            return None
        cache_key = f"{url}:{size[0]}x{size[1]}"
        if cache_key in self._images:
            return self._images[cache_key]
        with self._download_lock:
            if cache_key in self._images:
                return self._images[cache_key]
            try:
                response = requests.get(url, timeout=12)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content)).convert("RGBA")
                image = image.resize(size, Image.Resampling.LANCZOS)
                self._images[cache_key] = image
                return image
            except (requests.RequestException, OSError):
                return None

    def get_ctk_image(
        self,
        master: "ctk.CTkBaseClass",
        url: str,
        size: tuple[int, int] = DEFAULT_FLAG_SIZE,
    ) -> "ctk.CTkImage | None":
        if not url:
            return None
        key = f"{id(master)}:{url}:{size[0]}x{size[1]}"
        if key in self._ctk_images:
            return self._ctk_images[key]
        pil = self.get_pil(url, size)
        if pil is None:
            return None
        import customtkinter as ctk

        ctk_image = ctk.CTkImage(
            light_image=pil,
            dark_image=pil,
            size=size,
        )
        self._ctk_images[key] = ctk_image
        return ctk_image

    def preload(self, urls: list[str]) -> None:
        for url in urls:
            if url:
                self.get_pil(url)
