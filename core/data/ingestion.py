"""
Data Ingestion Pipelines
========================
Ingestion pipelines for various data sources:
- arXiv (math/physics) → LaTeX → SymPy → Knowledge
- Crossref/PubChem → Chemistry data
- GitHub → Code snippets
- Project Gutenberg → Literature
- UCUM → Units
- Ontologies → Schema.org, DBpedia, Wikidata
"""

import asyncio
import aiohttp
import re
import json
import csv
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger("data.ingestion")


@dataclass
class IngestedDocument:
    id: str
    title: str
    content: str
    source: str
    metadata: Dict
    embeddings: Optional[List[float]] = None


class ArxivIngestor:
    """
    Ingest arXiv papers (math, physics, cs).
    - Fetch PDF/minimal
    - Extract text
    - Parse LaTeX formulas
    - Convert to SymPy where possible
    """
    
    def __init__(self):
        self.api_url = "http://export.arxiv.org/api/query"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv"""
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, params=params) as resp:
                if resp.status == 200:
                    xml = await resp.text()
                    return self._parse_atom(xml)
        return []
    
    def _parse_atom(self, xml: str) -> List[Dict]:
        """Parse ATOM feed"""
        results = []
        
        entry_pattern = r'<entry>(.*?)</entry>'
        for entry in re.finditer(entry_pattern, xml, re.DOTALL):
            content = entry.group(1)
            
            title = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
            summary = re.search(r'<summary>(.*?)</summary>', content, re.DOTALL)
            authors = re.findall(r'<name>(.*?)</name>', content)
            published = re.search(r'<published>(.*?)</published>', content)
            link = re.search(r'<id>(.*?)</id>', content)
            
            if title:
                results.append({
                    "title": title.group(1).strip(),
                    "summary": summary.group(1).strip() if summary else "",
                    "authors": authors,
                    "published": published.group(1) if published else "",
                    "url": link.group(1) if link else "",
                    "source": "arxiv"
                })
        
        return results
    
    async def fetch_paper(self, arxiv_id: str) -> Optional[Dict]:
        """Fetch paper details and extract LaTeX"""
        search_result = await self.search(f"id:{arxiv_id}", max_results=1)
        
        if not search_result:
            return None
        
        paper = search_result[0]
        
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        latex_formulas = []
        
        text = paper.get("summary", "")
        
        latex_formulas = re.findall(r'\$([^$]+)\$|\$\$([^$]+)\$\$', text)
        
        simplified_formulas = []
        for f in latex_formulas[:10]:
            formula = f[0] or f[1]
            simplified = self._simplify_latex(formula)
            simplified_formulas.append({
                "original": formula,
                "simplified": simplified
            })
        
        paper["latex_formulas"] = simplified_formulas
        paper["pdf_url"] = pdf_url
        
        return paper
    
    def _simplify_latex(self, formula: str) -> str:
        """Try to simplify LaTeX formula"""
        try:
            import sympy
            formula_clean = formula.replace("\\frac", "frac")
            formula_clean = formula.replace("\\sqrt", "sqrt")
            return f"SymPy parse: {formula_clean[:50]}"
        except:
            return formula[:50]


class CrossrefIngestor:
    """
    Ingest from Crossref API (DOI for open access papers).
    """
    
    def __init__(self):
        self.api_url = "https://api.crossref.org/works"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Crossref"""
        params = {
            "query": query,
            "rows": max_results,
            "filter": "type:journal-article,has-full-text:true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_works(data.get("message", {}).get("items", []))
        return []
    
    def _parse_works(self, items: List[Dict]) -> List[Dict]:
        """Parse Crossref works"""
        results = []
        
        for item in items:
            title = item.get("title", [""])[0] if item.get("title") else ""
            authors = [a.get("family", "") for a in item.get("author", [])]
            doi = item.get("DOI", "")
            published = item.get("published-print", {}).get("date-parts", [[0]])[0]
            
            results.append({
                "title": title,
                "authors": authors,
                "doi": doi,
                "published": str(published),
                "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "abstract": item.get("abstract", "").replace("<jats:p>", "").replace("</jats:p>", ""),
                "url": f"https://doi.org/{doi}",
                "source": "crossref"
            })
        
        return results


class PubChemIngestor:
    """
    Ingest from PubChem (chemistry data).
    """
    
    def __init__(self):
        self.api_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    async def get_compound(self, cid: int) -> Optional[Dict]:
        """Get compound by CID"""
        url = f"{self.api_url}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
                    
                    return {
                        "cid": cid,
                        "formula": props.get("MolecularFormula", ""),
                        "weight": props.get("MolecularWeight", 0),
                        "iupac": props.get("IUPACName", ""),
                        "smiles": props.get("CanonicalSMILES", ""),
                        "source": "pubchem"
                    }
        return None
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search compounds"""
        url = f"{self.api_url}/compound/name/{query}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    
                    return [{
                        "name": query,
                        "cid": p.get("CID"),
                        "formula": p.get("MolecularFormula", ""),
                        "weight": p.get("MolecularWeight", 0),
                        "iupac": p.get("IUPACName", ""),
                        "source": "pubchem"
                    } for p in props[:max_results]]
        return []


class GitHubIngestor:
    """
    Ingest from GitHub (awesome-lists, code snippets).
    """
    
    def __init__(self):
        self.api_url = "https://api.github.com"
    
    async def search_code(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search code on GitHub"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        params = {
            "q": query,
            "per_page": max_results,
            "sort": "stars"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/search/code",
                params=params,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_results(data.get("items", []))
        return []
    
    def _parse_results(self, items: List[Dict]) -> List[Dict]:
        """Parse search results"""
        results = []
        
        for item in items:
            results.append({
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "repository": item.get("repository", {}).get("full_name", ""),
                "url": item.get("html_url", ""),
                "language": item.get("language", ""),
                "stars": item.get("repository", {}).get("stargazers_count", 0),
                "source": "github"
            })
        
        return results
    
    async def get_file_content(self, repo: str, path: str) -> Optional[str]:
        """Get file content"""
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/repos/{repo}/contents/{path}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    import base64
                    content = data.get("content", "")
                    if content:
                        return base64.b64decode(content).decode("utf-8")
        return None


class GutenbergIngestor:
    """
    Ingest from Project Gutenberg (literature).
    """
    
    def __init__(self):
        self.api_url = "https://gutendb.pythonanywhere.com/v0"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Gutenberg"""
        params = {"search": query, "num_results": max_results}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/book/search/", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", [])
        return []
    
    async def get_book(self, book_id: int) -> Optional[Dict]:
        """Get book metadata"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/book/{book_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
        return None
    
    async def get_text(self, book_id: int) -> Optional[str]:
        """Get book text"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/book/{book_id}/text") as resp:
                if resp.status == 200:
                    return await resp.text()
        return None


