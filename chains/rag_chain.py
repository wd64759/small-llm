from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain.schema.retriever import BaseRetriever
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RAGChain:
    """Retrieval-Augmented Generation Chain"""
    
    def __init__(self, retriever: BaseRetriever, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize RAG Chain
        
        Args:
            retriever: Vector store retriever
            model_name: OpenAI model name
        """
        self.retriever = retriever
        self.llm = OpenAI(model_name=model_name, temperature=0)
        self.chain = None
        self._setup_chain()
    
    def _setup_chain(self):
        """Setup the QA chain with custom prompt"""
        qa_template = """
        Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        qa_prompt = PromptTemplate(
            template=qa_template,
            input_variables=["context", "question"]
        )
        
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": qa_prompt}
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG chain
        
        Args:
            question: User question
            
        Returns:
            Dictionary containing answer and source documents
        """
        try:
            result = self.chain({"query": question})
            return {
                "answer": result["result"],
                "source_documents": result["source_documents"],
                "success": True
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "source_documents": [],
                "success": False
            }
    
    def get_relevant_documents(self, query: str, k: int = 4) -> List:
        """
        Get relevant documents for a query
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        return self.retriever.get_relevant_documents(query, k=k) 