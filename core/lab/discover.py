#!/usr/bin/env python3
"""
Script de Découverte Lab
======================
Explore les endpoints, services et modules disponibles.
"""

import sys
import os
from pathlib import Path

VERSION = "1.0.0"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def discover_registry():
    """Découverte des services dans le registry"""
    print_header("SERVICES DISPONIBLES (registry)")
    
    try:
        from server.extensions import registry
        
        print("Attributs du registry:")
        for attr in sorted(dir(registry)):
            if not attr.startswith('_'):
                val = getattr(registry, attr)
                val_type = type(val).__name__
                if val is None:
                    print(f"  • {attr}: None")
                else:
                    print(f"  • {attr}: {val_type}")
    except ImportError as e:
        print(f"  ⚠️ Registry non accessible: {e}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def discover_endpoints():
    """Découverte des endpoints API"""
    print_header("ENDPOINTS API")
    
    try:
        from server.routes import api_lab
        
        print("Routes Lab:")
        for route in api_lab.router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ','.join(route.methods)
                print(f"  {methods:8} {route.path}")
    except ImportError as e:
        print(f"  ⚠️ API non accessible: {e}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def discover_modules():
    """Découverte des modules Lab"""
    print_header("MODULES LAB")
    
    try:
        from core.lab.modules import list_lab_modules
        
        modules = list_lab_modules()
        print(f"Nombre de modules: {len(modules)}\n")
        
        for m in modules:
            print(f"  [{m['order']}] {m['icon']} {m['name']}")
            print(f"       ID: {m['id']}")
            print(f"       {m['description']}")
            print()
    except ImportError as e:
        print(f"  ⚠️ Modules non accessibles: {e}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def discover_themes():
    """Découverte des thèmes de l'Editeur Spécialiste"""
    print_header("THÈMES - ÉDITEUR SPÉCIALISTE")
    
    try:
        import importlib.util
        module_path = str(Path(__file__).parent / "modules" / "2_EditeurSpecialiste" / "themes.py")
        spec = importlib.util.spec_from_file_location("editeur_themes", module_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            THEMES = mod.THEMES
        else:
            THEMES = {}
        
        for theme_name, theme_data in THEMES.items():
            icon = theme_data.get("icon", "📁")
            print(f"  {icon} {theme_name}")
            
            subthemes = theme_data.get("subthemes", {})
            for i, (sub_name, sub_data) in enumerate(subthemes.items()):
                preprompt = sub_data.get("preprompt", "")[:60]
                prefix = "├──" if i < len(subthemes) - 1 else "└──"
                print(f"      {prefix} {sub_name}")
                print(f"      │   └── {prerompt}...")
            print()
    except ImportError as e:
        print(f"  ⚠️ Thèmes non accessibles: {e}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def discover_hemispheres():
    """Test de connexion aux hemispheres"""
    print_header("HÉMISPHERES")
    
    try:
        from server.extensions import registry
        
        if hasattr(registry, 'corps_calleux') and registry.corps_calleux:
            corps = registry.corps_calleux
            
            print("Statut des hemispheres:")
            print(f"  • Corps calleux: ✅ Connecté")
            print(f"  • Gauche: {'✅' if corps.left else '❌'}")
            print(f"  • Droit: {'✅' if corps.right else '❌'}")
            
            if corps.left:
                print(f"\nTest de l'hémisphère gauche:")
                try:
                    resp = corps.left.think("Réponds en un mot.", "Test")
                    print(f"  Réponse: {resp[:100]}...")
                except Exception as e:
                    print(f"  Erreur: {e}")
        else:
            print("  ⚠️ Corps calleux non initialisé")
    except ImportError as e:
        print(f"  ⚠️ Non accessible: {e}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def search_inference(query: str):
    """Rechercher dans les inferences"""
    print_header(f"RECHERCHE: '{query}'")
    
    try:
        from server.extensions import registry
        
        if hasattr(registry, 'corps_calleux') and registry.corps_calleux:
            corps = registry.corps_calleux
            
            if corps.left:
                print("Recherche via hemisphère gauche (analytique):")
                result = corps.left.think(
                    "Fais une recherche concise sur ce sujet.",
                    query
                )
                print(f"  {result[:500]}...")
            
            if corps.right:
                print("\nRecherche via hemisphère droit (intuitif):")
                result = corps.right.think(
                    "Propose une perspective intuitive sur ce sujet.",
                    query
                )
                print(f"  {result[:500]}...")
                
            print("\nSynthèse (si disponible):")
            if corps.left and corps.right:
                synthesis = corps.corpus.think if hasattr(corps, 'corpus') and corps.corpus else None
                if synthesis:
                    result = synthesis("Fais une synthèse des deux perspectives.", query)
                    print(f"  {result[:500]}...")
        else:
            print("  ⚠️ Corps calleux non disponible")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def search_code(pattern: str):
    """Rechercher dans le code des modules"""
    print_header(f"RECHERCHE DANS LES MODULES: '{pattern}'")
    
    modules_dir = Path(__file__).parent / "modules"
    
    if not modules_dir.exists():
        print("  ⚠️ Dossier modules non trouvé")
        return
    
    found = []
    for py_file in modules_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            if pattern.lower() in content.lower():
                rel_path = py_file.relative_to(modules_dir.parent)
                found.append(str(rel_path))
        except:
            pass
    
    if found:
        print(f"Fichiers contenant '{pattern}':")
        for f in found:
            print(f"  • {f}")
    else:
        print(f"Aucun fichier trouvé contenant '{pattern}'")


def test_action(module_id: str, action: str, data: dict = None):
    """Tester une action de module"""
    print_header(f"TEST ACTION: {module_id}.{action}")
    
    try:
        from core.lab.modules import get_lab_module
        
        module = get_lab_module(module_id)
        if not module:
            print(f"  ⚠️ Module non trouvé: {module_id}")
            return
        
        result = module.handle_action(action, data or {})
        print(f"  Résultat: {result}")
    except Exception as e:
        print(f"  ⚠️ Erreur: {e}")


def show_help():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                      COMMANDES DISPONIBLES                       ║
╠══════════════════════════════════════════════════════════════════╣
║  --all          Tout afficher                                     ║
║  --registry     Services disponibles                              ║
║  --endpoints    Endpoints API                                    ║
║  --modules      Modules Lab                                     ║
║  --themes       Thèmes Editeur Spécialiste                       ║
║  --hemi         Tester les hemispheres                          ║
║  --search       Rechercher dans les modules                     ║
║  --infer        Faire une inference de test                     ║
║  --test         Tester une action (module action)                ║
║  --help         Cette aide                                       ║
╚══════════════════════════════════════════════════════════════════╝

Exemples:
  python discover.py --all
  python discover.py --modules
  python discover.py --infer "pourquoi le ciel est bleu"
  python discover.py --search "corps_calleux"
  python discover.py --test editeur-specialiste get_themes
""")


def main():
    print("""
    o===================================================================o
    |                                                                   |
    | ██████╗ ██╗ ██████╗ █████╗ ███╗   ███╗███████╗██████╗ ██╗███████╗ |
    | ██╔══██╗██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔══██╗██║██╔════╝ |
    | ██████╔╝██║██║     ███████║██╔████╔██║█████╗  ██████╔╝██║███████╗ |
    | ██╔══██╗██║██║     ██╔══██║██║╚██╔╝██║██╔══╝  ██╔══██╗██║╚════██║ |
    | ██████╔╝██║╚██████╗██║  ██║██║ ╚═╝ ██║███████╗██║  ██║██║███████║ |
    | ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝ |
    |                                                                   |
    |                Diadikos & Palladion - By Hope 'n Mind             |
    |                            v1.0.0                                  |
    o===================================================================o
    """)
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Script de découverte Lab", add_help=False)
    parser.add_argument('--all', action='store_true', help="Tout afficher")
    parser.add_argument('--registry', action='store_true', help="Services disponibles")
    parser.add_argument('--endpoints', action='store_true', help="Endpoints API")
    parser.add_argument('--modules', action='store_true', help="Modules Lab")
    parser.add_argument('--themes', action='store_true', help="Thèmes Editeur Spécialiste")
    parser.add_argument('--hemi', action='store_true', help="Tester les hemispheres")
    parser.add_argument('--search', type=str, help="Rechercher dans le code")
    parser.add_argument('--infer', type=str, help="Faire une inference de test")
    parser.add_argument('--test', nargs=2, metavar=('MODULE', 'ACTION'), help="Tester une action")
    parser.add_argument('--help', action='store_true', help="Afficher l'aide")
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        return
    
    if args.all or not any([args.registry, args.endpoints, args.modules, args.themes, args.hemi, args.search, args.infer, args.test]):
        show_help()
        return
    
    if args.registry or args.all:
        discover_registry()
    if args.endpoints or args.all:
        discover_endpoints()
    if args.modules or args.all:
        discover_modules()
    if args.themes or args.all:
        discover_themes()
    if args.hemi or args.all:
        discover_hemispheres()
    if args.search:
        search_code(args.search)
    if args.infer:
        search_inference(args.infer)
    if args.test:
        test_action(args.test[0], args.test[1])


if __name__ == "__main__":
    main()
