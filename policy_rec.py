

# ✅ Imports
import json
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# ✅ Config
GROQ_API_KEY = "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"  # Your Groq API key
MODEL_NAME = "llama3-70b-8192"  # Groq model
K = 3  # Number of documents to retrieve

# ✅ Load FAISS index and metadata
with open("policy_metadata.json", "r", encoding="utf-8") as f:
    metadata_docs = json.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')  # Embedding model
index = faiss.read_index("faiss_policy.index")  # Your FAISS index file

# ✅ RAG-based policy recommendation function
def recommend_policy_rag(user_query, k=K):
    # 🔍 Step 1: Encode query and retrieve top-k documents
    query_vector = model.encode([user_query], convert_to_numpy=True)
    D, I = index.search(query_vector, k)
    top_docs = [metadata_docs[i] for i in I[0]]

    # 📚 Step 2: Prepare context for the LLM
    context = "\n".join([f"- {doc}" for doc in top_docs])

    prompt = f"""
## 🧾 User Query:
> **"{user_query}"**

## 📘 Top {k} Matching Policy Descriptions:
{context}

## 🎯 Task:
As an expert assistant, recommend **one** health insurance policy from the list above that best fits the user’s query. Explain your reasoning in 2–4 bullet points using simple language. Keep the response short, clear, and in **Markdown format**.
"""

    # 🛜 Step 3: Call Groq API
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant trained in Indian health insurance policy recommendations. Return all replies in clear Markdown with emojis."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 512
    }

    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return f"### ✅ Policy Recommendation\n\n{content}"
    except Exception as e:
        return f"❌ **Error:** {e}"
