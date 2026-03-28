#!/usr/bin/env python3
"""
BicameriS Launcher - Text User Interface
========================================
Diadikos & Palladion - By Hope 'n Mind

Interactive TUI for launching and configuring BicameriS.
"""

import sys
import os
import json
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure project root is in path
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))


# ============================================
# MODEL NAME RATIONALIZATION
# ============================================

def rationalize_model_name(filename: str) -> dict:
    """
    Converts technical filename to readable info.
    Example: "Qwen_Qwen3-14B-16K_Q8_0.gguf" -> 
        {name: "Qwen3", size: "14B", quant: "Q8_0", context: "16K", base: "Qwen"}
    """
    name = filename.replace('.gguf', '').replace('.GGUF', '')
    
    # Extract quantization (Q4_K_M, Q8_0, etc.)
    quant = "Unknown"
    quant_patterns = [
        r'[Qq](\d+)[_\s]*[KkSs]?[_\s]*[MmLl]?',  # Q4_K_M, Q8_0, etc.
        r'([fF]\d+)',  # f16, f32
        r'(GPTQ|AWQ|EXL2|GGML)',  # Other formats
    ]
    for pat in quant_patterns:
        match = re.search(pat, name)
        if match:
            quant = match.group(0)
            name = name.replace(quant, '').strip('_- ')
            break
    
    # Extract size (1B, 3B, 7B, 13B, 70B, etc.)
    size = "?"
    size_match = re.search(r'(\d+\.?\d*)[bB]', name)
    if size_match:
        size = f"{size_match.group(1)}B"
    
    # Extract context length (16K, 32K, 128K, etc.)
    context = ""
    ctx_match = re.search(r'(\d+)[kK]', name)
    if ctx_match:
        context = f"{ctx_match.group(1)}K"
    
    # Extract base model name (usually first part)
    # Remove common prefixes/suffixes
    name = re.sub(r'^[A-Za-z]+_', '', name)  # Remove provider prefix
    name = re.sub(r'[-_]\d+[bB].*', '', name)  # Remove size and after
    name = re.sub(r'[-_][Qq]\d+.*', '', name)  # Remove quant and after
    name = re.sub(r'[-_]\d+[kK].*', '', name)  # Remove context and after
    name = name.replace('_', ' ').replace('-', ' ').strip()
    
    # If name is empty or too short, use original
    if len(name) < 2:
        name = filename.split('_')[0] if '_' in filename else filename.split('-')[0]
    
    return {
        "display_name": name,
        "size": size,
        "quant": quant,
        "context": context,
        "full_path": "",
        "raw_name": filename
    }


def format_model_display(info: dict) -> str:
    """Format model info for display"""
    parts = [info["display_name"]]
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
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 1,
        "reload": False,
        "log_level": "info"
    },
    "models": {
        "left_hemisphere": {
            "name": "Left Brain",
            "path": "",
            "n_ctx": 16384,
            "n_gpu_layers": -1,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "max_tokens": 2048
        },
        "right_hemisphere": {
            "name": "Right Brain",
            "path": "",
            "n_ctx": 4096,
            "n_gpu_layers": -1,
            "temperature": 1.2,
            "top_p": 0.9,
            "repeat_penalty": 1.0,
            "max_tokens": 512
        }
    },
    "presets": {
        "balanced": {
            "left_temp": 0.7,
            "right_temp": 1.2,
            "left_ctx": 16384,
            "right_ctx": 4096
        },
        "creative": {
            "left_temp": 1.0,
            "right_temp": 1.5,
            "left_ctx": 8192,
            "right_ctx": 8192
        },
        "analytical": {
            "left_temp": 0.3,
            "right_temp": 0.8,
            "left_ctx": 32768,
            "right_ctx": 4096
        }
    }
}

CONFIG_FILE = BASE_DIR / "storage" / "config" / "launcher_config.json"
PRESETS_FILE = BASE_DIR / "storage" / "config" / "presets.json"


