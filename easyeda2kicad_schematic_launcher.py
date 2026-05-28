"""Schematic-side launcher for EasyEDA to KiCad importer.

Intended for KiCad Eeschema netlist/BOM script hooks where ActionPlugin menu
entries are not available in the Schematic Editor host.
"""

from __future__ import annotations

import traceback
import os
import sys

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGINS_DIR = os.path.join(_ROOT_DIR, "plugins")

for _path in (_ROOT_DIR, _PLUGINS_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def main() -> int:
    import wx

    # Support both repository layout (plugins/*) and flattened PCM layout
    # (action/dialog files directly in plugin root).
    try:
        from plugins.action_easyeda2kicad import _ensure_easyeda2kicad
        from plugins.dialog_easyeda2kicad import EasyEDA2KiCadDialog
    except Exception:
        from action_easyeda2kicad import _ensure_easyeda2kicad
        from dialog_easyeda2kicad import EasyEDA2KiCadDialog

    ok, err, python_exe = _ensure_easyeda2kicad()
    if not ok:
        wx.MessageBox(
            "Could not load easyeda2kicad.\n\n"
            f"{err}\n\n"
            f"Interpreter used: {python_exe}\n\n"
            "Please install it manually by running:\n"
            f"  {python_exe} -m pip install easyeda2kicad",
            "EasyEDA to KiCad – Installation Error",
            wx.OK | wx.ICON_ERROR,
        )
        return 1

    app = wx.GetApp()
    if app is None:
        app = wx.App(False)

    dlg = EasyEDA2KiCadDialog(None, python_executable=python_exe)
    dlg.ShowModal()
    dlg.Destroy()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        details = traceback.format_exc()
        message = (
            "EasyEDA to KiCad launcher crashed while starting.\n\n"
            "If this persists, share this traceback with the plugin developer.\n\n"
            f"{details}"
        )

        # Prefer wx popup, but use Win32 MessageBox fallback when wx import fails.
        try:
            import wx

            app = wx.GetApp()
            if app is None:
                app = wx.App(False)
            wx.MessageBox(message, "EasyEDA to KiCad – Launch Error", wx.OK | wx.ICON_ERROR)
        except Exception:
            try:
                import ctypes

                ctypes.windll.user32.MessageBoxW(0, message, "EasyEDA to KiCad – Launch Error", 0x10)
            except Exception:
                pass
        raise