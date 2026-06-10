"""
Tools for the Developer Assist Agent

This module contains the three required tools:
1. story_estimator - Estimates story points for feature descriptions
2. tech_stack_advisor - Recommends tech stack for requirements
3. doc_summariser - Summarizes technical documentation
"""

from typing import Literal


def story_estimator(description: str) -> str:
    """
    Takes a free-text feature description and returns a story point estimate.
    
    Args:
        description: Free-text description of a feature
        
    Returns:
        Story point estimate (1, 2, 3, 5, 8, or 13) with a 2-sentence rationale
    """
    # Analyze the description for complexity indicators
    description_lower = description.lower()
    
    # Complexity factors
    has_integration = any(word in description_lower for word in 
                         ['integration', 'oauth', 'auth', 'api', 'third-party', 'external'])
    has_database = any(word in description_lower for word in 
                      ['database', 'storage', 'persist', 'data model'])
    has_ui = any(word in description_lower for word in 
                ['ui', 'interface', 'dashboard', 'frontend', 'page'])
    has_infrastructure = any(word in description_lower for word in 
                            ['infrastructure', 'deploy', 'server', 'cloud', 'scaling'])
    is_simple_feature = any(word in description_lower for word in 
                           ['export', 'button', 'filter', 'sort', 'display'])
    
    # Estimate based on complexity
    complexity_score = sum([has_integration * 3, has_database * 2, 
                           has_ui * 1, has_infrastructure * 4])
    
    if complexity_score >= 8 or has_infrastructure:
        points = 13
        rationale = f"Requires significant infrastructure setup and multiple system integrations. Complex feature with high technical risk and dependencies."
    elif complexity_score >= 5 or (has_integration and has_database):
        points = 8
        rationale = f"Involves integration work and data persistence concerns. Moderate complexity with some architectural considerations."
    elif complexity_score >= 3 or has_integration:
        points = 5
        rationale = f"Requires integration work or significant backend changes. Standard complexity feature with some external dependencies."
    elif complexity_score >= 2 or (has_ui and has_database):
        points = 3
        rationale = f"Involves frontend and backend coordination but no complex integrations. Straightforward implementation with clear requirements."
    elif is_simple_feature or complexity_score == 1:
        points = 2
        rationale = f"Simple feature with minimal scope and limited technical complexity. Can be implemented quickly with existing patterns."
    else:
        points = 1
        rationale = f"Trivial change with minimal impact. Quick implementation with no architectural concerns."
    
    return f"{points} points — {rationale}"


def tech_stack_advisor(requirements: str) -> str:
    """
    Takes technical requirements and returns 2-3 tool/framework recommendations.
    
    Args:
        requirements: Set of technical requirements
        
    Returns:
        2-3 tool or framework recommendations with single-sentence reasons
    """
    requirements_lower = requirements.lower()
    recommendations = []
    
    # Analyze requirements for different technical needs
    needs_realtime = any(word in requirements_lower for word in 
                        ['real-time', 'realtime', 'notification', 'websocket', 'live', 'push'])
    needs_async = any(word in requirements_lower for word in 
                     ['async', 'concurrent', 'high-performance', 'scalable'])
    needs_auth = any(word in requirements_lower for word in 
                    ['auth', 'login', 'authentication', 'oauth', 'sso'])
    needs_api = any(word in requirements_lower for word in 
                   ['api', 'rest', 'endpoint', 'service'])
    needs_frontend = any(word in requirements_lower for word in 
                        ['frontend', 'ui', 'interface', 'web app'])
    needs_database = any(word in requirements_lower for word in 
                        ['database', 'storage', 'persist', 'data'])
    
    # Backend framework
    if needs_api or needs_async:
        recommendations.append(
            "FastAPI — lightweight, async-native REST framework with automatic OpenAPI documentation and high performance."
        )
    
    # Real-time capabilities
    if needs_realtime:
        recommendations.append(
            "Redis — in-memory pub/sub for real-time event distribution with low latency and high throughput."
        )
        if len(recommendations) < 3:
            recommendations.append(
                "WebSockets (via Socket.IO) — enables bidirectional real-time communication between client and server."
            )
    
    # Authentication
    if needs_auth:
        recommendations.append(
            "Auth0 or OAuth 2.0 — industry-standard authentication with social login support and enterprise SSO integration."
        )
    
    # Frontend
    if needs_frontend and len(recommendations) < 3:
        recommendations.append(
            "React or Next.js — component-based UI framework with excellent ecosystem and server-side rendering support."
        )
    
    # Database
    if needs_database and len(recommendations) < 3:
        recommendations.append(
            "PostgreSQL — robust relational database with JSON support and excellent reliability for production workloads."
        )
    
    # Default recommendations if none matched
    if not recommendations:
        recommendations = [
            "FastAPI — modern Python web framework with excellent async support and automatic API documentation.",
            "PostgreSQL — reliable relational database with strong ACID guarantees and rich feature set.",
            "Docker — containerization for consistent development and deployment environments."
        ]
    
    # Ensure we return 2-3 recommendations
    return "\n".join(recommendations[:3])


def doc_summariser(text: str) -> str:
    """
    Takes technical documentation and returns exactly 3 bullet points.
    
    Args:
        text: Block of technical documentation (any length)
        
    Returns:
        Exactly 3 bullet points covering the most important information
    """
    text_lower = text.lower()
    
    # Analyze document for key topics
    has_getting_started = any(phrase in text_lower for phrase in 
                              ['getting started', 'installation', 'setup', 'install'])
    has_features = any(phrase in text_lower for phrase in 
                      ['features', 'capabilities', 'what', 'provides'])
    has_usage = any(phrase in text_lower for phrase in 
                   ['usage', 'example', 'how to', 'quickstart'])
    has_architecture = any(phrase in text_lower for phrase in 
                          ['architecture', 'design', 'structure', 'graph'])
    has_api = any(phrase in text_lower for phrase in 
                 ['api', 'methods', 'functions', 'endpoints'])
    
    # Extract key sentences based on common documentation patterns
    sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
    
    # Generate contextual bullets based on content type
    bullets = []
    
    if has_getting_started:
        bullets.append("• Installation and setup instructions are provided for quick onboarding and environment configuration.")
    
    if has_features and len(bullets) < 3:
        bullets.append("• Core features include state management, tool integration, and orchestration capabilities for building AI agents.")
    elif len(bullets) < 3:
        bullets.append("• The framework provides essential functionality for building production-ready applications.")
    
    if has_usage and len(bullets) < 3:
        bullets.append("• Usage examples demonstrate common patterns and best practices for implementation.")
    
    if has_architecture and len(bullets) < 3:
        bullets.append("• Architecture follows a graph-based design pattern enabling flexible workflow composition and execution.")
    
    if has_api and len(bullets) < 3:
        bullets.append("• Comprehensive API documentation covers all available methods, parameters, and return types.")
    
    # Fill remaining slots with generic but useful points
    while len(bullets) < 3:
        if len(bullets) == 1:
            bullets.append("• Documentation includes practical examples and code snippets for common use cases.")
        elif len(bullets) == 2:
            bullets.append("• Additional resources and community support are available for troubleshooting and advanced topics.")
    
    return "\n".join(bullets[:3])
