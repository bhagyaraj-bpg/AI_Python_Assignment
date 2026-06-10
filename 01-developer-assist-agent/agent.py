"""
Developer Assist Agent - Main Implementation

Pattern: ReAct (Reasoning and Acting)
Loop: Thought → Action → Observation → repeat until Final Answer

This agent uses LangGraph StateGraph to implement a reasoning loop
that helps developers with story estimation, tech stack advice, and
documentation summarization.
"""

import os
import json
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI

from langgraph.graph import StateGraph, END
from state import AgentState, ReasoningStep
from tools import story_estimator, tech_stack_advisor, doc_summariser


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Maximum iterations guard
MAX_ITERATIONS = 6


def reasoning_node(state: AgentState) -> AgentState:
    """
    LLM reasoning node that generates Thought, Action, and Action Input.
    
    This node prompts the LLM to think through the problem and decide
    whether to use a tool or provide a final answer.
    """
    query = state["query"]
    reasoning_steps = state["reasoning_steps"]
    iteration_count = state["iteration_count"]
    
    # Build context from previous steps
    context = f"User Query: {query}\n\n"
    
    if reasoning_steps:
        context += "Previous Reasoning Steps:\n"
        for i, step in enumerate(reasoning_steps, 1):
            context += f"\nStep {i}:\n"
            context += f"Thought: {step.thought}\n"
            if step.action:
                context += f"Action: {step.action}\n"
                context += f"Action Input: {step.action_input}\n"
            if step.observation:
                context += f"Observation: {step.observation}\n"
    
    # Create system prompt
    system_prompt = """You are a developer assist agent using the ReAct pattern.

Available Tools:
1. story_estimator - Estimates story points (1,2,3,5,8,13) for feature descriptions
2. tech_stack_advisor - Recommends 2-3 technologies for technical requirements  
3. doc_summariser - Summarizes documentation into 3 bullet points

Your response MUST be valid JSON with this exact structure:
{
  "thought": "your reasoning about what to do next",
  "action": "tool_name or null if ready for final answer",
  "action_input": "input for the tool or null",
  "final_answer": "your final answer or null if you need more tools"
}

Rules:
- First, state your Thought about the problem
- If you need a tool, set action and action_input
- If you have enough information, set final_answer and leave action as null
- Use tools sequentially - one per turn
- Synthesize multiple tool results in your final answer
- Be direct and concise"""

    user_prompt = f"""{context}

Based on the query and any previous observations, what should you do next?
Respond with JSON only."""

    # Call OpenAI
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
    )
    
    # Parse LLM response
    content = response.choices[0].message.content.strip()
    
    # Extract JSON from markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        result = {
            "thought": "Unable to parse response properly",
            "action": None,
            "action_input": None,
            "final_answer": "I encountered an error processing your request. Please try rephrasing your question."
        }
    
    # Create new reasoning step
    step = ReasoningStep(
        thought=result.get("thought", ""),
        action=result.get("action"),
        action_input=result.get("action_input")
    )
    
    # Print the reasoning trace to console
    print(f"\n{'='*60}")
    print(f"ITERATION {iteration_count + 1}")
    print(f"{'='*60}")
    print(f"Thought: {step.thought}")
    
    if step.action:
        print(f"Action: {step.action}")
        print(f"Action Input: {step.action_input}")
    
    # Update state
    new_steps = reasoning_steps + [step]
    
    # Check if we have a final answer
    final_answer = result.get("final_answer")
    should_continue = final_answer is None and iteration_count < MAX_ITERATIONS
    
    if final_answer:
        print(f"\nFinal Answer: {final_answer}")
    
    return {
        **state,
        "reasoning_steps": new_steps,
        "final_answer": final_answer,
        "should_continue": should_continue,
        "iteration_count": iteration_count + 1
    }


def tool_execution_node(state: AgentState) -> AgentState:
    """
    Tool dispatcher that routes to the appropriate tool based on the action.
    
    Executes the tool and stores the observation in the state.
    """
    reasoning_steps = state["reasoning_steps"]
    current_step = reasoning_steps[-1]
    
    action = current_step.action
    action_input = current_step.action_input
    
    # Dispatch to the correct tool
    observation = ""
    
    if action == "story_estimator":
        observation = story_estimator(action_input)
    elif action == "tech_stack_advisor":
        observation = tech_stack_advisor(action_input)
    elif action == "doc_summariser":
        observation = doc_summariser(action_input)
    else:
        observation = f"Error: Unknown tool '{action}'"
    
    # Update the current step with the observation
    current_step.observation = observation
    
    # Print observation
    print(f"Observation: {observation}")
    
    return state


def should_continue_loop(state: AgentState) -> Literal["continue", "end"]:
    """
    Conditional edge function that determines whether to continue the loop
    or end with a final answer.
    
    Returns:
        "continue" if we should call another tool
        "end" if we have a final answer or hit max iterations
    """
    # Check if we've hit the iteration limit
    if state["iteration_count"] >= MAX_ITERATIONS:
        print(f"\n⚠️  Maximum iterations ({MAX_ITERATIONS}) reached. Stopping.")
        return "end"
    
    # Check if we have a final answer
    if state["final_answer"] is not None:
        return "end"
    
    # Check if the last step had an action (tool call)
    if state["reasoning_steps"] and state["reasoning_steps"][-1].action:
        return "continue"
    
    return "end"


def build_agent_graph() -> StateGraph:
    """
    Builds the LangGraph StateGraph for the Developer Assist Agent.
    
    Graph structure:
    START → reasoning_node → [conditional] → tool_execution_node → reasoning_node
                                          → END (if final answer ready)
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tool_execution", tool_execution_node)
    
    # Add edges
    workflow.set_entry_point("reasoning")
    
    # Conditional edge from reasoning node
    workflow.add_conditional_edges(
        "reasoning",
        should_continue_loop,
        {
            "continue": "tool_execution",
            "end": END
        }
    )
    
    # Edge from tool execution back to reasoning
    workflow.add_edge("tool_execution", "reasoning")
    
    # Compile the graph
    return workflow.compile()


def run_agent(query: str) -> str:
    """
    Run the Developer Assist Agent on a query.
    
    Args:
        query: User's question or request
        
    Returns:
        Final answer from the agent
    """
    print(f"\n{'='*60}")
    print(f"DEVELOPER ASSIST AGENT")
    print(f"{'='*60}")
    print(f"Query: {query}\n")
    
    # Initialize state
    initial_state: AgentState = {
        "query": query,
        "reasoning_steps": [],
        "iteration_count": 0,
        "final_answer": None,
        "should_continue": True
    }
    
    # Build and run the graph
    graph = build_agent_graph()
    final_state = graph.invoke(initial_state)
    
    # Handle case where we hit max iterations without final answer
    if final_state["final_answer"] is None:
        # Generate a best-effort answer from observations
        observations = [
            step.observation 
            for step in final_state["reasoning_steps"] 
            if step.observation
        ]
        
        if observations:
            final_answer = f"Based on the analysis:\n\n" + "\n\n".join(observations)
        else:
            final_answer = "I was unable to complete the analysis within the iteration limit."
        
        final_state["final_answer"] = final_answer
        print(f"\nFinal Answer (generated after max iterations): {final_answer}")
    
    print(f"\n{'='*60}\n")
    
    return final_state["final_answer"]


def main():
    """
    Main entry point with sample test queries.
    """
    query = input("\nEnter the Query...")
    answer = run_agent(query)
    print(f"\nAnswer: {answer}")


if __name__ == "__main__":
    main()
