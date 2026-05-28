"""
EasyEDA to KiCad – KiCad Action Plugin
Registers the plugin with KiCad on import.
"""

import os
import sys

# Ensure this directory is importable so relative imports work even when KiCad
# loads the package without the parent directory on sys.path.
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

try:
    from action_easyeda2kicad import EasyEDA2KiCadPlugin

    plugin = EasyEDA2KiCadPlugin()
    if hasattr(plugin, "register"):
        plugin.register()
    else:  # pragma: no cover
        print("[EasyEDA2KiCad] No KiCad ActionPlugin host available for registration.")
except Exception as exc:  # pragma: no cover
    print(f"[EasyEDA2KiCad] Failed to register plugin: {exc}")
