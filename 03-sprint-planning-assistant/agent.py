"""
Sprint Planning Assistant - Supervisor + FastMCP

Pattern: Supervisor Agent with specialist workers
Architecture: Central LLM router dispatching to specialist workers via FastMCP

The supervisor analyzes user requests and routes to:
- Sprint Builder: Decomposes features into tasks
- Capacity Checker: Analyzes sprint capacity and velocity
- Risk Assessor: Identifies blockers and concerns

All sprint data is managed through FastMCP - no direct Python object sharing.
"""

import os
import json
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI

from langgraph.graph import StateGraph, END
from state import SprintState

# Import MCP tools directly (simpler approach for educational purposes)
# In production, you'd use the full MCP protocol with server/client
import mcp_server

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def supervisor_node(state: SprintState) -> SprintState:
    """
    Supervisor node that analyzes requests and routes to specialist workers.
    
    Routing rules:
    - 'Plan [feature]' / 'Add tasks' / 'Break down' → Sprint Builder
    - 'Check capacity' / 'How many SP' / 'Velocity' → Capacity Checker
    - 'Any risks' / 'What could go wrong' / 'Blockers' → Risk Assessor
    - 'Done' / 'That's all' / 'Quit' → FINISH
    """
    user_request = state["user_request"]
    
    print(f"\n{'='*60}")
    print("🎯 SUPERVISOR NODE")
    print(f"{'='*60}")
    print(f"User Request: {user_request}")
    
    # Build routing prompt
    routing_prompt = f"""You are a sprint planning supervisor. Analyze the user request and route to the appropriate worker.

User Request: "{user_request}"

Available Workers:
1. sprint_builder - Decomposes features into 3-5 tasks with story points
2. capacity_checker - Analyzes sprint capacity and velocity
3. risk_assessor - Identifies risks, blockers, and concerns
4. finish - User is done with requests

Routing Rules:
- Keywords 'plan', 'add tasks', 'break down', 'create', 'feature' → sprint_builder
- Keywords 'capacity', 'velocity', 'how many SP', 'budget', 'points' → capacity_checker
- Keywords 'risk', 'blockers', 'concerns', 'go wrong', 'issues' → risk_assessor
- Keywords 'done', 'that's all', 'quit', 'finish', 'nothing else' → finish

Respond with ONLY the worker name in lowercase: sprint_builder, capacity_checker, risk_assessor, or finish."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": routing_prompt}],
        temperature=0.3
    )
    
    next_action = response.choices[0].message.content.strip().lower()
    
    print(f"Routing Decision: {next_action}")
    
    # Update state
    state["next_action"] = next_action
    state["should_continue"] = (next_action != "finish")
    
    return state


def sprint_builder_node(state: SprintState) -> SprintState:
    """
    Sprint Builder worker: Decomposes features into 3-5 tasks.
    Calls LLM to break down the feature, then calls add_task via MCP for each.
    """
    user_request = state["user_request"]
    
    print(f"\n{'='*60}")
    print("🏗️ SPRINT BUILDER NODE")
    print(f"{'='*60}")
    
    # Step 1: Use LLM to decompose feature into tasks
    decompose_prompt = f"""You are a sprint planning expert. Break down this feature request into 3-5 concrete tasks.

Feature Request: "{user_request}"

For each task, provide:
1. Clear, actionable title (5-10 words)
2. Suggested assignee (use realistic developer names like "Alice", "Bob", "Charlie", etc.)
3. Story point estimate (1, 2, 3, 5, 8, or 13)

Respond with ONLY a JSON array of tasks:
[
  {{"title": "...", "assignee": "...", "story_points": 3}},
  ...
]"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": decompose_prompt}],
        temperature=0.7
    )
    
    tasks_json = response.choices[0].message.content.strip()
    # Extract JSON from markdown code blocks if present
    if "```json" in tasks_json:
        tasks_json = tasks_json.split("```json")[1].split("```")[0].strip()
    elif "```" in tasks_json:
        tasks_json = tasks_json.split("```")[1].split("```")[0].strip()
    
    tasks = json.loads(tasks_json)
    
    print(f"LLM generated {len(tasks)} tasks")
    
    # Step 2: Call add_task via MCP for each task
    added_tasks = []
    
    for task in tasks:
        result = mcp_server.add_task(
            title=task["title"],
            assignee=task["assignee"],
            story_points=task["story_points"]
        )
        added_tasks.append(f"{task['title']} ({task['story_points']} SP)")
        print(f"  ✓ {result}")
    
    # Step 3: Format summary
    summary = f"Created {len(tasks)} tasks for feature: {', '.join(added_tasks)}"
    
    print(f"\nResult: {summary}")
    
    # Update state
    state["worker_results"] = state.get("worker_results", []) + [summary]
    state["messages"] = state.get("messages", []) + [f"Sprint Builder: {summary}"]
    
    return state


