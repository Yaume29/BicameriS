"""
Autonomous Scaffolding Module
=============================
Self-experimentation system for autonomous thinking.
The AI tests different modes, measures performance, and auto-adjusts.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import random

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
EXPERIMENTS_DIR = BASE_DIR / "storage" / "experiments"


@dataclass
class TestResult:
    mode: str
    timestamp: str
    latency_ms: float
    coherence_score: float
    reformulation_quality: float
    hardware_load: float
    success: bool
    error: Optional[str] = None


@dataclass
class ModePerformance:
    mode: str
    test_count: int
    avg_latency: float
    avg_coherence: float
    avg_reformulation: float
    success_rate: float
    recommendation: str


class AutonomousScaffolding:
    """
    Self-experimentation system for autonomous thinking modes.
    The AI tests different configurations and auto-tunes itself.
    """

    def __init__(self):
        self.experiments_file = EXPERIMENTS_DIR / "autonomous_tests.json"
        self.results: List[TestResult] = []
        self._load_results()
        self.current_test_mode: Optional[str] = None
        
    def _load_results(self):
        """Load previous test results"""
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        if self.experiments_file.exists():
            try:
                with open(self.experiments_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.results = [TestResult(**r) for r in data.get("results", [])]
            except Exception as e:
                logging.warning(f"[Scaffolding] Failed to load results: {e}")

    def _save_results(self):
        """Save test results to file"""
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "last_updated": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results]
        }
        with open(self.experiments_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def run_test(self, mode: str, test_prompt: str, hardware_metrics: Dict) -> TestResult:
        """
        Run a single test on a specific mode.
        Measures latency, coherence, and reformulation quality.
        """
        self.current_test_mode = mode
        start_time = time.time()
        
        try:
            result = await self._execute_mode_test(mode, test_prompt)
            latency = (time.time() - start_time) * 1000
            
            coherence = self._evaluate_coherence(result.get("response", ""))
            reformulation = self._evaluate_reformulation(
                test_prompt, 
                result.get("reformulated", "")
            )
            
            test_result = TestResult(
                mode=mode,
                timestamp=datetime.now().isoformat(),
                latency_ms=latency,
                coherence_score=coherence,
                reformulation_quality=reformulation,
                hardware_load=hardware_metrics.get("cpu_usage", 0.5),
                success=True
            )
            
        except Exception as e:
            test_result = TestResult(
                mode=mode,
                timestamp=datetime.now().isoformat(),
                latency_ms=0,
                coherence_score=0,
                reformulation_quality=0,
                hardware_load=hardware_metrics.get("cpu_usage", 0.5),
                success=False,
                error=str(e)
            )
        
        self.results.append(test_result)
        self._save_results()
        self.current_test_mode = None
        
        return test_result

    async def _execute_mode_test(self, mode: str, prompt: str) -> Dict:
        """Execute a test for a specific mode"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        reformulated = self._reformulate(prompt, mode)
        
        return {
            "response": f"[Mode: {mode}] Processed: {prompt[:50]}...",
            "reformulated": reformulated
        }

    def _reformulate(self, text: str, mode: str) -> str:
        """Simulate reformulation based on mode"""
        if mode == "relay":
            return f"RELAY: {text}"
        elif mode == "mirror":
            return text[::-1]
        elif mode == "whisper":
            return f"whisper: {text.lower()}"
        elif mode == "agent-mediate":
            return f"AGENT: {text}"
        return text

    def _evaluate_coherence(self, response: str) -> float:
        """Evaluate response coherence (0-1)"""
        if not response:
            return 0.0
        length_factor = min(len(response) / 100, 1.0)
        return 0.5 + (length_factor * 0.5)

    def _evaluate_reformulation(self, original: str, reformulated: str) -> float:
        """Evaluate reformulation quality (0-1)"""
        if not original or not reformulated:
            return 0.0
        
        original_words = set(original.lower().split())
        reformulated_words = set(reformulated.lower().split())
        
        if not original_words:
            return 0.0
            
        overlap = len(original_words & reformulated_words) / len(original_words)
        return 1.0 - overlap

    def get_mode_performance(self, mode: str) -> ModePerformance:
        """Get performance metrics for a specific mode"""
        mode_results = [r for r in self.results if r.mode == mode]
        
        if not mode_results:
            return ModePerformance(
                mode=mode,
                test_count=0,
                avg_latency=0,
                avg_coherence=0,
                avg_reformulation=0,
                success_rate=0,
                recommendation="Pas encore testé"
            )
        
        successful = [r for r in mode_results if r.success]
        success_rate = len(successful) / len(mode_results) if mode_results else 0
        
        return ModePerformance(
            mode=mode,
            test_count=len(mode_results),
            avg_latency=sum(r.latency_ms for r in successful) / len(successful) if successful else 0,
            avg_coherence=sum(r.coherence_score for r in successful) / len(successful) if successful else 0,
            avg_reformulation=sum(r.reformulation_quality for r in successful) / len(successful) if successful else 0,
            success_rate=success_rate,
            recommendation=self._generate_recommendation(successful)
        )

    def _generate_recommendation(self, results: List[TestResult]) -> str:
        """Generate recommendation based on test results"""
        if not results:
            return "Données insuffisantes"
        
        avg_latency = sum(r.latency_ms for r in results) / len(results)
        avg_coherence = sum(r.coherence_score for r in results) / len(results)
        
        if avg_latency < 200 and avg_coherence > 0.7:
            return "Excellent - Recommandé pour production"
        elif avg_latency < 500:
            return "Bon équilibre performance/qualité"
        else:
            return "Lent - Considerer l'optimisation"

    def get_best_mode(self, hardware_metrics: Dict = None) -> str:
        """
        Determine the best mode based on current hardware and past results.
        """
        modes = ["relay", "mirror", "whisper", "agent-mediate"]
        best_mode = "relay"
        best_score = -1
        
        cpu_limit = hardware_metrics.get("cpu_usage", 0.5) if hardware_metrics else 0.5
        
        for mode in modes:
            perf = self.get_mode_performance(mode)
            
            score = (
                perf.avg_coherence * 0.4 +
                (1.0 - min(perf.avg_latency / 1000, 1.0)) * 0.3 +
                perf.success_rate * 0.3
            )
            
            if mode == "agent-mediate" and cpu_limit > 0.7:
                score *= 0.5
            
            if score > best_score:
                best_score = score
                best_mode = mode
        
        return best_mode

    def auto_tune(self, hardware_metrics: Dict) -> Dict:
        """
        Automatically tune parameters based on hardware and past performance.
        Returns recommended configuration.
        """
        best_mode = self.get_best_mode(hardware_metrics)
        perf = self.get_mode_performance(best_mode)
        
        recommended_config = {
            "mode": best_mode,
            "reformulation_percentage": int(50 + (perf.avg_reformulation * 45)),
            "interval_ms": int(max(1000, perf.avg_latency * 2)),
            "confidence": perf.success_rate
        }
        
        return recommended_config

    def generate_experiment_report(self) -> str:
        """Generate a text report of all experiments"""
        modes = ["relay", "mirror", "whisper", "agent-mediate"]
        report = []
        report.append("=== RAPPORT D'EXPÉRIENCE AUTONOME ===")
        report.append(f"Date: {datetime.now().isoformat()}")
        report.append(f"Total tests: {len(self.results)}")
        report.append("")
        
        for mode in modes:
            perf = self.get_mode_performance(mode)
            report.append(f"--- {mode.upper()} ---")
            report.append(f"Tests: {perf.test_count}")
            report.append(f"Latence avg: {perf.avg_latency:.1f}ms")
            report.append(f"Cohérence: {perf.avg_coherence:.2f}")
            report.append(f"Reformulation: {perf.avg_reformulation:.2f}")
            report.append(f"Succès: {perf.success_rate*100:.1f}%")
            report.append(f"Recommandation: {perf.recommendation}")
            report.append("")
        
        best = self.get_best_mode()
        report.append(f">>> MODE RECOMMANDÉ: {best}")
        
        return "\n".join(report)


_scaffolding_instance: Optional[AutonomousScaffolding] = None


def get_autonomous_scaffolding() -> AutonomousScaffolding:
    """Get global autonomous scaffolding instance"""
    global _scaffolding_instance
    if _scaffolding_instance is None:
        _scaffolding_instance = AutonomousScaffolding()
    return _scaffolding_instance
