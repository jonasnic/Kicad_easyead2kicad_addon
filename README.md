# EasyEDA to KiCad – KiCad Addon

A **KiCad Plugin and Content Manager (PCM) addon** that lets you import any component from [LCSC](https://www.lcsc.com/) / [JLCPCB](https://jlcpcb.com/) directly into your KiCad library.

Just paste the component ID (e.g. `C294018`) and the plugin downloads and adds the **schematic symbol**, **PCB footprint**, and **3D model** in one click.

Powered by the open-source [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py) project, which is installed automatically on first use.

---

## Features

- Paste a LCSC / JLCPCB component ID (e.g. `C2040`, `C294018`) and click **Import**
- Checkboxes to choose what to import: **Symbol**, **Footprint**, **3D Model** — or tick **Full** to get all three
- Configurable output library folder and library name
- **Overwrite** option to update an already-imported component
- Coloured log output for easy troubleshooting
- **Self-contained**: automatically installs `easyeda2kicad` via pip on first launch if not already present

---

## Installation

### Via KiCad Plugin and Content Manager (recommended)

The repository/feed file (`repository.json`) is separate from the downloadable plugin ZIP payload.

1. Open KiCad → **Tools → Plugin and Content Manager**
2. Add a custom repository URL and use:
   - `https://raw.githubusercontent.com/jonasnic/Kicad_easyead2kicad_addon/main/repository.json`
3. Install **EasyEDA to KiCad Importer** from that repository feed, *or*
4. Click **Install from File…** and select the `.zip` release package

### Manual installation

1. Clone or download this repository
2. Copy the entire folder into your KiCad plugins directory:
   - **Windows**: `%APPDATA%\kicad\<version>\scripting\plugins\`
   - **Linux**: `~/.local/share/kicad/<version>/scripting/plugins/`
   - **macOS**: `~/Library/Preferences/kicad/<version>/scripting/plugins/`
3. Restart KiCad

---

## First-time use

The plugin will automatically install `easyeda2kicad` using pip and KiCad's bundled Python interpreter the first time you run it. An internet connection is required.

You can also install it manually beforehand:

```bash
pip install easyeda2kicad
```

On Windows, use the **KiCad Command Prompt** (search in the Start Menu):

```
pip install easyeda2kicad
```

---

## Usage

1. Open KiCad **PCB Editor** (or **Schematic Editor**)
2. Click **Tools → External Plugins → EasyEDA to KiCad**  
   (or use the toolbar button if visible)
3. Enter a LCSC / JLCPCB component ID in the **Component ID** field
4. Select what you want to import using the checkboxes
5. Set the output folder and library name (defaults work out of the box)
6. Click **Import**

The imported library files will be placed in:

| Type | File |
|------|------|
| Symbol | `<folder>/<lib_name>.kicad_sym` |
| Footprint | `<folder>/<lib_name>.pretty/` |
| 3D Model | `<folder>/<lib_name>.3dshapes/` |

After importing, add the library to KiCad via **Preferences → Manage Symbol Libraries** (and/or **Manage Footprint Libraries**).

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
├── repository.json            # PCM repository/feed entrypoint
├── metadata.json              # PCM package metadata
├── plugins/
│   ├── __init__.py            # Plugin registration
│   ├── action_easyeda2kicad.py  # KiCad ActionPlugin class
│   └── dialog_easyeda2kicad.py  # wxPython import dialog
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

- Keep using the repository feed URL above in KiCad PCM.
- For each release, upload a package asset named `easyeda2kicad_addon-v<version>.zip`.
- Ensure each `download_url` in `metadata.json` / `repository.json` points to the matching GitHub Release asset.
