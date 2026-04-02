"""
Logic Templates for Specialist Editor
=====================================
6 templates logiques pour différents types de travail.

Templates:
1. Academic - Format IMRAD (Introduction, Methods, Results, Discussion)
2. Code - Standards industriels + documentation
3. Research - Rapport universitaire EU-US
4. Experiment - Hypothèse → Méthode → Résultats → Conclusion
5. Analysis - Données → Pattern → Insight → Recommendation
6. Report - Executive Summary → Findings → Recommendations
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("specialist.logic_templates")


class LogicTemplate(Enum):
    """Templates logiques disponibles"""
    ACADEMIC = "academic"
    CODE = "code"
    RESEARCH = "research"
    EXPERIMENT = "experiment"
    ANALYSIS = "analysis"
    REPORT = "report"


@dataclass
class TemplateSection:
    """Section d'un template"""
    name: str
    description: str
    required: bool = True
    order: int = 0


@dataclass
class LogicTemplateConfig:
    """Configuration d'un template"""
    template: LogicTemplate
    name: str
    description: str
    sections: List[TemplateSection]
    style_guide: str = ""
    citation_format: str = "APA"


# Templates prédéfinis
TEMPLATES = {
    LogicTemplate.ACADEMIC: LogicTemplateConfig(
        template=LogicTemplate.ACADEMIC,
        name="Academic Paper (IMRAD)",
        description="Format académique standard pour publications scientifiques",
        sections=[
            TemplateSection("Abstract", "Résumé structuré (250 mots)", True, 1),
            TemplateSection("Introduction", "Contexte, problème, objectifs", True, 2),
            TemplateSection("Methods", "Méthodologie détaillée", True, 3),
            TemplateSection("Results", "Résultats bruts et analyses", True, 4),
            TemplateSection("Discussion", "Interprétation, limites, implications", True, 5),
            TemplateSection("Conclusion", "Synthèse et perspectives", True, 6),
            TemplateSection("References", "Citations formatées", True, 7),
        ],
        style_guide="Academic writing, formal tone, third person",
        citation_format="APA"
    ),
    
    LogicTemplate.CODE: LogicTemplateConfig(
        template=LogicTemplate.CODE,
        name="Code Documentation",
        description="Documentation technique pour code source",
        sections=[
            TemplateSection("Overview", "Vue d'ensemble du projet", True, 1),
            TemplateSection("Architecture", "Structure et composants", True, 2),
            TemplateSection("API Reference", "Documentation des endpoints/fonctions", True, 3),
            TemplateSection("Examples", "Exemples d'utilisation", True, 4),
            TemplateSection("Configuration", "Paramètres et options", False, 5),
            TemplateSection("Troubleshooting", "Problèmes courants et solutions", False, 6),
        ],
        style_guide="Clear, concise, code-focused",
        citation_format="N/A"
    ),
    
    LogicTemplate.RESEARCH: LogicTemplateConfig(
        template=LogicTemplate.RESEARCH,
        name="Research Report (EU-US)",
        description="Rapport de recherche aux normes universitaires EU-US",
        sections=[
            TemplateSection("Executive Summary", "Résumé exécutif (1 page)", True, 1),
            TemplateSection("Introduction", "Contexte et problématique", True, 2),
            TemplateSection("Literature Review", "Revue de littérature", True, 3),
            TemplateSection("Methodology", "Approche méthodologique", True, 4),
            TemplateSection("Findings", "Principales découvertes", True, 5),
            TemplateSection("Analysis", "Analyse approfondie", True, 6),
            TemplateSection("Conclusions", "Conclusions et recommandations", True, 7),
            TemplateSection("Bibliography", "Bibliographie complète", True, 8),
        ],
        style_guide="Formal, objective, evidence-based",
        citation_format="IEEE"
    ),
    
    LogicTemplate.EXPERIMENT: LogicTemplateConfig(
        template=LogicTemplate.EXPERIMENT,
        name="Experiment Report",
        description="Rapport d'expérimentation scientifique",
        sections=[
            TemplateSection("Hypothesis", "Hypothèse testable", True, 1),
            TemplateSection("Materials", "Matériel et équipements", True, 2),
            TemplateSection("Procedure", "Protocole expérimental", True, 3),
            TemplateSection("Data Collection", "Collecte de données", True, 4),
            TemplateSection("Analysis", "Analyse statistique", True, 5),
            TemplateSection("Results", "Résultats obtenus", True, 6),
            TemplateSection("Interpretation", "Interprétation des résultats", True, 7),
            TemplateSection("Validation", "Validation de l'hypothèse", True, 8),
        ],
        style_guide="Precise, measurable, reproducible",
        citation_format="APA"
    ),
    
    LogicTemplate.ANALYSIS: LogicTemplateConfig(
        template=LogicTemplate.ANALYSIS,
        name="Data Analysis Report",
        description="Rapport d'analyse de données",
        sections=[
            TemplateSection("Data Description", "Description des données", True, 1),
            TemplateSection("Methodology", "Méthodes d'analyse", True, 2),
            TemplateSection("Patterns", "Patterns identifiés", True, 3),
            TemplateSection("Insights", "Insights clés", True, 4),
            TemplateSection("Visualizations", "Graphiques et visualisations", False, 5),
            TemplateSection("Recommendations", "Recommandations basées sur les données", True, 6),
        ],
        style_guide="Data-driven, objective, actionable",
        citation_format="N/A"
    ),
    
    LogicTemplate.REPORT: LogicTemplateConfig(
        template=LogicTemplate.REPORT,
        name="Executive Report",
        description="Rapport exécutif pour décideurs",
        sections=[
            TemplateSection("Executive Summary", "Résumé exécutif (1-2 pages)", True, 1),
            TemplateSection("Key Findings", "Principales découvertes", True, 2),
            TemplateSection("Impact Analysis", "Analyse d'impact", True, 3),
            TemplateSection("Recommendations", "Recommandations stratégiques", True, 4),
            TemplateSection("Next Steps", "Prochaines étapes", True, 5),
            TemplateSection("Appendices", "Données supplémentaires", False, 6),
        ],
        style_guide="Concise, strategic, decision-focused",
        citation_format="N/A"
    ),
}


