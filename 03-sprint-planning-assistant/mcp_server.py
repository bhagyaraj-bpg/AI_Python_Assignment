"""
FastMCP Server for Sprint Planning

This server maintains a sprint backlog in memory and provides tools
for adding tasks, checking capacity, and analyzing risks.

Start this server BEFORE running the agent graph.
"""

from fastmcp import FastMCP
from typing import Dict, List

# Initialize FastMCP server
mcp = FastMCP("Sprint Planning Server")

# In-memory sprint backlog
sprint_backlog: List[Dict] = []


@mcp.tool()
def get_backlog() -> str:
    """
    Returns all tasks formatted as a readable list.
    Includes title, assignee, story_points, status, and risk_level for each task.
    
    Returns:
        Formatted string listing all backlog tasks
    """
    if not sprint_backlog:
        return "Sprint backlog is empty. No tasks have been added yet."
    
    result = "Sprint Backlog:\n" + "=" * 60 + "\n"
    for i, task in enumerate(sprint_backlog, 1):
        result += (
            f"{i}. {task['title']}\n"
            f"   Assignee: {task['assignee']}\n"
            f"   Story Points: {task['story_points']} SP\n"
            f"   Status: {task['status']}\n"
            f"   Risk Level: {task['risk_level']}\n"
            f"{'-' * 60}\n"
        )
    return result


@mcp.tool()
def add_task(title: str, assignee: str, story_points: int) -> str:
    """
    Creates a new task with status='todo' and risk_level='low'.
    
    Args:
        title: Task title/description
        assignee: Person assigned to the task
        story_points: Effort estimate in story points
    
    Returns:
        Confirmation message with task details
    """
    task = {
        "title": title,
        "assignee": assignee,
        "story_points": story_points,
        "status": "todo",
        "risk_level": "low"
    }
    sprint_backlog.append(task)
    return f"Task added: {title} ({story_points} SP, assigned to {assignee})"


@mcp.tool()
def check_capacity(velocity: int = 40) -> str:
    """
    Sums story_points of all non-done tasks and compares to velocity.
    
    Args:
        velocity: Sprint velocity in story points (default: 40)
    
    Returns:
        Capacity analysis with over/under calculation
    """
    total_sp = sum(
        task["story_points"] 
        for task in sprint_backlog 
        if task["status"] != "done"
    )
    
    difference = total_sp - velocity
    
    if difference > 0:
        status = f"Over capacity by {difference} SP"
    elif difference < 0:
        status = f"Under capacity by {abs(difference)} SP"
    else:
        status = "Exactly at capacity"
    
    return f"Sprint is at {total_sp}/{velocity} SP. {status}."


@mcp.tool()
def get_risk_summary() -> str:
    """
    Returns tasks with risk_level 'high' or 'medium'.
    
    Returns:
        Formatted numbered list of risky tasks
    """
    risky_tasks = [
        task for task in sprint_backlog 
        if task["risk_level"] in ["high", "medium"]
    ]
    
    if not risky_tasks:
        return "No high or medium risk tasks identified in the backlog."
    
    result = "Risk Summary:\n" + "=" * 60 + "\n"
    for i, task in enumerate(risky_tasks, 1):
        result += (
            f"{i}. {task['title']} - Risk: {task['risk_level'].upper()}\n"
            f"   Assignee: {task['assignee']}, Story Points: {task['story_points']} SP\n"
            f"   Status: {task['status']}\n"
        )
    return result


if __name__ == "__main__":
    # Run the MCP server
    print("Starting Sprint Planning MCP Server...")
    print("Server will expose 4 tools:")
    print("  - get_backlog()")
    print("  - add_task(title, assignee, story_points)")
    print("  - check_capacity(velocity)")
    print("  - get_risk_summary()")
    print("\nPress Ctrl+C to stop the server.")
    
    # Start server using FastMCP's built-in run method
    mcp.run()
