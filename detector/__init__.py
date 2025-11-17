"""
AgentDebug Error Detection System

This package provides error detection and analysis for LLM agent trajectories.
"""

from .error_definitions import ErrorDefinitionsLoader
from .fine_grained_analysis import ErrorTypeDetector, ModuleError, StepAnalysis
from .critical_error_detection import CriticalErrorAnalyzer, CriticalError

__all__ = [
    'ErrorDefinitionsLoader',
    'ErrorTypeDetector',
    'ModuleError',
    'StepAnalysis',
    'CriticalErrorAnalyzer',
    'CriticalError',
]
