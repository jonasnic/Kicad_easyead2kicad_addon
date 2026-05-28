"""
EasyEDA to KiCad – ActionPlugin
Integrates easyeda2kicad into KiCad as a PCB-editor action plugin.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_RESOURCES_DIR = os.path.join(_PLUGIN_DIR, "..", "resources")


# ---------------------------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------------------------

def _ensure_easyeda2kicad() -> tuple[bool, str]:
    """Return (success, error_message).

    Checks whether *easyeda2kicad* is importable. If not, attempts to install
    it into the current Python environment via pip so that the plugin works
    out of the box without any manual setup.
    """
    try:
        import easyeda2kicad  # noqa: F401
        return True, ""
    except ImportError:
        pass

    logger.info("easyeda2kicad not found – attempting automatic installation via pip…")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "easyeda2kicad"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            try:
                import easyeda2kicad  # noqa: F401
                logger.info("easyeda2kicad installed successfully.")
                return True, ""
            except ImportError as exc:
                return False, f"Installed but import still failed: {exc}"
        else:
            return False, f"pip install failed:\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "pip install timed out after 120 s."
    except Exception as exc:  # pragma: no cover
        return False, f"Unexpected error during installation: {exc}"


# ---------------------------------------------------------------------------
# ActionPlugin
# ---------------------------------------------------------------------------

def _get_action_plugin_base() -> type:
    """Return the available KiCad ActionPlugin base class.

    KiCad may load plugins in different editor host processes. Prefer
    `pcbnew.ActionPlugin` when available, but fall back to
    `eeschema.ActionPlugin` so the plugin can also appear in Schematic Editor.
    """
    try:
        import pcbnew  # available in PCB Editor host

        base = getattr(pcbnew, "ActionPlugin", None)
        if base is not None:
            return base
    except ImportError:
        pass

    try:
        import eeschema  # available in Schematic Editor host

        base = getattr(eeschema, "ActionPlugin", None)
        if base is not None:
            return base
    except ImportError:
        pass

    # Allow importing outside KiCad (tests, linting, docs tooling).
    return object


_BASE_CLASS = _get_action_plugin_base()


class EasyEDA2KiCadPlugin(_BASE_CLASS):
    """KiCad ActionPlugin that opens the EasyEDA-to-KiCad importer dialog."""

    def defaults(self) -> None:
        self.name = "EasyEDA to KiCad"
        self.category = "Import"
        self.description = (
            "Import a component from LCSC/EasyEDA (symbol, footprint, 3D model) "
            "into your KiCad library by entering its LCSC/JLCPCB ID."
        )
        self.show_toolbar_button = True
        icon_path = os.path.join(_RESOURCES_DIR, "icon.png")
        if os.path.isfile(icon_path):
            self.icon_file_name = icon_path

    def Run(self) -> None:  # noqa: N802
        import wx  # wx is bundled with KiCad

        ok, err = _ensure_easyeda2kicad()
        if not ok:
            wx.MessageBox(
                "Could not load easyeda2kicad.\n\n"
                f"{err}\n\n"
                "Please install it manually by running:\n"
                "  pip install easyeda2kicad\n\n"
                "On Windows, open the KiCad Command Prompt and run the command above.",
                "EasyEDA to KiCad – Installation Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        from dialog_easyeda2kicad import EasyEDA2KiCadDialog  # type: ignore[import]

        top_windows = wx.GetTopLevelWindows()
        parent = top_windows[0] if top_windows else None
        dlg = EasyEDA2KiCadDialog(parent)
        dlg.ShowModal()
        dlg.Destroy()
