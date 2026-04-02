#!/usr/bin/env python3
"""
BicameriS Launcher - Professional TUI
=====================================
Diadikos & Palladion - By Hope 'n Mind

Industrial-grade launcher for BicameriS cognitive kernel.

Usage:
    python launcher.py              # Interactive TUI menu
    python launcher.py --start       # Start server directly
    python launcher.py --scan        # Scan models only
    python launcher.py --help        # Show help
"""

import sys
import os
import json
import time
import re
import copy
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# ============================================
# CONSTANTS
# ============================================

VERSION = "1.0.0.6a"
CONFIG_FILE = BASE_DIR / "storage" / "config" / "launcher_config.json"

HEMISPHERE_PARAMS = {
    "temperature": {"min": 0.0, "max": 2.0, "step": 0.1, "default": 0.7, "desc": "Creativite (0=factuel, 2=aleatoire)"},
    "top_p": {"min": 0.1, "max": 1.0, "step": 0.05, "default": 0.9, "desc": "Nucleus sampling"},
    "repeat_penalty": {"min": 1.0, "max": 1.5, "step": 0.05, "default": 1.1, "desc": "Penalite repetition"},
    "n_ctx": {"values": [2048, 4096, 8192, 16384, 32768, 65536], "default": 16384, "desc": "Taille contexte"},
    "max_tokens": {"values": [256, 512, 1024, 2048, 4096], "default": 2048, "desc": "Tokens max par reponse"},
    "n_gpu_layers": {"values": [0, 10, 20, 50, 100, -1], "default": -1, "desc": "Couches GPU (-1=tout)"},
}


# ============================================
# MODEL NAME RATIONALIZATION
# ============================================

def rationalize_model_name(filename: str) -> dict:
    name = filename.replace('.gguf', '').replace('.GGUF', '')
    
    quant = "Unknown"
    quant_match = re.search(r'[Qq](\d+)[_\s]*[KkSs]?[_\s]*[MmLl]?', name)
    if quant_match:
        quant = quant_match.group(0)
        name = name.replace(quant, '').strip('_- ')
    else:
        for pat in [r'([fF]\d+)', r'(GPTQ|AWQ|GGML)']:
            m = re.search(pat, name)
            if m:
                quant = m.group(0)
                name = name.replace(quant, '').strip('_- ')
                break
    
    size = "?"
    size_match = re.search(r'(\d+\.?\d*)[bB]', name)
    if size_match:
        size = f"{size_match.group(1)}B"
    
    context = ""
    ctx_match = re.search(r'(\d+)[kK]', name)
    if ctx_match:
        context = f"{ctx_match.group(1)}K"
    
    name = re.sub(r'^[A-Za-z]+_', '', name)
    name = re.sub(r'[-_]\d+[bB].*', '', name)
    name = re.sub(r'[-_][Qq]\d+.*', '', name)
    name = re.sub(r'[-_]\d+[kK].*', '', name)
    name = name.replace('_', ' ').replace('-', ' ').strip()
    
    if len(name) < 2:
        name = filename.split('_')[0] if '_' in filename else filename.split('-')[0]
    
    return {
        "name": name,
        "size": size,
        "quant": quant,
        "context": context,
        "path": "",
        "raw": filename,
        "size_mb": 0
    }


def format_model_short(info: dict) -> str:
    parts = [info["name"]]
    if info["size"] != "?":
        parts.append(info["size"])
    if info["context"]:
        parts.append(info["context"])
    if info["quant"] != "Unknown":
        parts.append(info["quant"])
    return " | ".join(parts)


# ============================================
# CONFIGURATION
# ============================================

