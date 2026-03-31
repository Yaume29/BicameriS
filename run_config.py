#!/usr/bin/env python3
"""
Diadikos Launcher Configuration Script
========================================
Allows setting and modifying default parameters before server startup.
Can be run standalone or with the launcher.

Usage:
    python run_config.py              # Interactive mode
    python run_config.py --defaults   # Show current defaults
    python run_config.py --reset      # Reset to factory defaults
    python run_config.py --server     # Configure and start server
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


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
            "name": "Qwen2.5-14B",
            "path": "",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 4096
        },
        "right_hemisphere": {
            "name": "Gemma-3-12B",
            "path": "",
            "temperature": 0.9,
            "top_p": 0.95,
            "max_tokens": 2048
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
    "endocrine": {
        "enabled": True,
        "sensitivity": 0.5,
        "impact": 0.5
    },
    "security": {
        "strict_airgap_mode": False,
        "auto_scaffolding_full": False,
        "auto_scaffolding_limited": False,
        "auto_optimization": False,
        "sandbox_docker": True,
        "trauma_filter": True,
        "entropy_tracking": True,
        "max_execution_time": 30,
        "max_memory_mb": 512,
        "allowed_pip_packages": ["numpy", "pandas", "requests", "beautifulsoup4", "pillow"]
    },
    "threading": {
        "io_workers_max": 4,
        "dreamer_workers_max": 2,
        "inference_workers_max": 8
    },
    "timeouts": {
        "model_startup": 600,
        "inference": 120,
        "scan": 60
    },
    "mcp": {
        "enabled": False,
        "servers": []
    },
    "telemetry": {
        "enabled": True,
        "log_dir": "storage/logs",
        "retention_days": 7
    }
}

CONFIG_FILE = Path("storage/config/runtime_config.json")
HISTORY_FILE = Path("storage/config/config_history.json")


class ConfigManager:
    """Manage Diadikos runtime configuration"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.history: list = []
        self.load()
    
    def load(self):
        """Load configuration from file or defaults"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                print(f"📂 Configuration loaded from {CONFIG_FILE}")
            except json.JSONDecodeError:
                print("⚠️ Corrupted config, using defaults")
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()
            print("📝 Using default configuration")
        
        self.load_history()
    
    def load_history(self):
        """Load configuration history"""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def save(self):
        """Save configuration to file"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"💾 Configuration saved to {CONFIG_FILE}")
    
    def save_history(self):
        """Save configuration change history"""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)
    
    def reset(self):
        """Reset to factory defaults"""
        self.config = DEFAULT_CONFIG.copy()
        self.save()
        print("🔄 Configuration reset to factory defaults")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value by dot-separated path"""
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """Set config value by dot-separated path"""
        keys = key_path.split(".")
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        old_value = target.get(keys[-1])
        target[keys[-1]] = value
        
        if save:
            self.save()
            self.add_to_history(f"Changed {key_path}: {old_value} → {value}")
        
        return old_value, value
    
    def add_to_history(self, description: str):
        """Add change to history"""
        from datetime import datetime
        entry = {
            "timestamp": datetime.now().isoformat(),
            "description": description
        }
        self.history.append(entry)
        if len(self.history) > 50:
            self.history = self.history[-50:]
        self.save_history()
    
    def show(self):
        """Display current configuration"""
        print("\n" + "=" * 60)
        print("📋 Diadikos CONFIGURATION")
        print("=" * 60)
        
        for section, values in self.config.items():
            print(f"\n🔹 {section.upper()}")
            if isinstance(values, dict):
                for key, value in values.items():
                    if isinstance(value, dict):
                        print(f"  └─ {key}:")
                        for k, v in value.items():
                            print(f"      • {k}: {v}")
                    else:
                        print(f"  • {key}: {value}")
            else:
                print(f"  • {value}")
        print("\n" + "=" * 60)
    
    def show_diffs(self, other: Dict):
        """Show differences between configs"""
        print("\n📊 Configuration Differences:")
        for section, values in DEFAULT_CONFIG.items():
            if section in other:
                if values != other[section]:
                    print(f"\n🔸 {section}:")
                    self._compare_dict(values, other[section])
    
    def _compare_dict(self, d1: Dict, d2: Dict, indent: int = 2):
        """Recursively compare dictionaries"""
        for key in d1:
            if key not in d2:
                print(f"{' '*indent}  - {key}: {d1[key]} (removed)")
            elif d1[key] != d2[key]:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    print(f"{' '*indent}  • {key}:")
                    self._compare_dict(d1[key], d2[key], indent + 2)
                else:
                    print(f"{' '*indent}  • {key}: {d1[key]} → {d2[key]}")


def interactive_config(manager: ConfigManager):
    """Interactive configuration mode"""
    print("\n" + "=" * 60)
    print("⚙️  Diadikos INTERACTIVE CONFIGURATOR")
    print("=" * 60)
    print("\nAvailable sections:")
    print("  1. Server settings")
    print("  2. Model paths & parameters")
    print("  3. Hardware monitoring")
    print("  4. Cognitive modes")
    print("  5. Endocrine system")
    print("  6. Security settings")
    print("  7. MCP servers")
    print("  8. Telemetry")
    print("  9. Show full config")
    print(" 10. Reset to defaults")
    print(" 11. Save & Exit")
    print(" 12. Exit without saving")
    
    while True:
        try:
            choice = input("\n👉 Select option [1-12]: ").strip()
            
            if choice == "1":
                print("\n📡 SERVER SETTINGS")
                host = input(f"  Host [{manager.get('server.host')}]: ").strip() or None
                port = input(f"  Port [{manager.get('server.port')}]: ").strip() or None
                workers = input(f"  Workers [{manager.get('server.workers')}]: ").strip() or None
                log_level = input(f"  Log level [{manager.get('server.log_level')}]: ").strip() or None
                
                if host: manager.set("server.host", host)
                if port: manager.set("server.port", int(port))
                if workers: manager.set("server.workers", int(workers))
                if log_level: manager.set("server.log_level", log_level)
                
            elif choice == "2":
                print("\n🤖 MODEL CONFIGURATION")
                print("  [L] Left hemisphere (Qwen)")
                print("  [R] Right hemisphere (Gemma)")
                side = input("👉 Select [L/R]: ").upper().strip()
                
                prefix = "left_hemisphere" if side == "L" else "right_hemisphere"
                
                name = input(f"  Model name [{manager.get(f'models.{prefix}.name')}]: ").strip() or None
                path = input(f"  Model path [{manager.get(f'models.{prefix}.path')}]: ").strip() or None
                temp = input(f"  Temperature [{manager.get(f'models.{prefix}.temperature')}]: ").strip() or None
                max_tokens = input(f"  Max tokens [{manager.get(f'models.{prefix}.max_tokens')}]: ").strip() or None
                
                if name: manager.set(f"models.{prefix}.name", name)
                if path: manager.set(f"models.{prefix}.path", path)
                if temp: manager.set(f"models.{prefix}.temperature", float(temp))
                if max_tokens: manager.set(f"models.{prefix}.max_tokens", int(max_tokens))
                
            elif choice == "3":
                print("\n🌡️ HARDWARE MONITORING")
                thermal = input(f"  Enable thermal monitoring [Y/N]: ").strip().upper()
                entropy = input(f"  Enable entropy tracking [Y/N]: ").strip().upper()
                guillotine = input(f"  Enable VRAM guillotine [Y/N]: ").strip().upper()
                
                if thermal in ("Y", "N"):
                    manager.set("hardware.thermal_monitoring", thermal == "Y")
                if entropy in ("Y", "N"):
                    manager.set("hardware.entropy_tracking", entropy == "Y")
                if guillotine in ("Y", "N"):
                    manager.set("hardware.vr_guillotine", guillotine == "Y")
                    
            elif choice == "4":
                print("\n🧠 COGNITIVE MODES")
                autonomous = input(f"  Enable autonomous loop [Y/N]: ").strip().upper()
                interval = input(f"  Autonomous interval [s]: ").strip() or None
                pulse_high = input(f"  High pulse threshold: ").strip() or None
                pulse_low = input(f"  Low pulse threshold: ").strip() or None
                
                if autonomous in ("Y", "N"):
                    manager.set("cognition.autonomous_loop", autonomous == "Y")
                if interval: manager.set("cognition.autonomous_interval", int(interval))
                if pulse_high: manager.set("cognition.pulse_high", float(pulse_high))
                if pulse_low: manager.set("cognition.pulse_low", float(pulse_low))
                
            elif choice == "5":
                print("\n🧬 ENDOCRINE SYSTEM")
                enabled = input(f"  Enable hardware influence [Y/N]: ").strip().upper()
                sensitivity = input(f"  Sensitivity [0-1]: ").strip() or None
                impact = input(f"  Impact [0-1]: ").strip() or None
                
                if enabled in ("Y", "N"):
                    manager.set("endocrine.enabled", enabled == "Y")
                if sensitivity: manager.set("endocrine.sensitivity", float(sensitivity))
                if impact: manager.set("endocrine.impact", float(impact))
                
            elif choice == "6":
                print("\n🔒 SECURITY SETTINGS")
                airgap = input(f"  Strict airgap mode [Y/N]: ").strip().upper()
                scaffolding_full = input(f"  Auto-scaffolding FULL (docker, execute, web) [Y/N]: ").strip().upper()
                scaffolding_limited = input(f"  Auto-scaffolding LIMITED (file creation + web) [Y/N]: ").strip().upper()
                auto_opt = input(f"  Auto-optimization (LLM params) [Y/N]: ").strip().upper()
                docker = input(f"  Docker sandbox [Y/N]: ").strip().upper()
                trauma = input(f"  Trauma filter [Y/N]: ").strip().upper()
                
                if airgap in ("Y", "N"):
                    manager.set("security.strict_airgap_mode", airgap == "Y")
                if scaffolding_full in ("Y", "N"):
                    manager.set("security.auto_scaffolding_full", scaffolding_full == "Y")
                if scaffolding_limited in ("Y", "N"):
                    manager.set("security.auto_scaffolding_limited", scaffolding_limited == "Y")
                if auto_opt in ("Y", "N"):
                    manager.set("security.auto_optimization", auto_opt == "Y")
                if docker in ("Y", "N"):
                    manager.set("security.sandbox_docker", docker == "Y")
                if trauma in ("Y", "N"):
                    manager.set("security.trauma_filter", trauma == "Y")
                    
            elif choice == "7":
                print("\n🔌 MCP SERVERS")
                enabled = input(f"  Enable MCP [Y/N]: ").strip().upper()
                if enabled in ("Y", "N"):
                    manager.set("mcp.enabled", enabled == "Y")
                    
            elif choice == "8":
                print("\n📊 TELEMETRY")
                enabled = input(f"  Enable telemetry [Y/N]: ").strip().upper()
                retention = input(f"  Retention days: ").strip() or None
                
                if enabled in ("Y", "N"):
                    manager.set("telemetry.enabled", enabled == "Y")
                if retention: manager.set("telemetry.retention_days", int(retention))
                
            elif choice == "9":
                manager.show()
                
            elif choice == "10":
                confirm = input("⚠️ Reset ALL settings? [Y/N]: ").strip().upper()
                if confirm == "Y":
                    manager.reset()
                    
            elif choice == "11":
                print("\n💾 Saving configuration...")
                manager.save()
                print("✅ Configuration saved!")
                break
                
            elif choice == "12":
                print("\n👋 Exiting without saving...")
                break
                
        except (ValueError, KeyError) as e:
            print(f"⚠️ Error: {e}")
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Diadikos Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_config.py                  # Interactive mode
  python run_config.py --show           # Show current config
  python run_config.py --defaults       # Show defaults
  python run_config.py --reset          # Reset to defaults
  python run_config.py --set server.port 9000
  python run_config.py --server         # Configure & start
  python run_config.py --import config.json
        """
    )
    
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--defaults", action="store_true", help="Show default configuration")
    parser.add_argument("--reset", action="store_true", help="Reset to factory defaults")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set config value")
    parser.add_argument("--get", metavar="KEY", help="Get config value")
    parser.add_argument("--server", action="store_true", help="Configure and start server")
    parser.add_argument("--import-file", metavar="FILE", help="Import config from JSON file")
    parser.add_argument("--export", metavar="FILE", help="Export config to JSON file")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.show:
        manager.show()
        
    elif args.defaults:
        print("\n📋 DEFAULT CONFIGURATION:")
        print(json.dumps(DEFAULT_CONFIG, indent=2))
        
    elif args.reset:
        confirm = input("⚠️ Reset ALL settings to factory defaults? [Y/N]: ").strip().upper()
        if confirm == "Y":
            manager.reset()
        else:
            print("Cancelled.")
            
    elif args.set:
        key, value = args.set
        try:
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif "." in value and value.replace(".", "").isdigit():
                value = float(value)
            
            old, new = manager.set(key, value)
            print(f"✅ {key}: {old} → {new}")
        except Exception as e:
            print(f"⚠️ Error setting {key}: {e}")
            
    elif args.get:
        value = manager.get(args.get)
        print(f"{args.get}: {value}")
        
    elif args.server:
        interactive_config(manager)
        
        start = input("\n🚀 Start server now? [Y/N]: ").strip().upper()
        if start == "Y":
            import subprocess
            port = manager.get("server.port", 8000)
            host = manager.get("server.host", "0.0.0.0")
            print(f"\n🚀 Starting server on {host}:{port}...")
            subprocess.run(["python", "-m", "server.main", "--host", host, "--port", str(port)])
            
    elif args.import_file:
        try:
            with open(args.import_file, "r", encoding="utf-8") as f:
                imported = json.load(f)
            manager.config = imported
            manager.save()
            print(f"✅ Imported configuration from {args.import_file}")
        except Exception as e:
            print(f"⚠️ Import error: {e}")
            
    elif args.export:
        try:
            with open(args.export, "w", encoding="utf-8") as f:
                json.dump(manager.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Exported configuration to {args.export}")
        except Exception as e:
            print(f"⚠️ Export error: {e}")
            
    else:
        interactive_config(manager)


if __name__ == "__main__":
    main()
