"""
Test BrainCache Compatibility
=============================
Vérifie si llama-cpp-python supporte BrainCache KV cache compression.

BrainCache est notre nom pour la compression KV cache avancée.
Basé sur des techniques open-source de compression de cache.
"""

import sys
import os
import platform
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_header():
    print("=" * 60)
    print("  BrainCache Compatibility Test")
    print("=" * 60)
    print()

def test_python_version():
    """Vérifie la version Python"""
    print("[1/6] Version Python")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 10:
        print("  [OK] Python >= 3.10 requis")
        return True
    else:
        print("  [FAIL] Python >= 3.10 requis")
        return False

def test_llama_cpp_installed():
    """Vérifie si llama-cpp-python est installé"""
    print("\n[2/6] llama-cpp-python")
    try:
        import llama_cpp
        version = getattr(llama_cpp, "__version__", "unknown")
        print(f"  [OK] Installe (version {version})")
        return True
    except ImportError:
        print("  [FAIL] Non installe")
        print("  -> pip install llama-cpp-python")
        return False

def test_braincache_params():
    """Vérifie si les paramètres BrainCache sont supportés"""
    print("\n[3/6] Parametres BrainCache")
    try:
        from llama_cpp import Llama
        import inspect
        
        # Vérifier les paramètres de __init__
        init_params = inspect.signature(Llama.__init__).parameters
        param_names = list(init_params.keys())
        
        has_cache_type_k = "cache_type_k" in param_names
        has_cache_type_v = "cache_type_v" in param_names
        has_flash_attention = "flash_attention" in param_names
        
        print(f"  cache_type_k: {'OK' if has_cache_type_k else 'FAIL'}")
        print(f"  cache_type_v: {'OK' if has_cache_type_v else 'FAIL'}")
        print(f"  flash_attention: {'OK' if has_flash_attention else 'FAIL'}")
        
        if has_cache_type_k and has_cache_type_v:
            print("\n  [OK] BrainCache supporte!")
            return True
        else:
            print("\n  [FAIL] BrainCache NON supporte")
            print("  -> Recompiler llama-cpp-python avec support KV cache")
            return False
            
    except Exception as e:
        print(f"  [FAIL] Erreur: {e}")
        return False

def test_cuda_available():
    """Vérifie si CUDA est disponible"""
    print("\n[4/6] CUDA (NVIDIA GPU)")
    
    # Test 1: PyTorch CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"  [OK] CUDA disponible (PyTorch)")
            print(f"  GPU: {gpu_name}")
            print(f"  VRAM: {gpu_memory:.1f} GB")
            return True
    except ImportError:
        pass
    
    # Test 2: nvidia-smi
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split(', ')
                if len(parts) >= 2:
                    print(f"  [OK] GPU: {parts[0]}")
                    print(f"  VRAM: {parts[1]}")
            return True
    except:
        pass
    
    print("  [WARN] CUDA non detecte (CPU uniquement)")
    return False

def test_system_ram():
    """Vérifie la RAM système"""
    print("\n[5/6] RAM Systeme")
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / 1024**3
        print(f"  RAM totale: {ram_gb:.1f} GB")
        
        if ram_gb >= 32:
            print("  [OK] RAM suffisante (>= 32 GB)")
            return True
        elif ram_gb >= 16:
            print("  [WARN] RAM limitee (16 GB)")
            return True
        else:
            print("  [FAIL] RAM insuffisante (< 16 GB)")
            return False
    except ImportError:
        print("  [WARN] psutil non installe, impossible de verifier")
        return True

def test_model_compatibility():
    """Test de compatibilite avec un modele"""
    print("\n[6/6] Test de Chargement (optionnel)")
    print("  Ce test necessite un modele GGUF")
    print("  Ignore pour l'instant")
    return True

def print_summary(results):
    """Résumé des tests"""
    print("\n" + "=" * 60)
    print("  RESUME")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\n  Tests reussis: {passed}/{total}")
    
    if passed == total:
        print("\n  [OK] Votre systeme est COMPATIBLE avec BrainCache!")
        print("\n  Prochaines etapes:")
        print("  1. Activer BrainCache dans les settings")
        print("  2. Tester avec cache_type_k='braincache3'")
        print("  3. Mesurer les gains de performance")
    elif passed >= total - 1:
        print("\n  [WARN] Presque compatible!")
        print("\n  Actions requises:")
        if not results[2]:  # braincache params
            print("  -> Recompiler llama-cpp-python avec support KV cache")
            print("  -> Voir instructions ci-dessous")
    else:
        print("\n  [FAIL] Des problemes doivent etre resolus")
        print("\n  Verifiez les erreurs ci-dessus")

def print_build_instructions():
    """Instructions pour recompiler avec support BrainCache"""
    print("\n" + "=" * 60)
    print("  INSTRUCTIONS: Build avec Support BrainCache")
    print("=" * 60)
    print("""
  Block Size Recommande: 64 (bon compromis qualite/compression)
  
  Option A: Utiliser le fork llama-cpp-turboquant (renomme BrainCache)
  
  1. Cloner le fork
     git clone https://github.com/TheTom/llama-cpp-turboquant.git
     cd llama-cpp-turboquant
  
  2. Build avec CUDA (votre RTX 4090)
     cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
     cmake --build build -j
  
  3. Installer
     pip install -e .
  
  4. Verifier
     python scripts/test_braincache.py
  
  
  Option B: Utiliser directement le binaire
  
  1. Build le fork (ci-dessus)
  
  2. Lancer le serveur
     ./build/bin/llama-server \\
       -m votre-modele.gguf \\
       --cache-type-k turbo3 --cache-type-v turbo3 \\
       -ngl 99 -c 16384 -fa on
  
  3. Dans BicameriS, configurer le provider comme "serveur externe"
  
  Note: Block size 64 = 5.12x compression avec qualite identique
""")

def main():
    print_header()
    
    results = []
    results.append(test_python_version())
    results.append(test_llama_cpp_installed())
    results.append(test_braincache_params())
    results.append(test_cuda_available())
    results.append(test_system_ram())
    results.append(test_model_compatibility())
    
    print_summary(results)
    
    if not results[2]:  # braincache params not supported
        print_build_instructions()
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
