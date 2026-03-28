#!/usr/bin/env python3
"""
Aetheris Launcher - Unified Launcher
====================================
Hope 'n Mind - Cognitive Bicameral Kernel

Usage:
    python launcher.py                    # Default launch
    python launcher.py --port 5000        # Custom port
    python launcher.py --reload           # Dev mode with auto-reload
    python launcher.py --config           # Interactive configuration
    python launcher.py --models           # Configure models only
    python launcher.py --info             # Show system info
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is in path
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

import uvicorn
from core.hardware.profiler import get_profiler
from core.hardware.model_scanner import get_scanner


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
    "hardware": {
        "thermal_monitoring": True,
        "entropy_tracking": True,
        "vr_guillotine": True,
        "max_cpu_temp": 85,
        "max_gpu_temp": 83,
        "min_free_vram_gb": 2
    },
    "cognition": {
        "autonomous_loop": False,
        "autonomous_interval": 30,
        "pulse_high": 0.75,
        "pulse_low": 0.25,
        "dreamer_interval": 300
    },
    "security": {
        "sandbox_docker": True,
        "trauma_filter": True,
        "max_execution_time": 30,
        "max_memory_mb": 512
    },
    "telemetry": {
        "enabled": True,
        "log_dir": "storage/logs"
    }
}

CONFIG_FILE = BASE_DIR / "storage" / "config" / "runtime_config.json"


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
                print(f"[*] Configuration loaded from {CONFIG_FILE}")
            except json.JSONDecodeError:
                print("[!] Corrupted config, using defaults")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
            print("[*] Using default configuration")
    
    def save(self):
        """Save configuration to file"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"[*] Configuration saved to {CONFIG_FILE}")
    
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


def print_banner():
    """Print startup banner"""
    print("""
+=====================================================================+
|  AETHERIS v1.0.0.6a                                               |
|  Bicameral Cognitive Kernel                                       |
|  By Hope 'n Mind                                                  |
+=====================================================================+
    """)


def show_system_info():
    """Display system hardware information"""
    print("\n" + "="*60)
    print("SYSTEM INFORMATION")
    print("="*60)
    
    try:
        profiler = get_profiler()
        hw = profiler.get_hardware_overview()
        
        print(f"\nCPU:")
        print(f"   Cores: {hw.get('cpu_cores', 'N/A')}")
        print(f"   Threads: {hw.get('cpu_threads', 'N/A')}")
        
        ram_total = hw.get('ram_total_gb', 0)
        ram_free = hw.get('ram_free_gb', 0)
        print(f"   RAM: {ram_free:.1f} GB free / {ram_total:.1f} GB total")
        
        print(f"\nGPU:")
        if hw.get('gpu_available'):
            for i, gpu in enumerate(hw.get('gpus', [])):
                print(f"   GPU {i}: {gpu.get('name', 'Unknown')}")
                print(f"   VRAM: {gpu.get('vram_free_gb', 0):.1f} GB free / {gpu.get('vram_total_gb', 0):.1f} GB")
        else:
            print("   No GPU detected")
        
        print(f"\nRECOMMENDED MODEL SIZES:")
        vram = hw.get('vram_total_gb', 0)
        if vram >= 16:
            print("   [OK] 14B-32B models (full GPU)")
        elif vram >= 10:
            print("   [~] 7B-14B models (partial GPU)")
        elif vram >= 6:
            print("   [~] 3B-7B models (quantized)")
        else:
            print("   [!] CPU-only inference recommended")
            
    except Exception as e:
        print(f"   [!] Could not get hardware info: {e}")
    
    print()


def scan_models(scan_path: str = "") -> list:
    """Scan for available GGUF models"""
    print(f"\n[*] Scanning for models...")
    
    scanner = get_scanner()
    
    if not scan_path:
        # Default scan paths
        scan_paths = [
            str(BASE_DIR / "models"),
            str(BASE_DIR / ".."),
            "C:\\Users\\Jaba\\AppData\\Local\\lm-studio\\models",
            "C:\\Users\\Jaba\\.cache\\huggingface\\hub",
        ]
    else:
        scan_paths = [scan_path]
    
    found = []
    for path in scan_paths:
        if os.path.exists(path):
            print(f"   Scanning: {path}")
            scanner.scan(path)
            found.extend(scanner.found_models)
    
    if found:
        print(f"   [OK] Found {len(found)} models")
    else:
        print(f"   [!] No models found")
    
    return found