DEFAULT_CONFIG = {
    "server": {"host": "0.0.0.0", "port": 8000, "reload": False, "log_level": "info"},
    "models": {
        "left_hemisphere": {
            "name": "", "path": "",
            "temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.1,
            "n_ctx": 16384, "max_tokens": 2048, "n_gpu_layers": -1
        },
        "right_hemisphere": {
            "name": "", "path": "",
            "temperature": 1.2, "top_p": 0.9, "repeat_penalty": 1.0,
            "n_ctx": 4096, "max_tokens": 512, "n_gpu_layers": -1
        }
    },
    "woven_memory": {
        "enabled": False,
        "qdrant_url": "http://localhost:6333",
        "enable_vector": True,
        "enable_concepts": True,
        "enable_temporal": True,
        "decay_rate": 0.95,
        "vector_size": 384,
        "auto_learn": True,
        "warning_on_enable": "L'activation du Woven Memory permet une recherche contextuelle plus puissante mais augmente la dépendance aux outils externes (Qdrant)."
    },
    "lab": {
        "enabled": True,
        "modules": {
            "research": {
                "enabled": True,
                "name": "Research",
                "description": "Recherche scientifique et génération d'idées",
                "icon": "🔬",
                "hemisphere": "both",
                "temperature": 0.8
            },
            "python": {
                "enabled": True,
                "name": "Python Expert",
                "description": "Expert en code Python",
                "icon": "🐍",
                "hemisphere": "left",
                "temperature": 0.3
            },
            "uiux": {
                "enabled": True,
                "name": "UI/UX Designer",
                "description": "Design d'interfaces et expériences utilisateur",
                "icon": "🎨",
                "hemisphere": "right",
                "temperature": 1.0
            },
            "multi": {
                "enabled": True,
                "name": "Multi Expert",
                "description": "Polyvalent - combinaison de tous les modules",
                "icon": "🌐",
                "hemisphere": "both",
                "temperature": 0.7
            }
        },
        "workspace_base": "storage/lab/workspaces",
        "auto_save": True,
        "auto_save_interval": 30
    },
    "presets": {
        "balanced": {"left_temp": 0.7, "right_temp": 1.2, "left_ctx": 16384, "right_ctx": 4096},
        "creative": {"left_temp": 1.0, "right_temp": 1.5, "left_ctx": 8192, "right_ctx": 8192},
        "analytical": {"left_temp": 0.3, "right_temp": 0.8, "left_ctx": 32768, "right_ctx": 4096},
        "dreamer": {"left_temp": 1.2, "right_temp": 1.8, "left_ctx": 4096, "right_ctx": 8192}
    }
}


class Config:
    def __init__(self):
        self.data = {}
        self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = DEFAULT_CONFIG.copy()
        else:
            self.data = copy.deepcopy(DEFAULT_CONFIG)
    
    def save(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def get(self, path: str, default=None):
        keys = path.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
                if val is None:
                    return default
            else:
                return default
        return val
    
    def set(self, path: str, value):
        keys = path.split(".")
        d = self.data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value


# ============================================
# MODEL SCANNER
# ============================================

class Scanner:
    def __init__(self):
        self.models = []
        self.blacklist = {"$Recycle.Bin", "System Volume Information", "Windows",
                          "Program Files", "ProgramData", ".git", "__pycache__"}
    
    def scan(self, root_path: str) -> List[dict]:
        self.models = []
        root = Path(root_path)
        
        if not root.exists():
            return []
        
        print(f"\n  [*] Scan en cours...")
        count = 0
        
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in self.blacklist]
            
            for fn in filenames:
                if fn.lower().endswith('.gguf'):
                    try:
                        fp = os.path.join(dirpath, fn)
                        st = os.stat(fp)
                        info = rationalize_model_name(fn)
                        info["path"] = fp
                        info["size_mb"] = round(st.st_size / (1024**2), 1)
                        self.models.append(info)
                        count += 1
                        if count % 10 == 0:
                            print(f"    ... {count} trouves", end='\r')
                    except (OSError, PermissionError):
                        continue
        
        self.models.sort(key=lambda x: x["size_mb"])
        print(f"  [OK] {count} modeles trouves (tris par taille)")
        return self.models


# ============================================
# TUI HELPERS
# ============================================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause(msg="Appuyez sur Entree pour continuer"):
    input(f"\n  {msg}")


def header():
    print()
    print("    o===================================================================o")
    print("    |                                                                   |")
    print("    | ██████╗ ██╗ ██████╗ █████╗ ███╗   ███╗███████╗██████╗ ██╗███████╗ |")
    print("    | ██╔══██╗██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔══██╗██║██╔════╝ |")
    print("    | ██████╔╝██║██║     ███████║██╔████╔██║█████╗  ██████╔╝██║███████╗ |")
    print("    | ██╔══██╗██║██║     ██╔══██║██║╚██╔╝██║██╔══╝  ██╔══██╗██║╚════██║ |")
    print("    | ██████╔╝██║╚██████╗██║  ██║██║ ╚═╝ ██║███████╗██║  ██║██║███████║ |")
    print("    | ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝ |")
    print("    |                                                                   |")
    print("    |                Diadikos & Palladion - By Hope 'n Mind             |")
    print("    o===================================================================o")
    print(f"                              v{VERSION:<10}")

    print()


