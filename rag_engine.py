from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import openai

# Set OpenRouter endpoint and API key
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = "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"  # Replace with your OpenRouter key

def get_rag_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    llm = OpenAI(
        temperature=0.3,
        model_name="meta-llama/llama-3-70b-instruct",  
    )
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain

