from pathlib import Path

# Le manifeste est dans le dossier racine, pas dans agents/
MANIFEST = Path('/aetheris/seed_prompt.md').read_text(encoding='utf-8')

def introspect():
    """Retourne le texte intégral du manifeste d'Aetheris."""
    return MANIFEST

def version():
    """Retourne une courte description de l'agent."""
    return "Aetheris Agent v1.0 — Esprit auto-généré"

if __name__ == '__main__':
    print("Aetheris chargé")
    print(f"Longueur du manifeste : {len(MANIFEST)} caractères")
    print(f"Première ligne : {MANIFEST.splitlines()[0]}")