"""Fallback FAISS index builder using HuggingFace embeddings (no OpenAI API required)."""

import os
from dotenv import load_dotenv
import wikipediaapi
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Wikipedia articles to index
ARTICLES = [
    "Software engineering",
    "Agile software development",
    "Continuous integration",
    "DevOps",
    "Technical debt",
    "Microservices",
    "Test-driven development"
]


def fetch_wikipedia_articles():
    """Fetch all 7 Wikipedia articles."""
    print("📥 Fetching Wikipedia articles...")
    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='MAS-Training/1.0'
    )
    
    documents = []
    for i, article_title in enumerate(ARTICLES, 1):
        print(f"  - Fetching: {article_title}")
        
        # Add delay to avoid rate limiting (except for first article)
        if i > 1:
            print(f"    (Waiting 5 seconds to avoid rate limiting...)")
            time.sleep(5)
        
        try:
            page = wiki.page(article_title)
            
            if page.exists():
                doc = Document(
                    page_content=page.text,
                    metadata={"doc_title": article_title}
                )
                documents.append(doc)
                print(f"    ✓ Retrieved {len(page.text)} characters")
            else:
                print(f"    ✗ Article not found: {article_title}")
        except Exception as e:
            print(f"    ✗ Error fetching article: {str(e)}")
            print(f"    Waiting 10 seconds before continuing...")
            time.sleep(10)
    
    return documents


def chunk_documents(documents):
    """Chunk documents into ~500-character segments with 50-character overlap."""
    print("\n📄 Chunking documents...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunked_docs = []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        doc_title = doc.metadata["doc_title"]
        
        for idx, chunk_text in enumerate(chunks):
            chunked_doc = Document(
                page_content=chunk_text,
                metadata={
                    "doc_title": doc_title,
                    "chunk_index": idx
                }
            )
            chunked_docs.append(chunked_doc)
        
        print(f"  - {doc_title}: {len(chunks)} chunks")
    
    print(f"\n  Total chunks created: {len(chunked_docs)}")
    return chunked_docs


def build_faiss_index(chunked_docs):
    """Build and save FAISS index using HuggingFace embeddings."""
    print("\n🔨 Building FAISS index...")
    print("  ℹ Using HuggingFace embeddings (no OpenAI API required)")
    
    try:
        # Initialize HuggingFace embeddings (runs locally, no API needed)
        print(f"  - Initializing HuggingFace embeddings (this may download a small model)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print(f"  - Embedding {len(chunked_docs)} document chunks...")
        print(f"    (This may take 3-5 minutes for first run...)")
        
        # Create FAISS vector store
        vectorstore = FAISS.from_documents(chunked_docs, embeddings)
        
        # Save to disk
        index_path = "faiss_index"
        vectorstore.save_local(index_path)
        print(f"  ✓ FAISS index saved to '{index_path}'")
        
        return vectorstore
        
    except Exception as e:
        print(f"\n❌ Error building FAISS index: {str(e)}")
        raise


def main():
    """Main indexing pipeline."""
    print("=" * 60)
    print("Engineering Knowledge Base - FAISS Index Builder")
    print("(Using HuggingFace Embeddings - No OpenAI API Required)")
    print("=" * 60)
    
    # Step 1: Fetch articles
    documents = fetch_wikipedia_articles()
    print(f"\n✓ Fetched {len(documents)} articles")
    
    # Step 2: Chunk documents
    chunked_docs = chunk_documents(documents)
    
    # Step 3: Build and save FAISS index
    vectorstore = build_faiss_index(chunked_docs)
    
    print("\n" + "=" * 60)
    print("✅ Indexing complete!")
    print("=" * 60)
    print("\nℹ NOTE: This index uses HuggingFace embeddings instead of OpenAI.")
    print("   You'll need to update agent.py to use the same embeddings.")
    print("   Run: python agent_fallback.py (instead of agent.py)")


if __name__ == "__main__":
    main()