# ============================================
# TUI HELPERS
# ============================================

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print BicameriS header"""
    print()
    print("  " + "=" * 60)
    print("  |                                                          |")
    print("  |     ######  ##  ######  ####  ###   ### ###### ## ######  |")
    print("  |     ##  ## ## ##      ##  ## #### #### ##     ## ##      |")
    print("  |     ###### ## ##      ###### ## ### ## ####   ## ######  |")
    print("  |     ##  ## ## ##      ##  ## ##  #  ## ##     ##     ##  |")
    print("  |     ###### ## ####### ##  ## ##     ## ###### ## ######  |")
    print("  |                                                          |")
    print("  |      Diadikos & Palladion - By Hope 'n Mind              |")
    print("  " + "=" * 60)
    print()


def print_menu(options: list, title: str = "MENU"):
    """Print a menu with options"""
    print(f"  +{'-' * 42}+")
    print(f"  |  {title:^40}  |")
    print(f"  +{'-' * 42}+")
    for i, (key, desc) in enumerate(options, 1):
        print(f"  |  [{key}] {desc:<36}  |")
    print(f"  +{'-' * 42}+")
    print()


def get_input(prompt: str = "Choix", default: str = "") -> str:
    """Get user input with optional default"""
    if default:
        result = input(f"  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  {prompt}: ").strip()


def print_status(items: list):
    """Print status items"""
    print(f"  +{'-' * 42}+")
    for label, value in items:
        print(f"  |  {label:<20} {value:>18}  |")
    print(f"  +{'-' * 42}+")


# ============================================
# CONFIGURATION MANAGEMENT
# ============================================

class LauncherConfig:
    """Manage launcher configuration"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from file or defaults"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to file"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value by dot-notation key"""
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key_path: str, value: Any):
        """Set config value by dot-notation key"""
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


# ============================================
# MODEL SCANNER
# ============================================

class ModelScanner:
    """Recursive model scanner"""
    
    def __init__(self):
        self.found_models: List[dict] = []
        self.blacklist = {
            "$Recycle.Bin", "System Volume Information", "Windows",
            "AppData", "Program Files", "Program Files (x86)",
            "ProgramData", "Recovery", "PerfLogs", ".git", "__pycache__"
        }
    
    def scan(self, root_path: str, max_depth: int = 10) -> List[dict]:
        """Scan recursively for GGUF files"""
        self.found_models = []
        root = Path(root_path)
        
        if not root.exists():
            print(f"  [!] Chemin introuvable: {root_path}")
            return []
        
        print(f"  [*] Scan de: {root_path}")
        count = 0
        
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip blacklisted directories
            dirnames[:] = [d for d in dirnames if d not in self.blacklist]
            
            # Limit depth
            depth = dirpath.replace(str(root), '').count(os.sep)
            if depth > max_depth:
                dirnames.clear()
                continue
            
            for filename in filenames:
                if filename.lower().endswith('.gguf'):
                    try:
                        full_path = os.path.join(dirpath, filename)
                        stats = os.stat(full_path)
                        
                        # Rationalize name
                        info = rationalize_model_name(filename)
                        info["full_path"] = full_path
                        info["size_mb"] = round(stats.st_size / (1024**2), 1)
                        info["size_gb"] = round(stats.st_size / (1024**3), 2)
                        
                        self.found_models.append(info)
                        count += 1
                        
                        if count % 5 == 0:
                            print(f"    ... {count} modèles trouvés", end='\r')
                    except (OSError, PermissionError):
                        continue
        
        # Sort by size
        self.found_models.sort(key=lambda x: x["size_mb"])
        
        print(f"  [OK] {count} modèles trouvés (triés par taille)")
        return self.found_models


# ============================================
# MAIN TUI FUNCTIONS
# ============================================

def show_system_info():
    """Display system information"""
    clear_screen()
    print_header()
    print("  [+] INFORMATIONS SYSTEME")
    print("  " + "-" * 50)
    
    try:
        import psutil
        
        # CPU
        cpu_count = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        print(f"  CPU: {cpu_count} coeurs / {cpu_threads} threads")
        
        # RAM
        ram = psutil.virtual_memory()
        print(f"  RAM: {ram.total / (1024**3):.1f} Go total | {ram.available / (1024**3):.1f} Go libre")
        
        # GPU (if available)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                for gpu in gpus:
                    print(f"  GPU: {gpu.name} | {gpu.memoryTotal} Mo VRAM | {gpu.memoryFree} Mo libre")
            else:
                print("  GPU: Aucune détectée")
        except:
            print("  GPU: Non détecté")
        
        # Disk
        disk = psutil.disk_usage('/')
        print(f"  DISK: {disk.total / (1024**3):.0f} Go | {disk.free / (1024**3):.0f} Go libre")
        
    except ImportError:
        print("  [!] psutil non installé - informations limitées")
    
    input("\n  Appuyez sur Entrée pour continuer...")


