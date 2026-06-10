"""State management for Technical Brief Generator.

This module defines the state schema used across all nodes in the pipeline.
"""

from typing import TypedDict, List


class BriefState(TypedDict):
    """State schema for the technical brief generation pipeline.
    
    Attributes:
        topic: The topic to research and write about
        facts: List of distinct facts gathered by the Researcher
        insights: Structured insights distilled by the Analyst
        claim_count: Number of distinct, verifiable claims found
        retry_count: Number of times the Researcher has been retried
        article: Final structured brief produced by the Writer
        research_incomplete: Flag indicating if research was insufficient
    """
    topic: str
    facts: List[str]
    insights: str
    claim_count: int
    retry_count: int
    article: str
    research_incomplete: bool
