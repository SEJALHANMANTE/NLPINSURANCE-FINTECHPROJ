import os
import fitz  # PyMuPDF
import numpy as np
import faiss
import spacy
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm
import time
from openai import OpenAI  # OpenRouter Client

# ---------- Global Models & Setup ----------

# Load SpaCy model for sentence segmentation
spacy_model = spacy.load("en_core_web_sm")

# Load BERT model and tokenizer for insurance-specific embeddings
tokenizer = AutoTokenizer.from_pretrained("llmware/industry-bert-insurance-v0.1")
bert_model = AutoModel.from_pretrained("llmware/industry-bert-insurance-v0.1")

# Initialize FAISS index with the embedding dimension
embedding_dim = 768
faiss_index = faiss.IndexFlatIP(embedding_dim)  # Cosine similarity-based index
policy_chunk_map = []  # Holds chunks for the current policy

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  # Replace with your actual API key
)

# ---------- Utility Functions ----------







def extract_text(pdf_path):
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def chunk_policy_text(text, chunk_size=3):
    """Chunk the policy text into smaller segments."""
    doc = spacy_model(text)
    sentences = [
        sent.text.strip()
        for sent in doc.sents
        if len(sent.text.strip()) > 50 and not sent.text.lower().startswith(("sbi general", "registered office"))
    ]
    chunks = [" ".join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)]
    return chunks

def embed(text: str):
    """Generate BERT embeddings for a given text."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        output = bert_model(**inputs)
    return output.last_hidden_state.mean(dim=1).squeeze().numpy()

def normalize_vectors(vectors):
    """Normalize vectors for FAISS search."""
    vectors = np.array(vectors).astype(np.float32)
    faiss.normalize_L2(vectors)
    return vectors

# ---------- Processing & Indexing ----------

def process_current_policy(pdf_path):
    """Process and index the current policy PDF."""
    global faiss_index, policy_chunk_map

    print("📄 Extracting and chunking text...")
    text = extract_text(pdf_path)
    chunks = chunk_policy_text(text)

    print("📊 Embedding and indexing chunks...")
    chunk_vectors = [embed(chunk) for chunk in tqdm(chunks, desc="Embedding")]
    chunk_vectors = normalize_vectors(chunk_vectors)

    faiss_index.add(chunk_vectors)
    policy_chunk_map = chunks  # Store chunks for retrieval

    print(f"✅ Processed and indexed {len(chunks)} chunks.")

# ---------- Querying ----------

def search_policy(query, top_k=1):
    """Search the policy for the most relevant clause."""
    print("🤖 Thinking", end="")
    for _ in range(5): 
        time.sleep(0.2); print(".", end="", flush=True)
    print("\n🔍 Searching for relevant clauses...")

    query_vec = normalize_vectors([embed(query)])
    D, I = faiss_index.search(query_vec, top_k)

    # Check if the results are valid and not empty
    if I.shape[0] > 0 and I[0].size > 0:
        top_match = policy_chunk_map[I[0][0]]  # Access top match
        score = D[0][0]  # The similarity score
        print(f"\nResult (Cosine Similarity: {score:.4f}):\n{top_match}")
    else:
        print("❌ No relevant results found.")
        return None

    summary = summarize_with_openrouter(top_match)
    return summary

def summarize_with_openrouter(text):
    """Summarize the top result using OpenRouter's LLM."""
    print("\n📝 Summarizing result with OpenRouter...")
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout:free",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Summarize the following insurance policy clause: and also next explain it in easy to understand words"},
                    {"type": "text", "text": text}
                ]
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

# ---------- Execution ----------

if __name__ == "__main__":
    # Prompt user for the PDF file path
    pdf_path = input("Please enter the path to the policy PDF file: ")

    # Process the policy PDF
    process_current_policy(pdf_path)

    # Prompt user for the query
    user_query = input("Please enter your query about the insurance policy: ")

    # Ask the query
    result_summary = search_policy(user_query)
    if result_summary:
        print("\n🔑 Summary of the top result:\n", result_summary)

    # Clean-up (optional, but FAISS index will be destroyed after script ends)
    # del faiss_index

