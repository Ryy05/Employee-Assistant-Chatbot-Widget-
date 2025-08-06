# test_retrieval.py
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# --- Configuration ---
FAISS_INDEX_PATH = "data/mpc_faiss_index"
QUERIES = ["dress code", "leave without pay"]

def test_retrieval():
    """
    This script directly tests what information your FAISS vector store
    is retrieving for specific queries, bypassing the AI model.
    """
    print("--- Loading FAISS Index and Embedding Model ---")
    
    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"❌ ERROR: The index path '{FAISS_INDEX_PATH}' does not exist.")
        print("Please make sure your FAISS index is in the correct location.")
        return

    try:
        embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
        print("✅ Index loaded successfully.")
    except Exception as e:
        print(f"❌ An error occurred while loading the index: {e}")
        return

    print("\n" + "="*50 + "\n")

    for query in QUERIES:
        print(f"--- TESTING RETRIEVAL FOR QUERY: '{query}' ---")
        
        # Perform the similarity search to find the most relevant document chunks
        docs = db.similarity_search(query, k=3) # Let's look at the top 3 results

        if not docs:
            print("‼️ No documents found for this query.")
        else:
            print(f"✅ Found {len(docs)} relevant chunks. Here is their content:\n")
            for i, doc in enumerate(docs):
                print(f"--- Retrieved Chunk {i+1} ---\n{doc.page_content}\n" + "-"*20)
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    test_retrieval()