def menu_box(items: List[tuple], title="MENU"):
    print(f"    +{'-' * 50}+")
    print(f"    |  {title:^48}  |")
    print(f"    +{'-' * 50}+")
    for key, desc in items:
        print(f"    |  [{key}] {desc:<45} |")
    print(f"    +{'-' * 50}+")


def get_choice(prompt="Choix", default="", allow_back=True):
    suffix = " [0=retour]" if allow_back else ""
    result = input(f"  {prompt}{suffix} [{default}]: ").strip()
    return result if result else default


def confirm(prompt="Confirmer") -> bool:
    r = input(f"  {prompt} [o/N]: ").strip().lower()
    return r in ('o', 'oui', 'y', 'yes')


# ============================================
# DISPLAY FUNCTIONS
# ============================================

def show_status(config: Config):
    left = config.get("models.left_hemisphere.name") or "Non configure"
    right = config.get("models.right_hemisphere.name") or "Non configure"
    left_path = config.get("models.left_hemisphere.path") or ""
    right_path = config.get("models.right_hemisphere.path") or ""
    
    print(f"    +-- Etat Actuel {'-' * 36}+")
    print(f"    | DIA [Gauche]: {left:<35} |")
    print(f"    | PAL [Droit]:  {right:<35} |")
    print(f"    +{'-' * 52}+")
    print()


# ============================================
# MENU: INFORMATION SYSTEME
# ============================================

def menu_system_info():
    clear()
    header()
    print("    [+] INFORMATIONS SYSTEME")
    print("    " + "-" * 50)
    
    try:
        import psutil
        
        cpu_count = psutil.cpu_count(logical=False) or 0
        cpu_threads = psutil.cpu_count(logical=True) or 0
        print(f"  CPU:   {cpu_count} coeurs / {cpu_threads} threads")
        
        ram = psutil.virtual_memory()
        print(f"  RAM:   {ram.total / (1024**3):.1f} Go total | {ram.available / (1024**3):.1f} Go libre")
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                for g in gpus:
                    print(f"  GPU:   {g.name} | {g.memoryTotal} Mo VRAM | {g.memoryFree} Mo libre")
            else:
                print("  GPU:   Aucune detectee")
        except:
            print("  GPU:   Non detecte")
        
        disk = psutil.disk_usage('/')
        print(f"  DISK:  {disk.total / (1024**3):.0f} Go | {disk.free / (1024**3):.0f} Go libre")
        
        vram_gb = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                vram_gb = gpus[0].memoryTotal / 1024
        except:
            pass
        
        print()
        print("    [RECOMMANDATIONS]")
        if vram_gb >= 16:
            print("  Modeles 14B-32B (full GPU)")
        elif vram_gb >= 10:
            print("  Modeles 7B-14B (partiel GPU)")
        elif vram_gb >= 6:
            print("  Modeles 3B-7B (quantizes)")
        else:
            print("  CPU uniquement recommande")
            
    except ImportError:
        print("  [!] psutil non installe")
    
    pause()


# ============================================
# MENU: SCANNER
# ============================================

