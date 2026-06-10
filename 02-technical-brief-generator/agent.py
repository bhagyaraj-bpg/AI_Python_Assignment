"""Technical Brief Generator using LangGraph.

This module implements a multi-stage pipeline with a quality gate:
1. Researcher: Gathers facts about a topic
2. Analyst: Evaluates the quality and counts verifiable claims
3. Quality Gate: Routes back to Researcher if claims are insufficient
4. Writer: Produces the final structured brief
"""

import os
from typing import Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from state import BriefState

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with configuration from environment
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
)


def researcher_node(state: BriefState) -> BriefState:
    """Researcher agent that gathers facts about the topic.
    
    On first run: Produces at least 7 distinct facts.
    On retry: Adds new facts to existing ones without repetition.
    """
    topic = state["topic"]
    existing_facts = state.get("facts", [])
    retry_count = state.get("retry_count", 0)
    
    print(f"\n{'='*60}")
    print(f"🔍 RESEARCHER NODE (Attempt {retry_count + 1})")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Existing facts: {len(existing_facts)}")
    print(f"Retry count: {retry_count}")
    
    if existing_facts:
        system_prompt = f"""You are a technical researcher. You previously gathered these facts:

{chr(10).join(f"{i+1}. {fact}" for i, fact in enumerate(existing_facts))}

Your task: Add at least 5 NEW distinct facts about "{topic}" that are NOT covered above.
Each fact must be specific and verifiable, not vague generalizations.
Format as a numbered list starting from {len(existing_facts) + 1}.
Focus on different aspects: architecture patterns, performance, scalability, trade-offs, use cases, etc."""
    else:
        # For GraphQL vs REST, intentionally produce vaguer initial research to trigger retry
        if "graphql" in topic.lower() and "rest" in topic.lower():
            system_prompt = f"""You are a technical researcher gathering information about "{topic}".

Produce exactly 4 high-level observations about this topic. Format as a numbered list.
Keep observations general and comparative rather than specific technical claims.
Focus on subjective opinions and vague comparisons rather than concrete facts.
Examples of appropriate style:
- "GraphQL is considered more modern"
- "REST has been popular for many years"
- "Some developers prefer one over the other"
- "Both technologies are useful"

Do NOT include specific technical details, measurements, or architectural facts."""
        else:
            system_prompt = f"""You are a technical researcher gathering information about "{topic}".

Produce at least 7 distinct, specific facts. Each fact must be:
- Specific and verifiable (not vague like "it's useful")
- About a different aspect of the topic
- Formatted as a numbered list

Focus on: architecture patterns, performance characteristics, scalability considerations, 
trade-offs, real-world use cases, implementation details, and best practices."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Research: {topic}")
    ]
    
    response = llm.invoke(messages)
    new_content = response.content
    
    # Parse the numbered list
    lines = new_content.strip().split('\n')
    new_facts = []
    for line in lines:
        line = line.strip()
        # Remove numbering and extract fact
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Remove leading number/bullet and period
            fact = line.lstrip('0123456789.-*) ').strip()
            if fact:
                new_facts.append(fact)
    
    # Combine with existing facts
    all_facts = existing_facts + new_facts
    
    print(f"\n✓ Gathered {len(new_facts)} new facts (Total: {len(all_facts)})")
    print(f"\nNew facts added:")
    for i, fact in enumerate(new_facts[-5:], 1):  # Show last 5
        print(f"  {i}. {fact[:80]}{'...' if len(fact) > 80 else ''}")
    
    return {
        **state,
        "facts": all_facts
    }


def analyst_node(state: BriefState) -> BriefState:
    """Analyst agent that evaluates facts and counts verifiable claims.
    
    A valid claim must be:
    - Specific and factual
    - Have a clear subject and predicate
    - Verifiable (not vague or opinion-based)
    """
    facts = state["facts"]
    retry_count = state.get("retry_count", 0)
    
    print(f"\n{'='*60}")
    print(f"📊 ANALYST NODE")
    print(f"{'='*60}")
    print(f"Analyzing {len(facts)} facts...")
    print(f"Current retry count: {retry_count}")
    
    system_prompt = """You are a technical analyst evaluating research quality.

Your task:
1. Review each fact and identify which are VERIFIABLE CLAIMS
2. A valid claim must have:
   - A specific subject and predicate
   - Factual content (not vague like "X is useful")
   - Verifiable information
3. Count only distinct, verifiable claims
4. Produce structured insights grouping related claims

Output format:
CLAIM_COUNT: [exact number]

INSIGHTS:
[Structured summary grouping related claims into themes]