class LogicTemplateEngine:
    """
    Moteur de templates logiques.
    Génère des prompts et structures selon le template choisi.
    """
    
    def __init__(self):
        self.templates = TEMPLATES
    
    def get_template(self, template_id: str) -> Optional[LogicTemplateConfig]:
        """Récupère un template par ID"""
        try:
            template_enum = LogicTemplate(template_id)
            return self.templates.get(template_enum)
        except ValueError:
            return None
    
    def get_all_templates(self) -> List[Dict]:
        """Retourne tous les templates disponibles"""
        return [
            {
                "id": template.value,
                "name": config.name,
                "description": config.description,
                "sections": len(config.sections)
            }
            for template, config in self.templates.items()
        ]
    
    def generate_prompt(self, template_id: str, topic: str) -> str:
        """Génère un prompt basé sur le template"""
        template = self.get_template(template_id)
        
        if not template:
            return f"Traite ce sujet: {topic}"
        
        sections_text = "\n".join([
            f"{i+1}. {section.name}: {section.description}"
            for i, section in enumerate(sorted(template.sections, key=lambda s: s.order))
        ])
        
        return f"""Tu es un expert en {template.name.lower()}.

Sujet: {topic}

Structure requise:
{sections_text}

Style: {template.style_guide}
Format de citation: {template.citation_format}

Produis un document complet et professionnel selon cette structure."""
    
    def validate_content(self, content: str, template_id: str) -> Dict:
        """Valide le contenu par rapport au template"""
        template = self.get_template(template_id)
        
        if not template:
            return {"valid": False, "error": "Template non trouvé"}
        
        # Simple validation - check if sections are mentioned
        missing_sections = []
        for section in template.sections:
            if section.name.lower() not in content.lower():
                if section.required:
                    missing_sections.append(section.name)
        
        return {
            "valid": len(missing_sections) == 0,
            "missing_sections": missing_sections,
            "template": template.name
        }
    
    def get_style_guide(self, template_id: str) -> str:
        """Retourne le guide de style pour un template"""
        template = self.get_template(template_id)
        return template.style_guide if template else ""


# Instance globale
_logic_template_engine: Optional[LogicTemplateEngine] = None


def get_logic_template_engine() -> LogicTemplateEngine:
    """Récupère le moteur de templates logiques"""
    global _logic_template_engine
    if _logic_template_engine is None:
        _logic_template_engine = LogicTemplateEngine()
    return _logic_template_engine