def capacity_checker_node(state: SprintState) -> SprintState:
    """
    Capacity Checker worker: Analyzes sprint capacity.
    Calls check_capacity via MCP and provides recommendations.
    """
    print(f"\n{'='*60}")
    print("📊 CAPACITY CHECKER NODE")
    print(f"{'='*60}")
    
    # Call check_capacity via MCP
    capacity_status = mcp_server.check_capacity(velocity=40)
    print(f"Capacity Status: {capacity_status}")
    
    # Parse the result to determine recommendation
    if "Over capacity" in capacity_status:
        # Get backlog to suggest a task to descope
        backlog = mcp_server.get_backlog()
        
        recommendation = "Recommend descoping lowest priority task or splitting large tasks."
    elif "Under capacity" in capacity_status:
        recommendation = "Sprint has room for additional items."
    else:
        recommendation = "Sprint is balanced at target velocity."
    
    summary = f"{capacity_status} {recommendation}"
    
    print(f"Recommendation: {recommendation}")
    
    # Update state
    state["worker_results"] = state.get("worker_results", []) + [summary]
    state["messages"] = state.get("messages", []) + [f"Capacity Checker: {summary}"]
    
    return state


def risk_assessor_node(state: SprintState) -> SprintState:
    """
    Risk Assessor worker: Identifies risks and blockers.
    Calls get_backlog and get_risk_summary, then uses LLM to identify 2-3 specific risks.
    """
    print(f"\n{'='*60}")
    print("⚠️ RISK ASSESSOR NODE")
    print(f"{'='*60}")
    
    # Call MCP tools to get backlog and risk summary
    backlog = mcp_server.get_backlog()
    risk_summary = mcp_server.get_risk_summary()
    
    print(f"Analyzing backlog for risks...")
    
    # Use LLM to identify specific risks
    risk_prompt = f"""You are a sprint risk analyst. Analyze this sprint backlog and identify 2-3 specific risks.

{backlog}

{risk_summary}

For each risk, you MUST:
1. Name a specific task from the backlog
2. Explain why it is risky (dependencies, complexity, unclear requirements, no assignee, etc.)
3. Suggest mitigation

Example format:
- Task: "DB migration" (8 SP) — Risk: No assignee and depends on external vendor; high chance of blocking other tasks. Mitigation: Assign owner and confirm vendor availability.

Provide 2-3 specific, actionable risk assessments."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": risk_prompt}],
        temperature=0.7
    )
    
    risks = response.choices[0].message.content.strip()
    
    print(f"\nRisk Assessment:\n{risks}")
    
    # Update state
    state["worker_results"] = state.get("worker_results", []) + [risks]
    state["messages"] = state.get("messages", []) + [f"Risk Assessor: {risks}"]
    
    return state


def route_after_supervisor(state: SprintState) -> Literal["sprint_builder", "capacity_checker", "risk_assessor", "finish"]:
    """Routing function based on supervisor's decision."""
    next_action = state.get("next_action", "finish")
    
    if next_action == "sprint_builder":
        return "sprint_builder"
    elif next_action == "capacity_checker":
        return "capacity_checker"
    elif next_action == "risk_assessor":
        return "risk_assessor"
    else:
        return "finish"


def build_graph() -> StateGraph:
    """Build the supervisor-worker graph."""
    graph = StateGraph(SprintState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sprint_builder", sprint_builder_node)
    graph.add_node("capacity_checker", capacity_checker_node)
    graph.add_node("risk_assessor", risk_assessor_node)
    
    # Set entry point
    graph.set_entry_point("supervisor")
    
    # Add conditional routing from supervisor
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "sprint_builder": "sprint_builder",
            "capacity_checker": "capacity_checker",
            "risk_assessor": "risk_assessor",
            "finish": END
        }
    )
    
    # All workers go directly to END after execution
    # The loop happens at the application level, not graph level
    graph.add_edge("sprint_builder", END)
    graph.add_edge("capacity_checker", END)
    graph.add_edge("risk_assessor", END)
    
    return graph.compile()


async def main():
    """Main entry point for the Sprint Planning Assistant."""
    print("="*60)
    print("Sprint Planning Assistant")
    print("Pattern: Supervisor + FastMCP")
    print("="*60)
    print("\nMCP Tools Available:")
    print("  - get_backlog()")
    print("  - add_task(title, assignee, story_points)")
    print("  - check_capacity(velocity)")
    print("  - get_risk_summary()")
    print("\nAvailable commands:")
    print("  - 'Plan [feature]' - Break down a feature into tasks")
    print("  - 'Check capacity' - Analyze sprint capacity")
    print("  - 'Any risks?' - Identify blockers and concerns")
    print("  - 'Done' - Exit")
    print("="*60)
    
    # Build graph
    app = build_graph()
    
    # Interactive loop
    while True:
        user_input = input("\nYour request: ").strip()
        
        if not user_input:
            continue
        
        # Check if user wants to exit
        if user_input.lower() in ['done', 'quit', 'exit', 'finish', "that's all"]:
            print("\nThank you for using Sprint Planning Assistant!")
            break
        
        # Initialize state for this request
        initial_state: SprintState = {
            "user_request": user_input,
            "messages": [],
            "worker_results": [],
            "next_action": None,
            "should_continue": True
        }
        
        # Run graph (executes: Supervisor → Worker → END)
        final_state = await app.ainvoke(initial_state)
        
        # Display results
        if final_state["worker_results"]:
            print(f"\n{'='*60}")
            print("✅ COMPLETED")
            print(f"{'='*60}")
            for result in final_state["worker_results"]:
                print(f"{result}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