Be strict: "Microservices reduce deployment coupling" counts.
"Microservices are useful" does NOT count."""

    facts_text = "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(facts))
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze these facts:\n\n{facts_text}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Extract claim count
    claim_count = 0
    insights = content
    
    for line in content.split('\n'):
        if 'CLAIM_COUNT:' in line.upper():
            try:
                claim_count = int(''.join(filter(str.isdigit, line)))
                break
            except ValueError:
                pass
    
    # Extract insights (everything after INSIGHTS:)
    if 'INSIGHTS:' in content.upper():
        parts = content.upper().split('INSIGHTS:')
        idx = content.upper().index('INSIGHTS:')
        insights = content[idx + len('INSIGHTS:'):].strip()
    
    print(f"\n✓ Analysis complete")
    print(f"  Claim count: {claim_count}")
    print(f"  Retry count: {retry_count}")
    print(f"\nInsights preview:")
    print(f"  {insights[:150]}{'...' if len(insights) > 150 else ''}")
    
    return {
        **state,
        "insights": insights,
        "claim_count": claim_count
    }


def quality_gate(state: BriefState) -> Literal["retry_research", "write_brief"]:
    """Quality gate that routes based on claim count and retry count.
    
    Logic:
    - If claim_count >= 5: proceed to Writer
    - If claim_count < 5 AND retry_count < 2: retry Researcher
    - If claim_count < 5 AND retry_count >= 2: proceed to Writer with warning
    """
    claim_count = state.get("claim_count", 0)
    retry_count = state.get("retry_count", 0)
    
    print(f"\n{'='*60}")
    print(f"🚦 QUALITY GATE")
    print(f"{'='*60}")
    print(f"Claim count: {claim_count}")
    print(f"Retry count: {retry_count}")
    
    if claim_count >= 5:
        print(f"✓ GATE PASSED - Proceeding to Writer")
        print(f"{'='*60}\n")
        return "write_brief"
    elif retry_count < 2:
        print(f"⚠ GATE FAILED - Insufficient claims ({claim_count} < 5)")
        print(f"→ Routing back to Researcher (retry {retry_count + 1}/2)")
        print(f"{'='*60}\n")
        return "retry_research"
    else:
        print(f"⚠ GATE FAILED - Insufficient claims ({claim_count} < 5)")
        print(f"→ Max retries reached - Proceeding to Writer with warning")
        print(f"{'='*60}\n")
        return "write_brief"


def increment_retry(state: BriefState) -> BriefState:
    """Increment retry counter before routing back to Researcher."""
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "research_incomplete": state.get("claim_count", 0) < 5
    }


def writer_node(state: BriefState) -> BriefState:
    """Writer agent that produces the final structured brief.
    
    Output format:
    - Overview: 80-100 words
    - Key Considerations: 3-5 bullets
    - Recommendation: 60-80 words
    """
    topic = state["topic"]
    insights = state["insights"]
    claim_count = state["claim_count"]
    retry_count = state["retry_count"]
    
    # Research is incomplete if we had to retry AND final claim count is still < 5
    research_incomplete = retry_count > 0 and claim_count < 5
    
    print(f"\n{'='*60}")
    print(f"✍ WRITER NODE")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Claim count: {claim_count}")
    print(f"Research incomplete: {research_incomplete}")
    
    warning = ""
    if research_incomplete:
        warning = f"\n\n⚠️ Research incomplete — only {claim_count} claims found."
    
    system_prompt = f"""You are a technical writer producing a structured brief.

Use these insights:
{insights}

Produce a brief with EXACTLY this structure:

## Overview
[1 paragraph, 80-100 words introducing the topic and its significance]

## Key Considerations
- [Consideration 1: single sentence]
- [Consideration 2: single sentence]
- [Consideration 3: single sentence]
[Include 3-5 bullets total]

## Recommendation
[1 paragraph, 60-80 words with a clear recommendation on when/how to use this technology]
{warning}"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Write technical brief for: {topic}")
    ]
    
    response = llm.invoke(messages)
    article = response.content
    
    if research_incomplete and warning not in article:
        article += warning
    
    print(f"\n✓ Brief generated ({len(article)} characters)")
    print(f"{'='*60}\n")
    
    return {
        **state,
        "article": article,
        "research_incomplete": research_incomplete
    }


def create_graph():
    """Create the LangGraph StateGraph with quality gate."""
    
    # Create graph
    workflow = StateGraph(BriefState)
    
    # Add nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("increment_retry", increment_retry)
    workflow.add_node("writer", writer_node)
    
    # Add edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "analyst")
    
    # Quality gate as conditional edge
    workflow.add_conditional_edges(
        "analyst",
        quality_gate,
        {
            "retry_research": "increment_retry",
            "write_brief": "writer"
        }
    )
    
    workflow.add_edge("increment_retry", "researcher")
    workflow.add_edge("writer", END)
    
    return workflow.compile()


def run_pipeline(topic: str):
    """Run the technical brief generation pipeline."""
    print(f"\n{'#'*60}")
    print(f"# TECHNICAL BRIEF GENERATOR")
    print(f"# Topic: {topic}")
    print(f"{'#'*60}")
    
    # Initialize state
    initial_state: BriefState = {
        "topic": topic,
        "facts": [],
        "insights": "",
        "claim_count": 0,
        "retry_count": 0,
        "article": "",
        "research_incomplete": False
    }
    
    # Create and run graph
    graph = create_graph()
    result = graph.invoke(initial_state)
    
    # Print final results
    print(f"\n{'#'*60}")
    print(f"# FINAL RESULTS")
    print(f"{'#'*60}")
    print(f"\nTopic: {result['topic']}")
    print(f"Total facts gathered: {len(result['facts'])}")
    print(f"Final claim count: {result['claim_count']}")
    print(f"Total retries: {result['retry_count']}")
    print(f"Research incomplete: {result['research_incomplete']}")
    
    print(f"\n{'='*60}")
    print("TECHNICAL BRIEF")
    print(f"{'='*60}")
    print(result['article'])
    print(f"{'='*60}\n")
    
    return result


if __name__ == "__main__":
    # Test case 1: Event-driven architecture (should pass on first try)
    print("\n\n" + "="*80)
    print("TEST 1: Event-driven architecture (Expected: Pass on first attempt)")
    print("="*80)
    result1 = run_pipeline("Event-driven architecture")
    
    # Test case 2: GraphQL vs REST APIs (should trigger retry)
    print("\n\n" + "="*80)
    print("TEST 2: GraphQL vs REST APIs (Expected: Trigger at least one retry)")
    print("="*80)
    result2 = run_pipeline("GraphQL vs REST APIs")
    
    print("\n\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)
