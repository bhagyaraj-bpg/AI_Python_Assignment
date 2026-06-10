"""Engineering Knowledge Base Q&A Agent with Corrective RAG (HuggingFace Embeddings)."""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from state import KnowledgeBaseState

# Load environment variables
load_dotenv()

# Initialize OpenAI client for chat (this works with your API key)
llm = ChatOpenAI(
    model="gpt-4o",  # Using gpt-4o instead of gpt-4
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Load FAISS index with HuggingFace embeddings (no OpenAI API needed)
print("Loading FAISS index with HuggingFace embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
print("✓ FAISS index loaded successfully")


# ===== NODE 1: RETRIEVER =====
def retriever_node(state: KnowledgeBaseState) -> KnowledgeBaseState:
    """Retrieve top-4 documents from FAISS based on question."""
    question = state["question"]
    
    print(f"\n🔍 RETRIEVER NODE")
    print(f"Question: {question}")
    print(f"Retrieving top-4 documents from FAISS...")
    
    # Perform similarity search
    docs = vectorstore.similarity_search(question, k=4)
    
    # Convert to dict format with metadata
    retrieved_docs = []
    for doc in docs:
        retrieved_docs.append({
            "content": doc.page_content,
            "doc_title": doc.metadata.get("doc_title", "Unknown"),
            "chunk_index": doc.metadata.get("chunk_index", 0)
        })
    
    print(f"✓ Retrieved {len(retrieved_docs)} documents")
    for i, doc in enumerate(retrieved_docs, 1):
        print(f"  {i}. {doc['doc_title']} (chunk {doc['chunk_index']})")
    
    state["retrieved_docs"] = retrieved_docs
    state["grading_trace"] = []
    return state


# ===== NODE 2: GRADER =====
def grader_node(state: KnowledgeBaseState) -> KnowledgeBaseState:
    """Grade each retrieved document for relevance."""
    question = state["question"]
    retrieved_docs = state["retrieved_docs"]
    
    print(f"\n⚖️  GRADER NODE")
    print(f"Grading {len(retrieved_docs)} documents for relevance...")
    
    relevant_docs = []
    grading_trace = []
    
    for i, doc in enumerate(retrieved_docs, 1):
        # Create grading prompt
        grading_prompt = f"""Is the following text relevant to answering this question: {question}?

Text: {doc['content'][:300]}...

Reply with only: relevant or irrelevant."""
        
        # Call OpenAI for grading
        response = llm.invoke(grading_prompt)
        grade = response.content.strip().lower()
        
        # Log decision
        trace_entry = f"Doc {i} ({doc['doc_title']}): {grade}"
        grading_trace.append(trace_entry)
        print(f"  {trace_entry}")
        
        # Add to relevant docs if it passes
        if "relevant" in grade and "irrelevant" not in grade:
            relevant_docs.append(doc)
    
    print(f"\n✓ {len(relevant_docs)}/{len(retrieved_docs)} documents passed grading")
    
    state["relevant_docs"] = relevant_docs
    state["grading_trace"] = grading_trace
    return state


# ===== NODE 3: GENERATOR =====
def generator_node(state: KnowledgeBaseState) -> KnowledgeBaseState:
    """Generate answer based on relevant documents."""
    question = state["question"]
    relevant_docs = state["relevant_docs"]
    num_relevant = len(relevant_docs)
    
    print(f"\n📝 GENERATOR NODE")
    print(f"Generating answer with {num_relevant} relevant document(s)...")
    
    if num_relevant >= 2:
        # Case 1: ≥2 relevant docs → answer with citations
        context = "\n\n".join([
            f"[{doc['doc_title']}]\n{doc['content']}"
            for doc in relevant_docs
        ])
        
        prompt = f"""Answer the following question in 2-4 sentences based on the provided context.
Cite all source documents at the end in the format: 'Sources: [Title 1], [Title 2]'

Question: {question}

Context:
{context}

Answer:"""
        
        response = llm.invoke(prompt)
        answer = response.content.strip()
        
        # Ensure citation format is present
        if "Sources:" not in answer:
            source_titles = list(set([doc['doc_title'] for doc in relevant_docs]))
            answer += f"\n\nSources: {', '.join([f'[{title}]' for title in source_titles])}"
    
    elif num_relevant == 1:
        # Case 2: Exactly 1 relevant doc → answer with incompleteness note
        doc = relevant_docs[0]
        context = doc['content']
        
        prompt = f"""Answer the following question in 2-3 sentences based on the provided context.

Question: {question}

Context:
{context}

Answer:"""
        
        response = llm.invoke(prompt)
        answer = response.content.strip()
        answer += f"\n\nNote: only one source available — answer may be incomplete.\nSources: [{doc['doc_title']}]"
    
    else:
        # Case 3: 0 relevant docs → insufficient information
        answer = "Insufficient information in the knowledge base to answer this question."
    
    print(f"✓ Answer generated")
    
    state["answer"] = answer
    return state


# ===== BUILD GRAPH =====
def build_graph():
    """Build the LangGraph workflow."""
    workflow = StateGraph(KnowledgeBaseState)
    
    # Add nodes
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("generator", generator_node)
    
    # Define edges
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "grader")
    workflow.add_edge("grader", "generator")
    workflow.add_edge("generator", END)
    
    return workflow.compile()


# ===== MAIN FUNCTION =====
def main():
    """Run the knowledge base Q&A agent."""
    print("=" * 70)
    print("🧠 Engineering Knowledge Base Q&A Agent (Corrective RAG)")
    print("   (Using HuggingFace Embeddings)")
    print("=" * 70)
    
    # Build graph
    app = build_graph()
    
    # Test queries
    test_queries = [
        "What is trunk-based development and why do teams adopt it?",
        "How does technical debt accumulate and how should teams address it?",
        "What is the difference between microservices and a monolith?",
        "What are the current interest rates set by the Federal Reserve?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"TEST QUERY {i}/{len(test_queries)}")
        print(f"{'=' * 70}")
        
        # Initialize state
        initial_state = {
            "question": query,
            "retrieved_docs": [],
            "relevant_docs": [],
            "grading_trace": [],
            "answer": ""
        }
        
        # Run the graph
        final_state = app.invoke(initial_state)
        
        # Display results
        print(f"\n" + "=" * 70)
        print(f"📊 FINAL RESULTS")
        print(f"=" * 70)
        print(f"\nQuestion: {query}")
        print(f"\nGrading Trace:")
        for trace in final_state["grading_trace"]:
            print(f"  {trace}")
        print(f"\nAnswer:\n{final_state['answer']}")
        print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    # Check if FAISS index exists
    if not os.path.exists("faiss_index"):
        print("❌ FAISS index not found!")
        print("Please run 'python indexing_fallback.py' first to build the index.")
    else:
        main()
