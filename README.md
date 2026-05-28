# EasyEDA to KiCad – KiCad Addon

A **KiCad Plugin and Content Manager (PCM) addon** that lets you import any component from [LCSC](https://www.lcsc.com/) / [JLCPCB](https://jlcpcb.com/) directly into your KiCad library.

Just paste the component ID (e.g. `C294018`) and the plugin downloads and adds the **schematic symbol**, **PCB footprint**, and **3D model** in one click.

Powered by the open-source [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) project, which is installed automatically on first use.

---

## Features

- Paste a LCSC / JLCPCB component ID (e.g. `C2040`, `C294018`) and click **Import**
- Checkboxes to choose what to import: **Symbol**, **Footprint**, **3D Model** — or tick **Full** to get all three
- Configurable output library folder and library name
- Quick path buttons for **Global** and **Project** output locations
- Supports path variables in folder input (`${KIPRJMOD}`, `$(KIPRJMOD)`, `%USERPROFILE%`)
- Optional auto-create for missing output folders (enabled by default)
- **Overwrite** option to update an already-imported component
- Coloured log output for easy troubleshooting
- **Self-contained**: automatically installs `easyeda2kicad` via pip on first launch if not already present

---

## Installation

### Via KiCad Plugin and Content Manager (recommended)

This plugin is distributed through the **[JonasNic-Kicad-plugins](https://github.com/jonasnic/Kicad-plugins)** PCM repository, which acts as a central index for all jonasnic KiCad addons.

1. Open KiCad → **Tools → Plugin and Content Manager**
2. Click **Manage** next to *Manage Custom Repositories*, then **+** (Add) and paste:
   ```
   https://raw.githubusercontent.com/jonasnic/Kicad-plugins/main/repository.json
   ```
3. Click **OK**, then **Refresh**
4. Install **EasyEDA to KiCad Importer** from the list, *or*
5. Click **Install from File…** and select the `.zip` release package

### Manual installation

1. Clone or download this repository
2. Copy/link the entire folder into your KiCad plugins directory:
   - **Windows (common)**: `%APPDATA%\kicad\<version>\scripting\plugins\`
   - **Windows (KiCad 10 user setup seen in this project)**: `Documents\KiCad\10.0\3rdparty\plugins\`
   - **Linux**: `~/.local/share/kicad/<version>/scripting/plugins/`
   - **macOS**: `~/Library/Preferences/kicad/<version>/scripting/plugins/`
3. Restart KiCad

Tip: for local development, use a directory junction/symlink so KiCad loads your
working tree directly instead of copying files each time.

---

## First-time use

The plugin will automatically install `easyeda2kicad` the first time you run it.
An internet connection is required on first launch.

---

## Usage

1. Open KiCad **PCB Editor**
2. Click **Tools → External Plugins → EasyEDA to KiCad**  
   (or use the toolbar button if visible)
3. Enter a LCSC / JLCPCB component ID in the **Component ID** field
4. Select what you want to import using the checkboxes
5. Set the output folder and library name:
   - use **Use Global** for a shared user library folder
   - use **Use Project** for project-local output (when project path is detected)
   - keep **Create missing output folder(s)** enabled to auto-create folders
6. Click **Import**

Note for KiCad 10: this plugin is currently verified to appear in **PCB Editor**.
Some installations do not expose the same External Plugins path in Schematic Editor.

The imported library files will be placed in:

| Type | File |
|------|------|
| Symbol | `<folder>/<lib_name>.kicad_sym` |
| Footprint | `<folder>/<lib_name>.pretty/` |
| 3D Model | `<folder>/<lib_name>.3dshapes/` |

After importing, add the library to KiCad via **Preferences → Manage Symbol Libraries** (and/or **Manage Footprint Libraries**).

### Schematic Editor workaround (netlist/BOM launcher)

If the plugin does not appear in **Schematic Editor → Tools → External Plugins**,
you can launch the same importer dialog via Eeschema script hooks.

Use the script:

`easyeda2kicad_schematic_launcher.py`

This file is included in the addon root and in packaged releases.

In Eeschema, add/select this script in the netlist/BOM script tool, then run it.
The netlist/BOM input/output arguments are ignored by this launcher; it only
opens the EasyEDA importer dialog.

---

## Adding the default library to KiCad

Run at least one import first to create the library files, then:

1. **Preferences → Configure Paths** → add `EASYEDA2KICAD` pointing to your output folder
2. **Preferences → Manage Symbol Libraries** → add `${EASYEDA2KICAD}/easyeda2kicad.kicad_sym`
3. **Preferences → Manage Footprint Libraries** → add `${EASYEDA2KICAD}/easyeda2kicad.pretty`

---

## Project structure

```
Kicad_easyead2kicad_addon/
├── __init__.py                # Package bootstrap for KiCad discovery
├── easyeda2kicad_plugin.py    # Main ActionPlugin entrypoint (PCB Editor)
├── easyeda2kicad_schematic_launcher.py  # Eeschema netlist/BOM launcher workaround
├── metadata.json              # PCM package metadata
├── plugins/
│   ├── __init__.py            # Plugin package exports
│   ├── action_easyeda2kicad.py  # KiCad ActionPlugin class
│   └── dialog_easyeda2kicad.py  # wxPython import dialog
├── scripts/
│   ├── New-PcmRelease.ps1     # Parameterized release builder/updater
│   └── Release.ps1            # Simple no-parameter wrapper (edit values in file)
└── resources/
    ├── icon.png               # Toolbar/menu icon (32×32)
    └── generate_icon.py       # Script to regenerate icon.png (requires Pillow)
```

---

## Credits

- Component data powered by [EasyEDA](https://easyeda.com/) / [LCSC](https://www.lcsc.com/)
- Conversion library: [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py) by uPesy

## License

MIT

---

## PCM publishing notes

- The PCM repository index lives at [jonasnic/Kicad-plugins](https://github.com/jonasnic/Kicad-plugins). That is the URL users add to KiCad PCM.
- For each release, upload a package asset named `easyeda2kicad_addon-v<version>.zip` to this repo's GitHub Releases.
- Update `metadata.json` here with the new version and `download_url`, then update the `sha256` and `update_timestamp` in `Kicad-plugins/repository.json` to match.
  - (Get-FileHash .\metadata.json -Algorithm SHA256).Hash.ToLower()
  - [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

### Automated release helper (PowerShell)

This repo includes a release helper script at `scripts/New-PcmRelease.ps1`.

What it does:
- Creates a PCM-safe ZIP payload in `dist/easyeda2kicad_addon-v<version>.zip`
- Uses a temporary staging folder in your OS temp directory and cleans it automatically
- Packages only runtime files (`easyeda2kicad_plugin.py`, `plugins/`, `resources/`, optional `README.md`)
- Removes `__pycache__`, `*.pyc`, `*.pyo` from the staged package
- Updates `metadata.json` with the provided version and release asset `download_url`
- Optionally updates `repository.json` (`sha256` + `update_timestamp`)
- Prints `DOWNLOAD_SHA256`, `DOWNLOAD_SIZE`, `INSTALL_SIZE`, etc. for CI usage

Simple local workflow script:

- `scripts/Release.ps1`
- Edit `Version`, `ReleaseTag` and `RepositoryJsonPath` inside the file.
- Run:

```powershell
pwsh -File .\scripts\Release.ps1
```

Example usage:

```powershell
pwsh -File .\scripts\New-PcmRelease.ps1 -Version 0.1.2 `
   -GithubRepo jonasnic/Kicad_easyead2kicad_addon `
   -RepositoryJsonPath "..\MyKicadPlugins\repository.json"
```

After running:
1. Upload `dist/easyeda2kicad_addon-v<version>.zip` as a GitHub Release asset under tag `v<version>`.
2. Commit updated `metadata.json` (and `repository.json` if you passed `-RepositoryJsonPath`).