def menu_scan(scanner: Scanner) -> List[dict]:
    clear()
    header()
    print("    [+] SCANNER DE MODELES")
    print("    " + "-" * 50)
    
    menu_box([
        ("1", "Scanner les chemins habituels"),
        ("2", "Choisir un dossier specifique"),
    ], "TYPE DE SCAN")
    print()
    
    choice = get_choice("Choix", "1")
    if choice == "0":
        return []
    
    if choice == "2":
        path = get_choice("Chemin du dossier", "", allow_back=True)
        if path == "0" or not path:
            return []
        if not os.path.exists(path):
            print(f"\n  [!] Le chemin n'existe pas: {path}")
            pause()
            return []
        scan_path = path
    else:
        username = os.environ.get("USERNAME", "user")
        common = [
            str(BASE_DIR / "models"),
            f"C:\\Users\\{username}\\.lmstudio\\models",
            f"C:\\Users\\{username}\\AppData\\Local\\.lmstudio\\models",
        ]
        scan_path = None
        for p in common:
            if os.path.exists(p):
                scan_path = p
                break
        
        if not scan_path:
            print("\n  [!] Aucun chemin habituel trouve")
            print("      Utilisez l'option 2 pour choisir un dossier")
            pause()
            return []
    
    models = scanner.scan(scan_path)
    
    if models:
        print()
        print(f"    [{len(models)} MODELES - Tries du plus petit au plus grand]")
        print("    " + "-" * 50)
        for i, m in enumerate(models[:30], 1):
            display = format_model_short(m)
            size_str = f"{m['size_mb']/1024:.1f} Go" if m['size_mb'] >= 1024 else f"{m['size_mb']:.0f} Mo"
            print(f"      {i:>3}. {display:<42} {size_str:>10}")
        if len(models) > 30:
            print(f"      ... et {len(models) - 30} autres")
    
    pause()
    return models


# ============================================
# MENU: SELECT MODEL
# ============================================

def menu_select_model(scanner: Scanner, config: Config, hemisphere: str):
    label = "DIA [Gauche - Logique]" if "left" in hemisphere else "PAL [Droit - Intuition]"
    
    while True:
        clear()
        header()
        print(f"    [+] SELECTION MODELE - {label}")
        print("    " + "-" * 50)
        
        models = scanner.models
        
        if not models:
            print("  [!] Aucun modele scanne")
            print("      Lancez d'abord un scan (option 2)")
            pause()
            return
        
        # Current selection
        current = config.get(f"models.{hemisphere}.name") or "Aucun"
        print(f"  Modele actuel: {current}")
        print()
        
        # Display models
        print("    Modeles disponibles:")
        for i, m in enumerate(models[:30], 1):
            display = format_model_short(m)
            size_str = f"{m['size_mb']/1024:.1f} Go" if m['size_mb'] >= 1024 else f"{m['size_mb']:.0f} Mo"
            print(f"      {i:>3}. {display:<42} {size_str:>10}")
        if len(models) > 30:
            print(f"      ... et {len(models) - 30} autres")
        
        print()
        choice = get_choice("Numero du modele", "0")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                config.set(f"models.{hemisphere}.path", selected["path"])
                config.set(f"models.{hemisphere}.name", selected["name"])
                config.save()
                print(f"\n  [OK] {format_model_short(selected)}")
                pause()
                return
            else:
                print("  [!] Numero invalide")
                time.sleep(1)
        except ValueError:
            print("  [!] Entree invalide")
            time.sleep(1)


# ============================================
# MENU: MODEL SETTINGS
# ============================================

def menu_model_settings(config: Config, hemisphere: str):
    label = "DIA [Gauche]" if "left" in hemisphere else "PAL [Droit]"
    model_name = config.get(f"models.{hemisphere}.name") or "Aucun"
    
    while True:
        clear()
        header()
        print(f"    [+] REGLAGES MODELE - {label}")
        print(f"    Modele: {model_name}")
        print("    " + "-" * 50)
        
        # Show current values
        print("    Parametres actuels:")
        items = []
        for param, spec in HEMISPHERE_PARAMS.items():
            current = config.get(f"models.{hemisphere}.{param}", spec.get("default"))
            items.append((param, current, spec))
        
        for i, (param, current, spec) in enumerate(items, 1):
            desc = spec["desc"]
            print(f"      {i}. {param:<20} = {current:<10} ({desc})")
        
        print()
        print("      0. Retour")
        print()
        
        choice = get_choice("Parametre a modifier", "0")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                param, current, spec = items[idx]
                
                if "values" in spec:
                    # Multiple choice
                    print(f"\n    Valeurs possibles pour {param}:")
                    for j, v in enumerate(spec["values"], 1):
                        marker = " <--" if v == current else ""
                        print(f"      {j}. {v}{marker}")
                    
                    vc = get_choice("Choix", str(spec["values"].index(current) + 1) if current in spec["values"] else "1")
                    if vc != "0":
                        try:
                            val_idx = int(vc) - 1
                            if 0 <= val_idx < len(spec["values"]):
                                new_val = spec["values"][val_idx]
                                config.set(f"models.{hemisphere}.{param}", new_val)
                                config.save()
                                print(f"  [OK] {param} = {new_val}")
                                time.sleep(0.5)
                        except:
                            pass
                else:
                    # Slider value
                    print(f"\n    {spec['desc']}")
                    print(f"    Plage: {spec['min']} - {spec['max']} (pas: {spec['step']})")
                    
                    nv = get_choice("Nouvelle valeur", str(current))
                    if nv != "0":
                        try:
                            new_val = float(nv)
                            new_val = max(spec["min"], min(spec["max"], new_val))
                            config.set(f"models.{hemisphere}.{param}", new_val)
                            config.save()
                            print(f"  [OK] {param} = {new_val}")
                            time.sleep(0.5)
                        except:
                            print("  [!] Valeur invalide")
                            time.sleep(1)
        except ValueError:
            pass


