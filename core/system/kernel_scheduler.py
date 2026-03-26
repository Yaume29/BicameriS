"""
BICAMERIS - Kernel Scheduler (Master Clock)
==========================================
Single pacemaker that orchestrates cognitive ticks.
Replaces scattered while loops with centralized tick() calls.
"""

import asyncio
import logging
from typing import Optional, Dict, Any


class KernelScheduler:
    """
    The Master Clock - unique source of cognitive rhythm.
    Controls all autonomous loops via Switchboard state.
    """

    def __init__(self, switchboard, corps_calleux, conductor, entropy=None):
        self.switchboard = switchboard
        self.corps_calleux = corps_calleux
        self.conductor = conductor
        self.entropy = entropy

        self._is_running = False
        self._is_thinking = False
        self._is_dreaming = False
        self._dream_cooldown = 0
        self._task: Optional[asyncio.Task] = None
        self._base_interval = 2.0
        self._force_tick_event = asyncio.Event()

        logging.info("[KernelScheduler] ✅ Master Clock initialized")

    async def start(self):
        """Start the master clock"""
        if self._is_running:
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logging.info("[KernelScheduler] ⏱️ Master Clock: ON")

    async def stop(self):
        """Stop the master clock"""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logging.info("[KernelScheduler] ⏹️ Master Clock: OFF")

    async def _run_loop(self):
        """Main loop - checks switchboard and triggers ticks"""
        from core.system.endocrine import get_endocrine_system

        while self._is_running:
            try:
                if not self.switchboard.is_active("autonomous_loop"):
                    await asyncio.sleep(1.0)
                    continue

                # Metabolisme endocrinien
                get_endocrine_system().decay()

                pulse = 0.5
                if self.entropy:
                    try:
                        pulse = self.entropy.get_pulse()
                    except:
                        pass

                if self._dream_cooldown > 0:
                    self._dream_cooldown -= 1

                if pulse < 0.2 and not self._is_dreaming and self._dream_cooldown == 0:
                    logging.info(
                        "[KernelScheduler] 💤 Entropie très basse. Activation du DMN (Dreamer)."
                    )
                    from core.cognition.dreamer_agent import get_dreamer_agent

                    dreamer = get_dreamer_agent()
                    if dreamer and dreamer.is_available():
                        self._is_dreaming = True
                        await asyncio.to_thread(dreamer.trigger_rem_sleep)
                        from core.system.endocrine import get_endocrine_system

                        get_endocrine_system().spike_dopamine(0.1)
                        self._dream_cooldown = 10

                    interval = self._calculate_interval(pulse)
                    try:
                        await asyncio.wait_for(self._force_tick_event.wait(), timeout=interval)
                        self._force_tick_event.clear()
                    except asyncio.TimeoutError:
                        pass
                    continue
                elif self._is_dreaming and pulse >= 0.2:
                    self._is_dreaming = False

                tasks = []
                if self.corps_calleux:
                    if self.switchboard.is_active("autonomous_loop") and not self._is_thinking:
                        self._is_thinking = True

                        async def _think_worker():
                            try:
                                await asyncio.to_thread(self.corps_calleux.tick, pulse)
                            finally:
                                self._is_thinking = False

                        asyncio.create_task(_think_worker())

                interval = self._calculate_interval(pulse)
                try:
                    await asyncio.wait_for(self._force_tick_event.wait(), timeout=interval)
                    self._force_tick_event.clear()
                except asyncio.TimeoutError:
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[KernelScheduler] Tick error: {e}")
                await asyncio.sleep(1.0)

    def _calculate_interval(self, pulse: float) -> float:
        """Dynamic rhythm based on system entropy"""
        if pulse > 0.75:
            return 0.5  # High entropy = fast thinking
        elif pulse > 0.5:
            return 1.0
        elif pulse < 0.25:
            return 5.0  # Low entropy = slow, contemplative
        return self._base_interval

    def tick_now(self) -> Dict[str, Any]:
        """Manual trigger for one tick (non-async)"""
        if self._is_running:
            self._force_tick_event.set()
            return {"status": "Tick asynchrone commandé"}
        return {"error": "Horloge arrêtée"}

    def is_running(self) -> bool:
        """Check if master clock is active"""
        return self._is_running


_scheduler = None


def get_kernel_scheduler() -> KernelScheduler:
    global _scheduler
    return _scheduler


def init_kernel_scheduler(switchboard, corps_calleux, conductor, entropy=None) -> KernelScheduler:
    global _scheduler
    _scheduler = KernelScheduler(switchboard, corps_calleux, conductor, entropy)
    return _scheduler