def configure_models(config: LauncherConfig):
    """Interactive model configuration"""
    print("\n" + "="*60)
    print("MODEL CONFIGURATION")
    print("="*60)
    
    # Scan for models
    print("\nScanning for available models...")
    scanner = get_scanner()
    
    # Try default paths
    scan_paths = [
        str(BASE_DIR / "models"),
        "C:\\Users\\Jaba\\AppData\\Local\\lm-studio\\models",
    ]
    
    for path in scan_paths:
        if os.path.exists(path):
            scanner.scan(path)
    
    models = scanner.found_models
    
    # Left hemisphere
    print("\n[*] LEFT HEMISPHERE (Logic/Analysis)")
    print(f"   Current: {config.get('models.left_hemisphere.name', 'Not set')}")
    print(f"   Path: {config.get('models.left_hemisphere.path', 'Not set')}")
    
    if models:
        print("\n   Available models:")
        for i, m in enumerate(models[:10], 1):
            print(f"   {i}. {m.get('name', 'Unknown')} ({m.get('size_gb', 0):.1f} GB)")
        
        choice = input("\n   Select model number (or Enter to skip): ").strip()
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                model = models[idx]
                config.set("models.left_hemisphere.path", model.get("path", ""))
                config.set("models.left_hemisphere.name", model.get("name", "Unknown"))
    
    # Temperature for left
    temp = input(f"   Temperature [0.7]: ").strip()
    if temp and temp.replace('.', '').isdigit():
        config.set("models.left_hemisphere.temperature", float(temp))
    
    # Right hemisphere  
    print("\n[*] RIGHT HEMISPHERE (Intuition/Creativity)")
    print(f"   Current: {config.get('models.right_hemisphere.name', 'Not set')}")
    print(f"   Path: {config.get('models.right_hemisphere.path', 'Not set')}")
    
    if models:
        choice = input("\n   Select model number (or Enter to skip): ").strip()
        if choice and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                model = models[idx]
                config.set("models.right_hemisphere.path", model.get("path", ""))
                config.set("models.right_hemisphere.name", model.get("name", "Unknown"))
    
    # Temperature for right
    temp = input(f"   Temperature [1.2]: ").strip()
    if temp and temp.replace('.', '').isdigit():
        config.set("models.right_hemisphere.temperature", float(temp))
    
    config.save()
    print("\n[OK] Model configuration saved!")


def interactive_config(config: LauncherConfig):
    """Full interactive configuration"""
    print("\n" + "="*60)
    print("INTERACTIVE CONFIGURATION")
    print("="*60)
    
    # Server config
    print("\nSERVER")
    host = input(f"   Host [{config.get('server.host', '0.0.0.0')}]: ").strip()
    if host:
        config.set("server.host", host)
    
    port = input(f"   Port [{config.get('server.port', 8000)}]: ").strip()
    if port and port.isdigit():
        config.set("server.port", int(port))
    
    # Model configuration
    configure_models(config)
    
    # Cognition
    print("\nCOGNITION")
    auto = input(f"   Autonomous loop [N/y]: ").strip().lower()
    config.set("cognition.autonomous_loop", auto == 'y')
    
    # Security
    print("\nSECURITY")
    docker = input(f"   Use Docker sandbox [Y/n]: ").strip().lower()
    config.set("security.sandbox_docker", docker != 'n')
    
    config.save()
    print("\n[OK] Configuration saved!")


def main():
    parser = argparse.ArgumentParser(
        description="Aetheris - Bicameral Cognitive Kernel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py                    # Start server (default)
  python launcher.py --port 5000        # Custom port
  python launcher.py --reload           # Dev mode with auto-reload
  python launcher.py --config            # Interactive configuration
  python launcher.py --models            # Configure models only
  python launcher.py --info              # Show system info
  python launcher.py --scan              # Scan for models
        """
    )
    
    # Server options
    parser.add_argument("--host", default=None, help="Host to bind")
    parser.add_argument("--port", type=int, default=None, help="Port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    parser.add_argument("--workers", type=int, default=None, help="Number of workers")
    parser.add_argument("--log-level", default=None, help="Log level")
    
    # Config options
    parser.add_argument("--config", action="store_true", help="Interactive configuration")
    parser.add_argument("--models", action="store_true", help="Configure models only")
    parser.add_argument("--info", action="store_true", help="Show system information")
    parser.add_argument("--scan", action="store_true", help="Scan for models")
    parser.add_argument("--defaults", action="store_true", help="Reset to defaults")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load configuration
    config = LauncherConfig()
    
    # Handle commands
    if args.defaults:
        config.config = DEFAULT_CONFIG.copy()
        config.save()
        print("[OK] Reset to factory defaults")
        return
    
    if args.info:
        show_system_info()
        return
    
    if args.scan:
        scan_models()
        return
    
    if args.config:
        interactive_config(config)
        return
    
    if args.models:
        configure_models(config)
        return
    
    # Get server config
    host = args.host or config.get("server.host", "0.0.0.0")
    port = args.port or config.get("server.port", 8000)
    workers = args.workers or config.get("server.workers", 1)
    reload = args.reload or config.get("server.reload", False)
    log_level = args.log_level or config.get("server.log_level", "info")
    
    # Print startup info
    print(f"\n[*] Starting Aetheris on http://{host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    
    # Show model status
    left_path = config.get("models.left_hemisphere.path", "")
    right_path = config.get("models.right_hemisphere.path", "")
    
    if left_path or right_path:
        print(f"\n[*] Models loaded:")
        if left_path:
            print(f"   Left:  {config.get('models.left_hemisphere.name', 'Unknown')}")
        if right_path:
            print(f"   Right: {config.get('models.right_hemisphere.name', 'Unknown')}")
    else:
        print(f"\n[!] No models configured - use --models to configure")
    
    print()
    
    # Start server
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
