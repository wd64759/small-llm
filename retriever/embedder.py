from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.embeddings.base import Embeddings
from typing import List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class EmbedderFactory:
    """Factory for creating different types of embedders"""
    
    @staticmethod
    def create_openai_embedder(model: str = "text-embedding-ada-002") -> OpenAIEmbeddings:
        """
        Create OpenAI embedder
        
        Args:
            model: OpenAI embedding model name
            
        Returns:
            OpenAIEmbeddings instance
        """
        return OpenAIEmbeddings(model=model)
    
    @staticmethod
    def create_huggingface_embedder(
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ) -> HuggingFaceEmbeddings:
        """
        Create HuggingFace embedder
        
        Args:
            model_name: HuggingFace model name
            device: Device to run on ('cpu' or 'cuda')
            
        Returns:
            HuggingFaceEmbeddings instance
        """
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device}
        )

class EmbedderManager:
    """Manager for handling different embedding models"""
    
    def __init__(self, embedder_type: str = "openai", **kwargs):
        """
        Initialize embedder manager
        
        Args:
            embedder_type: Type of embedder ('openai' or 'huggingface')
            **kwargs: Additional arguments for embedder initialization
        """
        self.embedder_type = embedder_type
        self.embedder = self._create_embedder(**kwargs)
    
    def _create_embedder(self, **kwargs) -> Embeddings:
        """Create embedder based on type"""
        if self.embedder_type == "openai":
            model = kwargs.get("model", "text-embedding-ada-002")
            return EmbedderFactory.create_openai_embedder(model)
        elif self.embedder_type == "huggingface":
            model_name = kwargs.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
            device = kwargs.get("device", "cpu")
            return EmbedderFactory.create_huggingface_embedder(model_name, device)
        else:
            raise ValueError(f"Unsupported embedder type: {self.embedder_type}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents
        
        Args:
            texts: List of text documents
            
        Returns:
            List of embeddings
        """
        try:
            return self.embedder.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text
        
        Args:
            text: Query text
            
        Returns:
            Query embedding
        """
        try:
            return self.embedder.embed_query(text)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        # This is a placeholder - you would need to implement based on your embedder
        if self.embedder_type == "openai":
            return 1536  # OpenAI ada-002 dimension
        elif self.embedder_type == "huggingface":
            return 384   # Common dimension for many sentence transformers
        else:
            return 768   # Default fallback 