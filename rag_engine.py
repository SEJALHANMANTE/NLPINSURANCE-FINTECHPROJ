# rag_engine.py

from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

def get_rag_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    llm = OpenAI(temperature=0.3)  # or use GPT-4 if available
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    return qa_chain
