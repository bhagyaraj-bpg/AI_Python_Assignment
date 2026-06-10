# AI Python Assignments

This repository contains multiple AI agent assignments, each demonstrating different architectural patterns and use cases.

## 📁 Repository Structure

```
AI_Python_Assignment/
├── .env                            # Environment variables (API keys)
├── 01-developer-assist-agent/      # ReAct pattern agent
├── 02-technical-brief-generator/   # Multi-stage pipeline with quality gate
├── 03-sprint-planning-assistant/   # Supervisor + FastMCP pattern
└── README.md                       # This file
```

## 🎯 Assignments

### Assignment 01 - Developer Assist Agent
**Pattern**: ReAct (Thought → Action → Observation)  
**Stack**: Python · LangGraph · OpenAI · 3 tools  
**Status**: ✅ Complete

A development assistant that helps engineering teams with:
- Story point estimation
- Tech stack recommendations  
- Documentation summarization

[View Assignment →](./01-developer-assist-agent/)

---

### Assignment 02 - Technical Brief Generator
**Pattern**: Multi-Stage Pipeline with Quality Gate  
**Stack**: Python · LangGraph · LangChain · OpenAI  
**Status**: ✅ Complete

A content pipeline that generates structured technical briefs:
- Researcher gathers facts about a topic
- Analyst evaluates quality and counts verifiable claims
- Quality gate routes back if claims are insufficient
- Writer produces final structured brief

[View Assignment →](./02-technical-brief-generator/)

---

### Assignment 03 - Sprint Planning Assistant
**Pattern**: Supervisor Agent + FastMCP  
**Stack**: Python · LangGraph · FastMCP · OpenAI  
**Status**: ✅ Complete

A sprint planning assistant with supervisor-worker architecture:
- Supervisor routes requests to specialist workers
- Sprint Builder decomposes features into tasks
- Capacity Checker analyzes sprint velocity
- Risk Assessor identifies blockers and concerns
- All data managed through FastMCP (no direct state sharing)

[View Assignment →](./03-sprint-planning-assistant/)

---

## 🚀 Quick Start

Each assignment has its own isolated environment and dependencies.

```bash
# Navigate to specific assignment
cd 01-developer-assist-agent

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API keys
cp .env.template .env
# Edit .env with your keys

# Run the agent
python agent.py
```

## 🔒 Security Notes

- All API keys and secrets are stored in `.env` files
- `.env` files are gitignored across all assignments
- Never commit credentials to version control
- Use `.env.template` files as reference

## 📚 Common Technical Stack

Most assignments use:
- **LangGraph**: StateGraph is mandatory for ALL assignments
- **OpenAI**: GPT-4 or compatible models
- **Python 3.8+**: Core language
- **python-dotenv**: Environment management

## 🎓 Assignment Guidelines

Each assignment follows these standards:
- ✅ PEP-8 compliant code
- ✅ Comprehensive README with setup instructions
- ✅ Architecture diagrams
- ✅ Sample test queries with transcripts
- ✅ Type hints and docstrings
- ✅ Proper error handling
- ✅ Secure credential management

## 📦 Repository Setup (Future)

When ready to push to GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all assignments
git add .

# Commit
git commit -m "Initial commit: AI Python Assignments"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/AI_Python_Assignment.git

# Push
git push -u origin main
```

## 🤝 Contributing

This is an educational repository for assignment submissions. Each assignment is self-contained and follows the course requirements.

---

**Last Updated**: June 2026  
**Course**: AI Python Development  
**Framework**: LangGraph (StateGraph)