# ============================================
# MENU: PRESETS
# ============================================

def menu_presets(config: Config):
    while True:
        clear()
        header()
        print("    [+] PRESETS DE CONFIGURATION")
        print("    " + "-" * 50)
        
        presets = config.get("presets", {})
        
        menu_box([
            ("1", "Appliquer un preset"),
            ("2", "Voir les presets disponibles"),
        ], "PRESETS")
        print()
        
        choice = get_choice("Choix", "1")
        
        if choice == "0":
            return
        
        if choice == "2":
            print("\n    Presets disponibles:")
            for name, p in presets.items():
                print(f"      - {name}: DIA temp={p.get('left_temp','?')}, PAL temp={p.get('right_temp','?')}")
            pause()
            continue
        
        if choice == "1":
            print("\n    Presets disponibles:")
            preset_names = list(presets.keys())
            for i, name in enumerate(preset_names, 1):
                p = presets[name]
                print(f"      {i}. {name}: DIA={p.get('left_temp','?')}, PAL={p.get('right_temp','?')}")
            
            print()
            pc = get_choice("Numero du preset", "1")
            
            if pc == "0":
                continue
            
            try:
                pidx = int(pc) - 1
                if 0 <= pidx < len(preset_names):
                    name = preset_names[pidx]
                    p = presets[name]
                    config.set("models.left_hemisphere.temperature", p.get("left_temp", 0.7))
                    config.set("models.right_hemisphere.temperature", p.get("right_temp", 1.2))
                    config.set("models.left_hemisphere.n_ctx", p.get("left_ctx", 16384))
                    config.set("models.right_hemisphere.n_ctx", p.get("right_ctx", 4096))
                    config.save()
                    print(f"\n  [OK] Preset '{name}' applique")
                    pause()
            except:
                pass


# ============================================
# MENU: SERVER
# ============================================

def start_server(config: Config):
    clear()
    header()
    print("    [+] DEMARRAGE DU SERVEUR")
    print("    " + "-" * 50)
    
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8000)
    
    left_name = config.get("models.left_hemisphere.name") or "Non configure"
    right_name = config.get("models.right_hemisphere.name") or "Non configure"
    
    print(f"  DIA [Gauche]: {left_name}")
    print(f"  PAL [Droit]:  {right_name}")
    print()
    print(f"  Serveur: http://localhost:{port}")
    print(f"  Docs:    http://localhost:{port}/docs")
    print()
    print("  Ctrl+C pour arreter")
    print("  " + "-" * 50)
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "server.main:app",
            host=host,
            port=port,
            reload=config.get("server.reload", False),
            log_level=config.get("server.log_level", "info")
        )
    except KeyboardInterrupt:
        print("\n  [!] Serveur arrete")
        pause()
    except Exception as e:
        print(f"\n  [!] Erreur: {e}")
        pause()


# ============================================
# MAIN MENU
# ============================================

