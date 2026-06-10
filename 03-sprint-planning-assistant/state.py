"""
State management for the Sprint Planning Assistant

This module defines the state schema for the supervisor-worker pattern.
The supervisor routes requests to specialist workers, and all sprint data
is managed through FastMCP.
"""

from typing import TypedDict, List, Optional


class SprintState(TypedDict):
    """
    State schema for the Sprint Planning Assistant
    
    Tracks the conversation flow through the supervisor-worker graph:
    - user_request: Original user query
    - messages: Accumulated conversation history
    - worker_results: Results from worker nodes
    - next_action: Supervisor's routing decision
    """
    # User's original request
    user_request: str
    
    # Conversation history (formatted messages)
    messages: List[str]
    
    # Results from worker nodes
    worker_results: List[str]
    
    # Supervisor's routing decision
    next_action: Optional[str]
    
    # Flag to continue or finish
    should_continue: bool
