"""
Data Ingestion Tool Registration
================================
Register data ingestion tools in the Tool Registry.
"""

import logging
from .tool_registry import get_tool_registry
from .web_tools import get_web_tools
from ..data.ingestion import get_ingestion_system

logger = logging.getLogger("agents.data_tools_registration")


def register_data_tools():
    """Register all data ingestion tools"""
    registry = get_tool_registry()
    ingestion = get_ingestion_system()
    
    registry.register(
        name="ingest_arxiv",
        description="Search and ingest arXiv papers (math, physics, CS). Returns paper metadata and extracts LaTeX formulas.",
        parameters={
            "query": {"type": "string", "description": "Search query for arXiv"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        function=lambda query, max_results=5: _sync_ingest(ingestion, "arxiv", query, max_results),
        category="research",
        enabled=False,
        examples=["Search arXiv for quantum computing papers", "Find latest deep learning papers on arXiv"]
    )
    
    registry.register(
        name="ingest_crossref",
        description="Search open access papers via Crossref DOI. Returns metadata, abstracts, and references.",
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        function=lambda query, max_results=5: _sync_ingest(ingestion, "crossref", query, max_results),
        category="research",
        enabled=False,
        examples=["Find papers about climate change via DOI"]
    )
    
    registry.register(
        name="ingest_pubchem",
        description="Search chemical compounds in PubChem. Returns molecular formulas, weights, and properties.",
        parameters={
            "query": {"type": "string", "description": "Compound name or formula"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        function=lambda query, max_results=5: _sync_ingest(ingestion, "pubchem", query, max_results),
        category="research",
        enabled=False,
        examples=["Search caffeine in PubChem", "Find molecular formula of water"]
    )
    
    registry.register(
        name="ingest_github",
        description="Search code snippets on GitHub. Returns file content, language, and repository info.",
        parameters={
            "query": {"type": "string", "description": "Code search query"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        function=lambda query, max_results=5: _sync_ingest(ingestion, "github", query, max_results),
        category="code",
        enabled=False,
        examples=["Find authentication Python code snippets", "Search React hooks implementations"]
    )
    
    registry.register(
        name="ingest_gutenberg",
        description="Search classic literature from Project Gutenberg. Returns book metadata and text.",
        parameters={
            "query": {"type": "string", "description": "Book title or author"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5}
        },
        function=lambda query, max_results=5: _sync_ingest(ingestion, "gutenberg", query, max_results),
        category="research",
        enabled=False,
        examples=["Find Shakespeare plays in Gutenberg"]
    )
    
    registry.register(
        name="convert_units",
        description="Convert between units using UCUM. Supports SI and derived units.",
        parameters={
            "value": {"type": "number", "description": "Value to convert"},
            "from_unit": {"type": "string", "description": "Source unit"},
            "to_unit": {"type": "string", "description": "Target unit"}
        },
        function=lambda value, from_unit, to_unit: _convert_units(ingestion, value, from_unit, to_unit),
        category="research",
        enabled=False,
        examples=["Convert 100 km to miles", "Convert 1 hour to seconds"]
    )
    
    registry.register(
        name="search_ontology",
        description="Search ontology entities (Schema.org, DBpedia, Wikidata).",
        parameters={
            "query": {"type": "string", "description": "Entity to search"},
            "source": {"type": "string", "description": "ontology or schemaorg", "default": "ontology"}
        },
        function=lambda query, source="ontology": _search_ontology(ingestion, query, source),
        category="research",
        enabled=False,
        examples=["Search Schema.org for Person", "Find definition of AI in ontologies"]
    )
    
    logger.info("[DataTools] Registered: arxiv, crossref, pubchem, github, gutenberg, units, ontology")


def _sync_ingest(ingestion, source, query, max_results):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                ingestion.ingest(source, query, max_results=max_results),
                loop
            )
            return {"status": "ok", "results": future.result()}
        else:
            return loop.run_until_complete(ingestion.ingest(source, query, max_results=max_results))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _convert_units(ingestion, value, from_unit, to_unit):
    result = ingestion.ucum.convert(float(value), from_unit, to_unit)
    if result is not None:
        return {"status": "ok", "result": result, "from": f"{value} {from_unit}", "to": f"{result} {to_unit}"}
    return {"status": "error", "message": f"Conversion failed. Available units: {list(ingestion.ucum.units.keys())[:10]}..."}


def _search_ontology(ingestion, query, source):
    results = ingestion.ontology.search(query)
    return {"status": "ok", "results": results[:10]}
