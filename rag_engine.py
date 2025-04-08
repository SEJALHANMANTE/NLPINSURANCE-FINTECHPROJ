from langchain.llms import BaseLLM
import openrouter

# Custom LLM class to integrate with OpenRouter Llama 4 Maverick model
class OpenRouterLlama4MaverickLLM(BaseLLM):
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
    
    def _generate(self, prompt: str) -> str:
        # Make the API request to OpenRouter for the Llama 4 Maverick model
        response = openrouter.Completion.create(
            model=self.model_name,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=500  # Adjust max tokens as needed
        )
        return response['choices'][0]['text'].strip()

    @property
    def _llm_type(self):
        return "OpenRouter Llama 4 Maverick"

from langchain.chains import RetrievalQA

def get_rag_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    
    # Use Llama 4 Maverick model instead of OpenAI or previous Llama versions
    llm = OpenRouterLlama4MaverickLLM(
        model_name="meta-llama/llama-4-maverick:free",  
        temperature=0.3
    )
    
    # Create the RAG chain with the retriever and Llama 4 Maverick model
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)
    
    return qa_chain


