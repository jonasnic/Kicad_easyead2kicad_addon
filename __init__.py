"""KiCad package bootstrap for EasyEDA to KiCad plugin."""

import logging

try:
    from .plugins import EasyEDA2KiCadPlugin

    plugin = EasyEDA2KiCadPlugin()
    if hasattr(plugin, "register"):
        plugin.register()
except Exception as exc:  # pragma: no cover
    logging.getLogger(__name__).debug("EasyEDA2KiCad bootstrap failed: %r", exc)