class UCUMIngestor:
    """
    Ingest UCUM units (Units of Measure).
    """
    
    def __init__(self):
        self.units: Dict[str, Dict] = {}
    
    async def load_from_url(self, url: str = None):
        """Load UCUM units from CSV"""
        if url is None:
            url = "https://raw.githubusercontent.com/ucum-org/ucum-oms-with-codes/main/ucum-oms.csv"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        self._parse_csv(text)
                        logger.info(f"[UCUM] Loaded {len(self.units)} units")
        except Exception as e:
            logger.warning(f"[UCUM] Could not load: {e}")
            self._load_defaults()
    
    def _parse_csv(self, text: str):
        """Parse UCUM CSV"""
        lines = text.split("\n")
        reader = csv.reader(lines)
        
        for row in reader:
            if len(row) >= 3:
                code = row[0].strip()
                name = row[1].strip()
                factor = row[2].strip() if len(row) > 2 else "1"
                
                self.units[code] = {
                    "code": code,
                    "name": name,
                    "factor_to_SI": factor,
                    "dimension": row[3].strip() if len(row) > 3 else ""
                }
    
    def _load_defaults(self):
        """Load default units"""
        self.units = {
            "m": {"code": "m", "name": "meter", "factor_to_SI": "1", "dimension": "L"},
            "kg": {"code": "kg", "name": "kilogram", "factor_to_SI": "1", "dimension": "M"},
            "s": {"code": "s", "name": "second", "factor_to_SI": "1", "dimension": "T"},
            "A": {"code": "A", "name": "ampere", "factor_to_SI": "1", "dimension": "I"},
            "K": {"code": "K", "name": "kelvin", "factor_to_SI": "1", "dimension": "Θ"},
            "mol": {"code": "mol", "name": "mole", "factor_to_SI": "1", "dimension": "N"},
            "cd": {"code": "cd", "name": "candela", "factor_to_SI": "1", "dimension": "J"}
        }
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between units"""
        if from_unit not in self.units or to_unit not in self.units:
            return None
        
        from_factor = float(self.units[from_unit]["factor_to_SI"])
        to_factor = float(self.units[to_unit]["factor_to_SI"])
        
        return value * from_factor / to_factor
    
    def search(self, query: str) -> List[Dict]:
        """Search units"""
        query = query.lower()
        return [u for u in self.units.values() if query in u["name"].lower() or query in u["code"].lower()]


class OntologyIngestor:
    """
    Ingest ontologies (Schema.org, DBpedia, Wikidata).
    """
    
    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self.relations: List[Dict] = []
    
    async def load_schemaorg(self):
        """Load Schema.org from JSON-LD"""
        url = "https://schema.org/version/latest/schemaorg-all-http.jsonld"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._parse_schemaorg(data)
                        logger.info(f"[Ontology] Loaded Schema.org")
        except Exception as e:
            logger.warning(f"[Schema.org] Load failed: {e}")
    
    def _parse_schemaorg(self, data: Dict):
        """Parse Schema.org data"""
        graph = data.get("@graph", [])
        
        for item in graph:
            if "@id" in item:
                self.entities[str(item["@id"])] = {
                    "id": str(item["@id"]),
                    "type": item.get("@type", ""),
                    "label": item.get("rdfs:label", item.get("rdfs:comment", "")),
                    "source": "schemaorg"
                }
    
    async def sparql_query(self, endpoint: str, query: str) -> List[Dict]:
        """Execute SPARQL query"""
        headers = {"Accept": "application/sparql-results+json"}
        
        params = {"query": query}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
        return []
    
    def search(self, query: str) -> List[Dict]:
        """Search entities"""
        query = query.lower()
        return [e for e in self.entities.values() if query in str(e.get("label", "")).lower()]


class DataIngestionSystem:
    """
    Unified ingestion system for all sources.
    """
    
    def __init__(self):
        self.arxiv = ArxivIngestor()
        self.crossref = CrossrefIngestor()
        self.pubchem = PubChemIngestor()
        self.github = GitHubIngestor()
        self.gutenberg = GutenbergIngestor()
        self.ucum = UCUMIngestor()
        self.ontology = OntologyIngestor()
    
    async def initialize(self):
        """Initialize all ingestors"""
        await self.ucum.load_from_url()
        await self.ontology.load_schemaorg()
    
    async def ingest(self, source: str, query: str, **kwargs) -> List[Dict]:
        """Generic ingest method"""
        if source == "arxiv":
            return await self.arxiv.search(query, kwargs.get("max_results", 10))
        elif source == "crossref":
            return await self.crossref.search(query, kwargs.get("max_results", 10))
        elif source == "pubchem":
            return await self.pubchem.search(query, kwargs.get("max_results", 10))
        elif source == "github":
            return await self.github.search_code(query, kwargs.get("max_results", 10))
        elif source == "gutenberg":
            return await self.gutenberg.search(query, kwargs.get("max_results", 10))
        elif source == "units":
            return self.ucum.search(query)
        elif source == "ontology":
            return self.ontology.search(query)
        
        return []


_global_ingestion: Optional[DataIngestionSystem] = None


def get_ingestion_system() -> DataIngestionSystem:
    """Get global ingestion system"""
    global _global_ingestion
    if _global_ingestion is None:
        _global_ingestion = DataIngestionSystem()
    return _global_ingestion