def scan_models(scanner: ModelScanner) -> List[dict]:
    """Interactive model scanner"""
    clear_screen()
    print_header()
    print("  [+] SCANNER DE MODELES")
    print("  " + "-" * 50)
    
    # Common scan paths (using username dynamically)
    username = os.environ.get("USERNAME", "user")
    common_paths = [
        str(BASE_DIR / "models"),
        f"C:\\Users\\{username}\\LMStudio\\models",
        f"C:\\Users\\{username}\\.lmstudio\\models",
        f"C:\\Users\\{username}\\AppData\\Local\\.lmstudio\\models",
        f"C:\\Users\\{username}\\.cache\\lm-studio\\models",
        f"C:\\Users\\{username}\\.cache\\huggingface\\hub",
        "D:\\LMStudio\\models",
        "D:\\LLM\\models",
        "D:\\models",
    ]
    
    print("  Chemins de scan disponibles:")
    for i, path in enumerate(common_paths, 1):
        exists = "[OK]" if os.path.exists(path) else "[!!]"
        print(f"    [{i}] {exists} {path}")
    
    print()
    choice = get_input("Choix du chemin (1-5 ou chemin personnalisé)", "1")
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(common_paths):
            scan_path = common_paths[idx]
        else:
            scan_path = choice
    except ValueError:
        scan_path = choice
    
    if not os.path.exists(scan_path):
        print(f"  [!] Le chemin n'existe pas: {scan_path}")
        input("\n  Appuyez sur Entrée pour continuer...")
        return []
    
    print()
    models = scanner.scan(scan_path)
    
    if models:
        print()
        print(f"  [{len(models)} MODELES TROUVES - Triés par taille]")
        print("  " + "-" * 50)
        
        for i, model in enumerate(models[:20], 1):  # Show first 20
            display = format_model_display(model)
            print(f"    {i:>3}. {display:<40} {model['size_gb']:>6.1f} Go")
        
        if len(models) > 20:
            print(f"    ... et {len(models) - 20} autres modèles")
    
    input("\n  Appuyez sur Entrée pour continuer...")
    return models


def select_model(scanner: ModelScanner, hemisphere: str, config: LauncherConfig) -> bool:
    """Select a model for a hemisphere"""
    clear_screen()
    print_header()
    print(f"  [+] SELECTION MODELE - {hemisphere.upper()}")
    print("  " + "-" * 50)
    
    models = scanner.found_models
    
    if not models:
        print("  [!] Aucun modèle scanné. Scannez d'abord.")
        input("\n  Appuyez sur Entrée pour continuer...")
        return False
    
    # Display models
    print("  Modèles disponibles:")
    for i, model in enumerate(models[:30], 1):
        display = format_model_display(model)
        print(f"    {i:>3}. {display:<40} {model['size_gb']:>6.1f} Go")
    
    if len(models) > 30:
        print(f"    ... et {len(models) - 30} autres")
    
    print()
    choice = get_input("Numéro du modèle (ou 0 pour annuler)", "0")
    
    try:
        idx = int(choice) - 1
        if idx < 0:
            return False
        if idx >= len(models):
            print("  [!] Numéro invalide")
            input("\n  Appuyez sur Entrée pour continuer...")
            return False
        
        selected = models[idx]
        
        # Save to config
        config.set(f"models.{hemisphere}.path", selected["full_path"])
        config.set(f"models.{hemisphere}.name", selected["display_name"])
        config.save()
        
        print(f"  [OK] Modèle sélectionné: {format_model_display(selected)}")
        input("\n  Appuyez sur Entrée pour continuer...")
        return True
        
    except ValueError:
        print("  [!] Entrée invalide")
        input("\n  Appuyez sur Entrée pour continuer...")
        return False


