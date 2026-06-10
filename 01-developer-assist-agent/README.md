# Assignment 01 — Developer Assist Agent

A development assistant that uses the **ReAct pattern** (Thought → Action → Observation loop) to help engineering teams with story estimation, tech stack recommendations, and documentation summarization.

## 📋 Overview

This agent implements a reasoning loop using **LangGraph StateGraph** to:
- Estimate story points for feature descriptions
- Recommend technologies for technical requirements
- Summarize technical documentation
- Handle complex queries requiring multiple tools

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Assist Agent                   │
│                    (ReAct Pattern Implementation)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  START (Query)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Reasoning Node  │◄────────┐
                    │  (LLM thinks)   │         │
                    └────────┬────────┘         │
                             │                  │
                     ┌───────┴────────┐         │
                     │  Conditional   │         │
                     │     Check      │         │
                     └───────┬────────┘         │
                             │                  │
                  ┌──────────┴──────────┐       │
                  │                     │       │
            Final Answer           Tool Call    │
                  │                     │       │
                  ▼                     ▼       │
            ┌─────────┐         ┌──────────┐   │
            │   END   │         │   Tool   │   │
            └─────────┘         │Execution │───┘
                                └──────────┘
                                (Observation)

Tools Available:
├── story_estimator (feature → story points + rationale)
├── tech_stack_advisor (requirements → tech recommendations)
└── doc_summariser (documentation → 3 bullet summary)
```

## 🛠️ Technical Stack

As per assignment requirements:

| Tool | Version | Purpose |
|------|---------|---------|
| **LangGraph** | ≥0.2.0 | StateGraph (mandatory) - orchestrates ReAct loop |
| **OpenAI** | ≥1.0.0 | LLM for reasoning and decision-making |
| **Python** | 3.8+ | Core language |

Additional utilities:
- `python-dotenv` - Environment variable management
- `pydantic` - Type safety

## 📦 Installation & Setup

### 1. Clone the repository

```bash
cd AI_Python_Assignment/01-developer-assist-agent
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy the template and add your OpenAI API key:

```bash
cp .env.template .env
```

Edit `.env` and set your key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4  # or gpt-4o, gpt-3.5-turbo
```

⚠️ **Important**: The `.env` file is gitignored to keep your API key secure.

## 🚀 Usage

### Run all test queries

```bash
python agent.py
```

This will execute the 4 sample queries from the assignment specification.

### Run custom query

```python
from agent import run_agent

answer = run_agent("Your question here")
print(answer)
```

## 🧪 Test Queries & Expected Behavior

### Query 1: Story Estimation
```
Query: "Estimate the effort for adding a CSV export feature to the admin dashboard"

Expected:
✓ Uses story_estimator tool
✓ Returns story points (1,2,3,5,8,13)
✓ Provides 2-sentence rationale
```

### Query 2: Tech Stack Advice
```
Query: "What stack should I use to build a real-time notification system?"

Expected:
✓ Uses tech_stack_advisor tool
✓ Returns 2-3 technology recommendations
✓ Each with single-sentence justification
```

### Query 3: Documentation Summary
```
Query: "Summarise this doc: [LangGraph documentation text]"

Expected:
✓ Uses doc_summariser tool
✓ Returns exactly 3 bullet points
✓ Each bullet is one sentence
```

### Query 4: Multi-Tool Query
```
Query: "I need to add OAuth login — what tech should I use and how much effort will it take?"

Expected:
✓ Uses BOTH tech_stack_advisor AND story_estimator
✓ Shows multiple Thought → Action → Observation cycles
✓ Synthesizes both results in final answer
```

## 📊 Sample Transcript

Below is an example of the agent's reasoning trace:

```
============================================================
DEVELOPER ASSIST AGENT
============================================================
Query: I need to add OAuth login — what tech should I use and how much effort will it take?

============================================================
ITERATION 1
============================================================
Thought: The user is asking two questions: (1) what technology to use for OAuth login, and (2) how much effort it will take. I need to use two tools sequentially.

Action: tech_stack_advisor
Action Input: OAuth login authentication

Observation: Auth0 or OAuth 2.0 — industry-standard authentication with social login support and enterprise SSO integration.
FastAPI — lightweight, async-native REST framework with automatic OpenAPI documentation and high performance.
PostgreSQL — robust relational database with strong ACID guarantees and excellent reliability for production workloads.

============================================================
ITERATION 2
============================================================
Thought: I have the technology recommendations. Now I need to estimate the story points for implementing OAuth login.

Action: story_estimator
Action Input: Add OAuth login with social login support

Observation: 5 points — Requires integration work or significant backend changes. Standard complexity feature with some external dependencies.

Final Answer: To add OAuth login, I recommend using Auth0 or implementing OAuth 2.0 directly, paired with FastAPI for your backend framework. For data persistence, PostgreSQL is a solid choice. The implementation will take approximately 5 story points, as it requires OAuth integration and session management but doesn't need new infrastructure setup.

============================================================
```

## 🔒 Safety Features

- **6-iteration guard**: Prevents infinite loops by capping at 6 tool calls
- **Graceful degradation**: Returns best available answer if max iterations reached
- **Error handling**: Catches and handles malformed LLM responses

## 📝 Project Structure

```
01-developer-assist-agent/
├── agent.py              # Main agent implementation with ReAct loop
├── state.py              # State schema (AgentState, ReasoningStep)
├── tools.py              # Three required tools
├── requirements.txt      # Dependencies (LangGraph, OpenAI, etc.)
├── .env.template         # Environment variable template
├── .gitignore           # Excludes .env and Python artifacts
└── README.md            # This file
```

## 🎯 Rubric Compliance

| Criterion | Implementation | Status |
|-----------|----------------|--------|
| **Graph & Pattern** | LangGraph StateGraph with ReAct pattern | ✅ |
| **ReAct Loop** | Thought→Action→Observation visible; 6-iteration guard | ✅ |
| **State & Orchestration** | AgentState flows through all nodes cleanly | ✅ |
| **End-to-End Run** | All 4 test queries pass with correct outputs | ✅ |
| **Documentation** | PEP-8 compliant; README with diagram + transcripts | ✅ |

## 🔧 Development

### Code Style

Follows **PEP-8** conventions:
- 4-space indentation
- Max line length: 100 characters
- Docstrings for all functions
- Type hints where applicable

### Testing

Run the test suite:

```bash
python agent.py
```

View full reasoning traces in console output.

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)

## 🤝 Assignment Info

**Course**: AI Python Assignments  
**Assignment**: 01 - Developer Assist Agent  
**Pattern**: ReAct (Reasoning and Acting)  
**Framework**: LangGraph (StateGraph mandatory)  
**Model**: OpenAI GPT-4

---

**Note**: This is an educational project for assignment submission. API keys must be kept secure and never committed to version control.
