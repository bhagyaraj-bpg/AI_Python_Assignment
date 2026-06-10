"""Build FAISS index from Wikipedia articles for Engineering Knowledge Base."""

import os
import time
from dotenv import load_dotenv
import wikipediaapi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

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
            time.sleep(5)  # 5 second delay between requests
        
        try:
            page = wiki.page(article_title)
            
            if page.exists():
                # Create a Document with the article text and metadata
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
    """Build and save FAISS index."""
    print("\n🔨 Building FAISS index...")
    
    try:
        # Initialize OpenAI embeddings with base URL configuration
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        print(f"  - Initializing OpenAI embeddings...")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=api_key,
            openai_api_base=os.getenv("OPENAI_API_BASE"),  # Allow custom base URL
            max_retries=3,
            timeout=60
        )
        
        # Create FAISS vector store in batches to handle errors better
        print(f"  - Embedding {len(chunked_docs)} document chunks...")
        print(f"    (This may take 2-3 minutes...)")
        
        vectorstore = FAISS.from_documents(chunked_docs, embeddings)
        
        # Save to disk
        index_path = "faiss_index"
        vectorstore.save_local(index_path)
        print(f"  ✓ FAISS index saved to '{index_path}'")
        
        return vectorstore
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error building FAISS index: {error_msg}")
        
        if "401" in error_msg or "geography" in error_msg.lower():
            print("\n💡 OpenAI API Authentication Error Detected!")
            print("   This error suggests your API key has geography restrictions.")
            print("\n   Solutions:")
            print("   1. Verify your API key is correct in .env file")
            print("   2. Check if your OpenAI project allows access from your region")
            print("   3. Try creating a new API key in a project without geography restrictions")
            print("   4. Visit: https://platform.openai.com/api-keys")
        
        raise


def main():
    """Main indexing pipeline."""
    print("=" * 60)
    print("Engineering Knowledge Base - FAISS Index Builder")
    print("=" * 60)
    
    # Step 1: Fetch articles
    documents = fetch_wikipedia_articles()
    print(f"\n✓ Fetched {len(documents)} articles")
    
    # Step 2: Chunk documents
    chunked_docs = chunk_documents(documents)
    
    # Step 3: Build and save FAISS index
    vectorstore = build_faiss_index(chunked_docs)
    
    print("\n" + "=" * 60)
    print("✅ Indexing complete! Run agent.py to query the knowledge base.")
    print("=" * 60)


if __name__ == "__main__":
    main()
