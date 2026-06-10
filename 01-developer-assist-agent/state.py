"""
State management for the Developer Assist Agent

This module defines the state schema for tracking reasoning steps,
tool calls, observations, and final answers in the ReAct loop.
"""

from typing import TypedDict, Literal, Optional, List
from dataclasses import dataclass


@dataclass
class ReasoningStep:
    """Represents a single step in the ReAct loop"""
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


class AgentState(TypedDict):
    """
    State schema for the Developer Assist Agent
    
    Tracks the complete reasoning trace through the ReAct loop:
    - Thoughts: What the agent is reasoning about
    - Actions: Tools to call
    - Observations: Tool outputs
    - Final Answer: Synthesized response
    """
    # User's original query
    query: str
    
    # Reasoning trace - list of steps
    reasoning_steps: List[ReasoningStep]
    
    # Current iteration count (for 6-iteration guard)
    iteration_count: int
    
    # Final answer when ready
    final_answer: Optional[str]
    
    # Flag to indicate if we should continue looping
    should_continue: bool
