import os, shutil, re, argparse, platform, json
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.status import Status
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None

def get_kicad_data_paths():
    """Automatically finds the 3rdparty folder based on OS."""
    system = platform.system()
    home = Path.home()
    paths = []
    
    # Standard KiCad 9 3rd-party locations
    if system == "Linux":
        paths.append(home / ".local/share/kicad/9.0/3rdparty")
    elif system == "Windows":
        paths.append(home / "Documents/KiCad/9.0/3rdparty")
    elif system == "Darwin": # macOS
        paths.append(home / "Library/Application Support/kicad/9.0/3rdparty")
        
    return [p for p in paths if p.exists()]

def update_lib_table(root, table_name, lib_type, lib_path):
    table_file = root / table_name
    lib_nick = lib_path.stem
    ext = ".kicad_sym" if lib_type == "sym" else ".pretty"
    uri = f"${{KIPRJMOD}}/local_libs/{lib_nick}{ext}"
    
    if not table_file.exists():
        table_file.write_text(f"({lib_type}_lib_table\n)")
    
    content = table_file.read_text()
    # Update or Add
    if f'(name "{lib_nick}")' not in content:
        entry = f'  (lib (name "{lib_nick}")(type "KiCad")(uri "{uri}")(options "")(descr ""))\n'
        content = content.rsplit(")", 1)[0] + entry + ")"
        table_file.write_text(content)
        return True
    return False

def run_sync(project_path, user_search_dirs):
    root = Path(project_path).resolve()
    pcb_file = next(root.glob("*.kicad_pcb"), None)
    if not pcb_file: return None

    local_libs = root / "local_libs"
    local_3d = local_libs / "3d"
    local_libs.mkdir(parents=True, exist_ok=True)
    local_3d.mkdir(parents=True, exist_ok=True)

    # Combined search: User provided + Auto-discovered KiCad 9 paths
    search_dirs = list(set([Path(d).expanduser() for d in user_search_dirs] + get_kicad_data_paths()))
    
    content = pcb_file.read_text(encoding='utf-8')
    stats = {"3d": 0, "libs": 0, "cleaned": 0}

    # --- 1. CLEANUP ROOT & SYNC EXTERNAL LIBS ---
    # Check root for loose libs first
    for root_item in list(root.iterdir()):
        if root_item.name == "local_libs": continue
        
        # Move loose .kicad_sym or .pretty from root to local_libs
        if root_item.suffix == ".kicad_sym" or root_item.suffix == ".pretty":
            dest = local_libs / root_item.name
            if dest != root_item:
                if dest.exists(): 
                    if dest.is_dir(): shutil.rmtree(dest)
                    else: dest.unlink()
                shutil.move(str(root_item), str(dest))
                stats["cleaned"] += 1
            update_lib_table(root, "sym-lib-table" if root_item.suffix == ".kicad_sym" else "fp-lib-table", 
                             "sym" if root_item.suffix == ".kicad_sym" else "fp", dest)
            stats["libs"] += 1

    # Now search external directories
    for s_dir in search_dirs:
        for sym in s_dir.rglob("*.kicad_sym"):
            shutil.copy2(sym, local_libs / sym.name)
            if update_lib_table(root, "sym-lib-table", "sym", sym): stats["libs"] += 1
        for pretty in s_dir.rglob("*.pretty"):
            dest = local_libs / pretty.name
            if dest.exists(): shutil.rmtree(dest)
            shutil.copytree(pretty, dest)
            if update_lib_table(root, "fp-lib-table", "fp", pretty): stats["libs"] += 1

    # --- 2. SYNC 3D MODELS & CLEAN ROOT 3D ---
    matches = list(set(re.findall(r'\(model\s+"([^"]+)"', content)))
    for raw_path in matches:
        if raw_path.startswith("${KIPRJMOD}"): continue
        
        fname = Path(raw_path.replace("\\", "/")).name
        source = None

        # Check if the file is sitting loose in the project root
        if (root / fname).exists():
            source = root / fname
            # Move it to local_libs/3d
            dest = local_3d / fname
            shutil.move(str(source), str(dest))
            stats["cleaned"] += 1
            source = dest
        else:
            # Hunt externally
            for s_dir in search_dirs:
                candidate = next(s_dir.rglob(fname), None)
                if candidate:
                    shutil.copy2(candidate, local_3d / fname)
                    source = local_3d / fname
                    break

        if source:
            content = content.replace(f'"{raw_path}"', f'"${{KIPRJMOD}}/local_libs/3d/{fname}"')
            stats["3d"] += 1

    pcb_file.write_text(content)
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Project folder")
    parser.add_argument("-s", "--search", action="append", default=[], help="Extra search folders")
    args = parser.parse_args()

    if RICH_AVAILABLE:
        console.print(Panel.fit("🚀 [bold blue]KiCad Smart Localizer[/bold blue]", border_style="cyan"))
        with Status("[bold yellow]Cleaning root and syncing assets...", spinner="bouncingBar"):
            res = run_sync(args.path, args.search)
    else:
        res = run_sync(args.path, args.search)

    if res:
        table = Table(title="Localization & Cleanup Results")
        table.add_column("Action", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_row("Assets Localized (3D/Lib)", str(res["3d"] + res["libs"]))
        table.add_row("Root Files Moved to Libs", str(res["cleaned"]))
        console.print(table)
