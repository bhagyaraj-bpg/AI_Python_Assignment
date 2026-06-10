"""State management for Engineering Knowledge Base Q&A agent."""

from typing import TypedDict, List, Dict, Any


class KnowledgeBaseState(TypedDict):
    """State for the knowledge base Q&A agent."""
    
    # Input
    question: str
    
    # Retrieved documents from FAISS
    retrieved_docs: List[Dict[str, Any]]
    
    # Documents that passed relevance grading
    relevant_docs: List[Dict[str, Any]]
    
    # Grading trace for logging
    grading_trace: List[str]
    
    # Final answer
    answer: str
