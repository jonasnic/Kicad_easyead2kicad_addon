"""
EasyEDA to KiCad – Import Dialog
wxPython dialog that provides the user interface for importing LCSC/EasyEDA
components into KiCad libraries.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import wx
import wx.adv

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT = str(Path.home() / "Documents" / "KiCad" / "easyeda2kicad")


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


class _TextCtrlLogHandler(logging.Handler):
    """Logging handler that appends records to a wx.TextCtrl."""

    def __init__(self, text_ctrl: wx.TextCtrl) -> None:
        super().__init__()
        self._ctrl = text_ctrl

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        level = record.levelname
        wx.CallAfter(self._append, msg, level)

    def _append(self, msg: str, level: str) -> None:
        if not self._ctrl:
            return
        if level in ("ERROR", "CRITICAL"):
            colour = wx.Colour(200, 0, 0)
        elif level == "WARNING":
            colour = wx.Colour(180, 100, 0)
        else:
            colour = wx.BLACK
        self._ctrl.SetDefaultStyle(wx.TextAttr(colour))
        self._ctrl.AppendText(msg + "\n")
        self._ctrl.SetDefaultStyle(wx.TextAttr(wx.BLACK))


class EasyEDA2KiCadDialog(wx.Dialog):
    """Main import dialog for the EasyEDA-to-KiCad addon."""

    def __init__(self, parent: wx.Window | None, python_executable: str | None = None) -> None:
        super().__init__(
            parent,
            title="EasyEDA to KiCad Importer",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(560, 560),
        )
        self._log_handler: _TextCtrlLogHandler | None = None
        self._python_executable = python_executable or _resolve_python_executable()
        self._build_ui()
        self.Centre()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)

        # ── Component ID ──────────────────────────────────────────────
        id_box = wx.StaticBox(panel, label="Component ID")
        id_sizer = wx.StaticBoxSizer(id_box, wx.HORIZONTAL)
        id_label = wx.StaticText(panel, label="LCSC / JLCPCB ID:")
        self.lcsc_id_ctrl = wx.TextCtrl(panel, size=(200, -1))
        self.lcsc_id_ctrl.SetHint("e.g. C2040")
        id_sizer.Add(id_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        id_sizer.Add(self.lcsc_id_ctrl, 1, wx.EXPAND)
        root.Add(id_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # ── What to import ────────────────────────────────────────────
        import_box = wx.StaticBox(panel, label="What to import")
        import_sizer = wx.StaticBoxSizer(import_box, wx.VERTICAL)

        self.full_cb = wx.CheckBox(panel, label="Full  (Symbol + Footprint + 3D Model)")
        self.symbol_cb = wx.CheckBox(panel, label="Symbol")
        self.footprint_cb = wx.CheckBox(panel, label="Footprint")
        self.model_3d_cb = wx.CheckBox(panel, label="3D Model")

        # Start with "Full" checked
        for cb in (self.full_cb, self.symbol_cb, self.footprint_cb, self.model_3d_cb):
            cb.SetValue(True)

        import_sizer.Add(self.full_cb, 0, wx.ALL, 4)

        # Indented individual options
        sub_sizer = wx.BoxSizer(wx.VERTICAL)
        for cb in (self.symbol_cb, self.footprint_cb, self.model_3d_cb):
            sub_sizer.Add(cb, 0, wx.BOTTOM, 2)
        import_sizer.Add(sub_sizer, 0, wx.LEFT | wx.BOTTOM, 24)

        root.Add(import_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # ── Output path ───────────────────────────────────────────────
        out_box = wx.StaticBox(panel, label="Output Library")
        out_sizer = wx.StaticBoxSizer(out_box, wx.VERTICAL)

        folder_row = wx.BoxSizer(wx.HORIZONTAL)
        folder_label = wx.StaticText(panel, label="Folder:")
        self.folder_ctrl = wx.TextCtrl(panel, value=_DEFAULT_OUTPUT)
        self.browse_btn = wx.Button(panel, label="Browse…")
        folder_row.Add(folder_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        folder_row.Add(self.folder_ctrl, 1, wx.EXPAND | wx.RIGHT, 8)
        folder_row.Add(self.browse_btn, 0)
        out_sizer.Add(folder_row, 0, wx.EXPAND | wx.ALL, 4)

        libname_row = wx.BoxSizer(wx.HORIZONTAL)
        libname_label = wx.StaticText(panel, label="Library name:")
        self.libname_ctrl = wx.TextCtrl(panel, value="easyeda2kicad")
        libname_row.Add(libname_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        libname_row.Add(self.libname_ctrl, 1, wx.EXPAND)
        out_sizer.Add(libname_row, 0, wx.EXPAND | wx.ALL, 4)

        root.Add(out_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # ── Options ───────────────────────────────────────────────────
        opt_box = wx.StaticBox(panel, label="Options")
        opt_sizer = wx.StaticBoxSizer(opt_box, wx.VERTICAL)
        self.overwrite_cb = wx.CheckBox(panel, label="Overwrite existing component")
        opt_sizer.Add(self.overwrite_cb, 0, wx.ALL, 4)
        root.Add(opt_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # ── Import button ─────────────────────────────────────────────
        self.import_btn = wx.Button(panel, label="Import")
        font = self.import_btn.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.import_btn.SetFont(font)
        root.Add(self.import_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # ── Log ───────────────────────────────────────────────────────
        log_box = wx.StaticBox(panel, label="Log")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log_ctrl = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
            size=(-1, 120),
        )
        log_font = wx.Font(
            9,
            wx.FONTFAMILY_TELETYPE,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL,
        )
        self.log_ctrl.SetFont(log_font)
        log_sizer.Add(self.log_ctrl, 1, wx.EXPAND | wx.ALL, 4)
        root.Add(log_sizer, 1, wx.EXPAND | wx.ALL, 8)

        # ── Close button ──────────────────────────────────────────────
        close_btn = wx.Button(panel, wx.ID_CLOSE, label="Close")
        root.Add(close_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        panel.SetSizer(root)
        root.Fit(self)

        # Bind events
        self.full_cb.Bind(wx.EVT_CHECKBOX, self._on_full_changed)
        for cb in (self.symbol_cb, self.footprint_cb, self.model_3d_cb):
            cb.Bind(wx.EVT_CHECKBOX, self._on_individual_changed)
        self.browse_btn.Bind(wx.EVT_BUTTON, self._on_browse)
        self.import_btn.Bind(wx.EVT_BUTTON, self._on_import)
        close_btn.Bind(wx.EVT_BUTTON, lambda _e: self.EndModal(wx.ID_CLOSE))

        # Attach logging handler
        self._log_handler = _TextCtrlLogHandler(self.log_ctrl)
        self._log_handler.setFormatter(logging.Formatter("%(levelname)s – %(message)s"))
        logging.getLogger().addHandler(self._log_handler)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_full_changed(self, _event: wx.CommandEvent) -> None:
        checked = self.full_cb.GetValue()
        for cb in (self.symbol_cb, self.footprint_cb, self.model_3d_cb):
            cb.SetValue(checked)

    def _on_individual_changed(self, _event: wx.CommandEvent) -> None:
        all_on = all(
            cb.GetValue()
            for cb in (self.symbol_cb, self.footprint_cb, self.model_3d_cb)
        )
        self.full_cb.SetValue(all_on)

    def _on_browse(self, _event: wx.CommandEvent) -> None:
        with wx.DirDialog(
            self,
            "Choose the output library folder",
            defaultPath=self.folder_ctrl.GetValue(),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.folder_ctrl.SetValue(dlg.GetPath())

    def _on_import(self, _event: wx.CommandEvent) -> None:
        lcsc_id = self.lcsc_id_ctrl.GetValue().strip()

        if not lcsc_id:
            wx.MessageBox(
                "Please enter a LCSC / JLCPCB component ID.",
                "Missing ID",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        # easyeda2kicad requires all LCSC/JLCPCB component IDs to start with 'C'
        # (e.g. C2040, C294018). This is a hard requirement of the upstream tool.
        if not lcsc_id.upper().startswith("C"):
            wx.MessageBox(
                f"Component ID '{lcsc_id}' should start with 'C' (e.g. C2040).",
                "Invalid ID",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        do_symbol = self.symbol_cb.GetValue()
        do_footprint = self.footprint_cb.GetValue()
        do_3d = self.model_3d_cb.GetValue()

        if not any((do_symbol, do_footprint, do_3d)):
            wx.MessageBox(
                "Please select at least one item to import\n"
                "(Symbol, Footprint, or 3D Model).",
                "Nothing selected",
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        folder = self.folder_ctrl.GetValue().strip()
        lib_name = self.libname_ctrl.GetValue().strip() or "easyeda2kicad"
        overwrite = self.overwrite_cb.GetValue()

        self.import_btn.Disable()
        self.log_ctrl.Clear()
        self._log(f"Starting import of component {lcsc_id} …")

        thread = threading.Thread(
            target=self._run_import,
            args=(lcsc_id, do_symbol, do_footprint, do_3d, overwrite, folder, lib_name),
            daemon=True,
        )
        thread.start()

    # ------------------------------------------------------------------
    # Import logic (runs in a background thread)
    # ------------------------------------------------------------------

    def _run_import(
        self,
        lcsc_id: str,
        do_symbol: bool,
        do_footprint: bool,
        do_3d: bool,
        overwrite: bool,
        folder: str,
        lib_name: str,
    ) -> None:
        try:
            output_path = str(Path(folder) / lib_name)
            python_exe = self._python_executable

            cmd: list[str] = [
                python_exe,
                "-m",
                "easyeda2kicad",
                f"--lcsc_id={lcsc_id}",
                f"--output={output_path}",
            ]

            if do_symbol:
                cmd.append("--symbol")
            if do_footprint:
                cmd.append("--footprint")
            if do_3d:
                cmd.append("--3d")
            if overwrite:
                cmd.append("--overwrite")

            self._log(f"Running: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            assert process.stdout is not None
            for line in process.stdout:
                stripped = line.rstrip()
                if stripped:
                    wx.CallAfter(self._log, stripped)

            process.wait()

            if process.returncode == 0:
                wx.CallAfter(
                    self._log,
                    f"✓ Successfully imported {lcsc_id}  →  {output_path}",
                    colour=wx.Colour(0, 140, 0),
                )
            else:
                wx.CallAfter(
                    self._log,
                    f"✗ Import failed for {lcsc_id} (exit code {process.returncode}).",
                    colour=wx.Colour(200, 0, 0),
                )

        except FileNotFoundError:
            wx.CallAfter(
                self._log,
                "easyeda2kicad is not installed or not accessible via the current "
                f"Python interpreter ({python_exe}).\n"
                "Try restarting KiCad after installing:  pip install easyeda2kicad",
                colour=wx.Colour(200, 0, 0),
            )
        except Exception as exc:  # pragma: no cover
            wx.CallAfter(self._log, f"Unexpected error: {exc}", colour=wx.Colour(200, 0, 0))
        finally:
            wx.CallAfter(self.import_btn.Enable)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str, colour: wx.Colour | None = None) -> None:
        if colour is not None:
            self.log_ctrl.SetDefaultStyle(wx.TextAttr(colour))
        self.log_ctrl.AppendText(msg + "\n")
        if colour is not None:
            self.log_ctrl.SetDefaultStyle(wx.TextAttr(wx.BLACK))

    def Destroy(self) -> bool:  # noqa: N802
        """Clean up the logging handler when the dialog is destroyed."""
        if self._log_handler is not None:
            logging.getLogger().removeHandler(self._log_handler)
            self._log_handler = None
        return super().Destroy()