def main():
    config = Config()
    scanner = Scanner()
    
    while True:
        clear()
        header()
        show_status(config)
        
        menu_box([
            ("1", "Demarrer BicameriS"),
            ("2", "Scanner les modeles"),
            ("3", "Configurer DIA [Gauche - Logique]"),
            ("4", "Configurer PAL [Droit - Intuition]"),
            ("5", "Presets de configuration"),
            ("6", "Informations systeme"),
            ("q", "Quitter"),
        ])
        print()
        
        choice = get_choice("Choix", "1", allow_back=False)
        
        if choice == "1":
            start_server(config)
        elif choice == "2":
            menu_scan(scanner)
        elif choice == "3":
            if not scanner.models:
                print("\n  [!] Scannez d'abord les modeles (option 2)")
                time.sleep(1.5)
                continue
            while True:
                clear()
                header()
                print("    [+] CONFIGURATION DIA [Gauche - Logique]")
                print("    " + "-" * 50)
                current = config.get("models.left_hemisphere.name") or "Aucun"
                print(f"  Modele actuel: {current}")
                print()
                menu_box([
                    ("1", "Selectionner un modele"),
                    ("2", "Regler les parametres"),
                    ("3", "Restaurer les valeurs par defaut"),
                ], "OPTIONS")
                print()
                
                sub = get_choice("Choix", "1")
                if sub == "0":
                    break
                elif sub == "1":
                    menu_select_model(scanner, config, "left_hemisphere")
                elif sub == "2":
                    menu_model_settings(config, "left_hemisphere")
                elif sub == "3":
                    for param, spec in HEMISPHERE_PARAMS.items():
                        config.set(f"models.left_hemisphere.{param}", spec["default"])
                    config.save()
                    print("\n  [OK] Valeurs par defaut restaurees")
                    time.sleep(1)
        elif choice == "4":
            if not scanner.models:
                print("\n  [!] Scannez d'abord les modeles (option 2)")
                time.sleep(1.5)
                continue
            while True:
                clear()
                header()
                print("    [+] CONFIGURATION PAL [Droit - Intuition]")
                print("    " + "-" * 50)
                current = config.get("models.right_hemisphere.name") or "Aucun"
                print(f"  Modele actuel: {current}")
                print()
                menu_box([
                    ("1", "Selectionner un modele"),
                    ("2", "Regler les parametres"),
                    ("3", "Restaurer les valeurs par defaut"),
                ], "OPTIONS")
                print()
                
                sub = get_choice("Choix", "1")
                if sub == "0":
                    break
                elif sub == "1":
                    menu_select_model(scanner, config, "right_hemisphere")
                elif sub == "2":
                    menu_model_settings(config, "right_hemisphere")
                elif sub == "3":
                    for param, spec in HEMISPHERE_PARAMS.items():
                        config.set(f"models.right_hemisphere.{param}", spec["default"])
                    config.save()
                    print("\n  [OK] Valeurs par defaut restaurees")
                    time.sleep(1)
        elif choice == "5":
            menu_presets(config)
        elif choice == "6":
            menu_system_info()
        elif choice.lower() == "q":
            clear()
            print("\n\n  Au revoir!\n")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BicameriS Launcher - Cortex Cognitif Bicaméral",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python launcher.py              # Interactive TUI menu
    python launcher.py --start       # Start server directly
    python launcher.py --scan        # Scan models only
    python launcher.py --port 9000   # Start on custom port
    python launcher.py --no-gpu      # Disable GPU layers
        """
    )
    parser.add_argument("--start", action="store_true", help="Start server directly without TUI")
    parser.add_argument("--scan", action="store_true", help="Scan models and exit")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU acceleration")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    if args.version:
        print(f"BicameriS Launcher v{VERSION}")
        sys.exit(0)
    
    if args.start or args.scan:
        config = Config()
        scanner = Scanner()
        
        if args.scan:
            username = os.environ.get("USERNAME", "user")
            common = [
                str(BASE_DIR / "models"),
                f"C:\\Users\\{username}\\.lmstudio\\models",
                f"C:\\Users\\{username}\\AppData\\Local\\.lmstudio\\models",
            ]
            scan_path = None
            for p in common:
                if os.path.exists(p):
                    scan_path = p
                    break
            
            if scan_path:
                models = scanner.scan(scan_path)
                print(f"\n[OK] {len(models)} models found")
                for m in models[:10]:
                    print(f"  - {m['name']} ({m['size_mb']:.0f} MB)")
            else:
                print("[!] No model paths found")
            sys.exit(0)
        
        if args.start:
            config.set("server.port", args.port)
            config.set("server.host", args.host)
            config.set("server.reload", args.reload)
            
            if args.no_gpu:
                config.set("models.left_hemisphere.n_gpu_layers", 0)
                config.set("models.right_hemisphere.n_gpu_layers", 0)
            
            start_server(config)
    else:
        main()
