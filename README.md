# 🚀 KiCad Project Localizer

> Make your hardware projects truly portable — and Git-ready. ✨

> ⚠️ **WARNING — Vibes ahead**
>
> This script was purely vibe coded, I looked at what it does for maybe 30 seconds. Please make sure you trust it there's a non zero chance it will blow up and do something unexpected.
>
> - Make sure you have backups
> - Even this readme was generated
>
> I would love some help de-slopifying the code! And if you find any problems please open an issue.

Tired of cloning a KiCad repo only to find 3D models or custom footprints missing because they pointed to an absolute path on someone else's machine? This script acts like a Project Janitor: it deep-scans your `.kicad_pcb`, finds external dependencies, and pulls them into your project using relative pathing (`${KIPRJMOD}`).

## ✨ Key Features

- 🔍 **Zero-Config Auto-Discovery** — Finds KiCad 9 third-party folders on Linux, Windows, and macOS.
- 📦 **Total Asset Sync** — Collects 3D models (`.step`, `.stp`, `.wrl`), symbols (`.kicad_sym`), and footprints (`.pretty`).
- 🧹 **Project Root Janitor** — Moves loose assets into a tidy `local_libs/` inside the project.
- 🔗 **Dynamic Table Injection** — Updates `sym-lib-table` and `fp-lib-table` to point to the local copies.
- 🌐 **Cross-Platform Safe** — Handles case-sensitivity (Linux) and Windows path quirks.

## ⚙️ Quick Start

### Prerequisites

You need Python 3 and a friendly output renderer:

```bash
pip install rich
```

### Run the Localizer

Point the script at your project folder:

```bash
python kicad_localize.py ./my_project_folder
```

### Deep Search (Optional)

If you keep libraries in a non-standard location (shared drives, Downloads, etc.), use `-s` to add extra search paths:

```bash
python kicad_localize.py bms_okmr -s ~/Downloads/Custom_Parts
```

## 📁 Resulting Project Layout

After running, your repo becomes self-contained and portable. Example:

- `local_libs/` — all collected project assets
- `local_libs/3d/` — `.step` / `.stp` 3D models
- `sym-lib-table` — rewritten to reference `./local_libs`
- `fp-lib-table` — rewritten to reference `./local_libs`

This makes the project safe to zip, move, or push to Git — it will open correctly on another machine.

## 🧠 How It Works (Short)

- 🔎 **Environment Scan**: Reads `kicad_common.json` to resolve variables like `${KICAD_3RD_PARTY}`.
- 🕵️ **Asset Hunting**: Uses recursive globbing (rglob) so even deeply nested files are found.
- 🔁 **Refactoring**: Rewrites absolute paths in `.kicad_pcb` to relative references such as `${KIPRJMOD}/local_libs/3d/filename.step`.

> 💡 Pro tip: Add `local_libs/` to your repository so clones include the exact parts you used. Avoid committing your global KiCad library paths.

---

## ✅ Want more?

- Add a `requirements.txt` for reproducible installs.
- I can add a minimal example project to test the script end-to-end.
- I can also add a one-line Git pre-commit check to ensure `local_libs/` is present.

If you'd like any of the above, tell me which and I'll add it.
