"""
Tests for reasoning_kernel module
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.cognition.reasoning_kernel import ReasoningKernel, get_reasoning_kernel, MCTSNode


class TestMCTSNode:
    """Tests for MCTSNode class"""
    
    def test_node_creation(self):
        """Test node creation"""
        node = MCTSNode(state="test")
        assert node.state == "test"
        assert node.visits == 0
        assert node.value == 0.0
        assert len(node.children) == 0
    
    def test_ucb1_unvisited(self):
        """Test UCB1 for unvisited node"""
        parent = MCTSNode(state="parent")
        parent.visits = 10
        
        child = MCTSNode(state="child", parent=parent)
        assert child.ucb1() == float('inf')
    
    def test_ucb1_visited(self):
        """Test UCB1 for visited node"""
        parent = MCTSNode(state="parent")
        parent.visits = 100
        
        child = MCTSNode(state="child", parent=parent)
        child.visits = 10
        child.value = 5.0
        
        ucb = child.ucb1()
        assert ucb != float('inf')
        assert ucb > 0
    
    def test_expand(self):
        """Test node expansion"""
        node = MCTSNode(state="root")
        actions = ["action1", "action2", "action3"]
        
        child = node.expand(actions)
        assert len(node.children) == 1
        assert child.parent == node
        assert child.action in actions


class TestReasoningKernel:
    """Tests for ReasoningKernel class"""
    
    def test_initialization(self):
        """Test kernel initialization"""
        kernel = ReasoningKernel()
        assert not kernel.is_initialized
        assert kernel.logic_hemi is None
        assert kernel.intuition_hemi is None
    
    def test_initialize_with_hemispheres(self):
        """Test kernel initialization with hemispheres"""
        kernel = ReasoningKernel()
        kernel.initialize(logic_hemi=None, intuition_hemi=None)
        assert kernel.is_initialized
    
    def test_solve_without_hemispheres(self):
        """Test solve without hemispheres (fallback)"""
        kernel = ReasoningKernel()
        kernel.is_initialized = True
        
        result = kernel.solve("test problem", iterations=10)
        
        assert "solution" in result
        assert "confidence" in result
        assert "nodes_explored" in result
        assert "time_ms" in result
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        kernel = ReasoningKernel()
        stats = kernel.get_stats()
        
        assert "initialized" in stats
        assert "logic_hemi_available" in stats
        assert "intuition_hemi_available" in stats
        assert "total_solves" in stats
    
    def test_configure(self):
        """Test configuration"""
        kernel = ReasoningKernel()
        kernel.configure(iterations=500, exploration=2.0)
        
        assert kernel.iterations == 500
        assert kernel.exploration == 2.0


class TestGetReasoningKernel:
    """Tests for get_reasoning_kernel function"""
    
    def test_returns_singleton(self):
        """Test that function returns singleton"""
        # Reset global instance
        import core.cognition.reasoning_kernel as rk_module
        rk_module._reasoning_kernel = None
        
        kernel1 = get_reasoning_kernel()
        kernel2 = get_reasoning_kernel()
        
        assert kernel1 is kernel2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
