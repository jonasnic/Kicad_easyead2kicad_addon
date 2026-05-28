"""
EasyEDA to KiCad – KiCad Action Plugin package.
"""

import os
import sys

# Ensure this directory is importable so relative imports work even when KiCad
# loads the package without the parent directory on sys.path.
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

from action_easyeda2kicad import EasyEDA2KiCadPlugin


def _register_if_available() -> None:
    """Register plugin when imported as KiCad's primary package entrypoint."""
    try:
        plugin = EasyEDA2KiCadPlugin()
        if hasattr(plugin, "register"):
            plugin.register()
    except Exception:
        # Keep import side effects non-fatal for non-KiCad contexts.
        pass


_register_if_available()

