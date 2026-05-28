"""
EasyEDA to KiCad – ActionPlugin
Integrates easyeda2kicad into KiCad as a PCB-editor action plugin.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_RESOURCES_DIR = os.path.join(_PLUGIN_DIR, "..", "resources")


# ---------------------------------------------------------------------------
# Dependency bootstrap
# ---------------------------------------------------------------------------

def _resolve_python_executable() -> str:
    """Return a usable Python interpreter path for subprocess invocations."""
    candidates: list[str] = []

    for attr in ("executable", "_base_executable"):
        value = getattr(sys, attr, "")
        if isinstance(value, str) and value:
            candidates.append(value)

    exe_dir = os.path.dirname(sys.executable) if sys.executable else ""
    if exe_dir:
        candidates.append(os.path.join(exe_dir, "python.exe"))
        candidates.append(os.path.join(exe_dir, "python3.exe"))

    for name in ("python", "python3"):
        which_path = shutil.which(name)
        if which_path:
            candidates.append(which_path)

    for candidate in candidates:
        if not candidate:
            continue
        base = os.path.basename(candidate).lower()
        if base.startswith("python") and os.path.exists(candidate):
            return candidate

    # Last resort for environments where PATH lookup is the only option.
    return "python"

def _ensure_easyeda2kicad() -> tuple[bool, str, str]:
    """Return (success, error_message, python_executable).

    Validates *easyeda2kicad* in a subprocess using the selected Python
    interpreter. If missing, attempts installation via pip and validates again.
    This avoids false negatives when KiCad's host process cannot directly
    import modules that are available to the subprocess interpreter.
    """
    python_exe = _resolve_python_executable()

    def _module_available() -> tuple[bool, str]:
        check = subprocess.run(
            [python_exe, "-c", "import easyeda2kicad"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check.returncode == 0:
            return True, ""
        err = (check.stderr or check.stdout or "").strip()
        return False, err

    ok, check_err = _module_available()
    if ok:
        return True, "", python_exe

    logger.info("easyeda2kicad not found – attempting automatic installation via pip…")
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "easyeda2kicad"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            ok, post_install_err = _module_available()
            if ok:
                logger.info("easyeda2kicad installed successfully.")
                return True, "", python_exe
            return False, f"Installed but import still failed: {post_install_err}", python_exe
        else:
            return False, f"pip install failed:\n{result.stderr.strip()}", python_exe
    except subprocess.TimeoutExpired:
        return False, "pip install timed out after 120 s.", python_exe
    except Exception as exc:  # pragma: no cover
        return False, f"Unexpected error during installation: {exc}", python_exe


# ---------------------------------------------------------------------------
# ActionPlugin
# ---------------------------------------------------------------------------

def _get_action_plugin_base() -> type:
    """Return the available KiCad ActionPlugin base class.

    KiCad may load plugins in different editor host processes. Prefer
    `pcbnew.ActionPlugin` when available, but fall back to
    `eeschema.ActionPlugin` so the plugin can also appear in Schematic Editor.
    """
    # Prefer whichever KiCad host has already imported its module first.
    for module_name in ("eeschema", "pcbnew"):
        module = sys.modules.get(module_name)
        if module is not None:
            base = getattr(module, "ActionPlugin", None)
            if base is not None:
                return base

    # Fall back to importing likely hosts (eeschema first, then pcbnew).
    for module_name in ("eeschema", "pcbnew"):
        try:
            module = __import__(module_name)
            base = getattr(module, "ActionPlugin", None)
            if base is not None:
                return base
        except ImportError:
            continue

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

        ok, err, python_exe = _ensure_easyeda2kicad()
        if not ok:
            wx.MessageBox(
                "Could not load easyeda2kicad.\n\n"
                f"{err}\n\n"
                f"Interpreter used: {python_exe}\n\n"
                "Please install it manually by running:\n"
                f"  {python_exe} -m pip install easyeda2kicad\n\n"
                "On Windows, open the KiCad Command Prompt and run the command above.",
                "EasyEDA to KiCad – Installation Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        launcher_path = os.path.normpath(
            os.path.join(_PLUGIN_DIR, "..", "easyeda2kicad_schematic_launcher.py")
        )
        if not os.path.isfile(launcher_path):
            wx.MessageBox(
                "Could not find launcher script:\n\n"
                f"{launcher_path}",
                "EasyEDA to KiCad – Launch Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        creationflags = 0
        if os.name == "nt":
            creationflags = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )

        try:
            subprocess.Popen(
                [python_exe, launcher_path],
                cwd=os.path.dirname(launcher_path),
                creationflags=creationflags,
            )
        except Exception as exc:
            wx.MessageBox(
                "Could not launch importer window in a separate process.\n\n"
                f"{exc}",
                "EasyEDA to KiCad – Launch Error",
                wx.OK | wx.ICON_ERROR,
            )