def manage_presets(config: LauncherConfig):
    """Manage configuration presets"""
    clear_screen()
    print_header()
    print("  [+] PRESETS DE CONFIGURATION")
    print("  " + "-" * 50)
    
    presets = config.get("presets", {})
    
    print("  Presets disponibles:")
    for name, preset in presets.items():
        print(f"    - {name}: Left={preset.get('left_temp', '?')}, Right={preset.get('right_temp', '?')}")
    
    print()
    print("  [1] Utiliser un preset")
    print("  [2] Créer un nouveau preset")
    print("  [3] Retour")
    
    choice = get_input("Choix", "1")
    
    if choice == "1":
        preset_name = get_input("Nom du preset", "balanced")
        if preset_name in presets:
            preset = presets[preset_name]
            config.set("models.left_hemisphere.temperature", preset.get("left_temp", 0.7))
            config.set("models.right_hemisphere.temperature", preset.get("right_temp", 1.2))
            config.set("models.left_hemisphere.n_ctx", preset.get("left_ctx", 16384))
            config.set("models.right_hemisphere.n_ctx", preset.get("right_ctx", 4096))
            config.save()
            print(f"  [OK] Preset '{preset_name}' appliqué")
        else:
            print(f"  [!] Preset '{preset_name}' introuvable")
    
    elif choice == "2":
        name = get_input("Nom du nouveau preset")
        left_temp = float(get_input("Température Gauche", "0.7"))
        right_temp = float(get_input("Température Droite", "1.2"))
        left_ctx = int(get_input("Contexte Gauche", "16384"))
        right_ctx = int(get_input("Contexte Droite", "4096"))
        
        presets[name] = {
            "left_temp": left_temp,
            "right_temp": right_temp,
            "left_ctx": left_ctx,
            "right_ctx": right_ctx
        }
        config.set("presets", presets)
        config.save()
        print(f"  [OK] Preset '{name}' créé")
    
    input("\n  Appuyez sur Entrée pour continuer...")


def start_server(config: LauncherConfig):
    """Start the BicameriS server"""
    clear_screen()
    print_header()
    print("  [+] DEMARRAGE DU SERVEUR")
    print("  " + "-" * 50)
    
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8000)
    
    # Show configured models
    left_path = config.get("models.left_hemisphere.path", "")
    right_path = config.get("models.right_hemisphere.path", "")
    left_name = config.get("models.left_hemisphere.name", "Non configuré")
    right_name = config.get("models.right_hemisphere.name", "Non configuré")
    
    print(f"  Hémisphère Gauche: {left_name or 'Non configuré'}")
    print(f"  Hémisphère Droit:  {right_name or 'Non configuré'}")
    print()
    print(f"  Serveur: http://{host}:{port}")
    print(f"  Docs:    http://{host}:{port}/docs")
    print()
    print("  Appuyez sur Ctrl+C pour arrêter")
    print("  " + "-" * 50)
    
    # Start uvicorn
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
        print("\n  [!] Serveur arrêté")
    except Exception as e:
        print(f"\n  [!] Erreur: {e}")
        input("\n  Appuyez sur Entrée pour continuer...")


# ============================================
# MAIN MENU
# ============================================

def main():
    """Main TUI loop"""
    config = LauncherConfig()
    scanner = ModelScanner()
    
    while True:
        clear_screen()
        print_header()
        
        # Show current status
        left_name = config.get("models.left_hemisphere.name", "Non configuré")
        right_name = config.get("models.right_hemisphere.name", "Non configuré")
        left_path = config.get("models.left_hemisphere.path", "")
        right_path = config.get("models.right_hemisphere.path", "")
        
        print(f"  +-- Statut {'-' * 35}+")
        print(f"  | Gauche: {left_name or 'Non configuré':<33} |")
        print(f"  | Droit:  {right_name or 'Non configuré':<33} |")
        print(f"  +{'-' * 45}+")
        print()
        
        # Main menu
        print("  +==========================================+")
        print("  |              MENU PRINCIPAL                |")
        print("  +==========================================+")
        print("  |  [1] Demarrer BicameriS                    |")
        print("  |  [2] Scanner les modeles                   |")
        print("  |  [3] Selectionner modele Gauche (Logique)  |")
        print("  |  [4] Selectionner modele Droit (Intuition) |")
        print("  |  [5] Presets de configuration               |")
        print("  |  [6] Informations systeme                   |")
        print("  |  [q] Quitter                                |")
        print("  +==========================================+")
        
        choice = get_input("Choix", "1")
        
        if choice == "1":
            start_server(config)
        elif choice == "2":
            scan_models(scanner)
        elif choice == "3":
            select_model(scanner, "left_hemisphere", config)
        elif choice == "4":
            select_model(scanner, "right_hemisphere", config)
        elif choice == "5":
            manage_presets(config)
        elif choice == "6":
            show_system_info()
        elif choice.lower() == "q":
            print("\n  Au revoir!")
            break
        else:
            print("  [!] Choix invalide")
            time.sleep(1)


if __name__ == "__main__":
    main()
