from langchain.vectorstores import FAISS, Chroma, Qdrant
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from typing import List, Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class VectorDBManager:
    """Manager for different vector database implementations"""
    
    def __init__(self, db_type: str = "faiss", **kwargs):
        """
        Initialize vector database manager
        
        Args:
            db_type: Type of vector database ('faiss', 'chroma', 'qdrant')
            **kwargs: Additional arguments for database initialization
        """
        self.db_type = db_type
        self.vectorstore = None
        self.kwargs = kwargs
    
    def create_vectorstore(
        self, 
        documents: List[Document], 
        embeddings: Embeddings,
        persist_directory: Optional[str] = None
    ):
        """
        Create vector store from documents
        
        Args:
            documents: List of documents to index
            embeddings: Embeddings model
            persist_directory: Directory to persist the database
        """
        try:
            if self.db_type == "faiss":
                self.vectorstore = FAISS.from_documents(documents, embeddings)
                if persist_directory:
                    self.vectorstore.save_local(persist_directory)
                    
            elif self.db_type == "chroma":
                persist_directory = persist_directory or "./data/knowledge_base/chroma"
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=embeddings,
                    persist_directory=persist_directory
                )
                self.vectorstore.persist()
                
            elif self.db_type == "qdrant":
                # Qdrant requires a collection name
                collection_name = self.kwargs.get("collection_name", "documents")
                self.vectorstore = Qdrant.from_documents(
                    documents=documents,
                    embedding=embeddings,
                    collection_name=collection_name
                )
            else:
                raise ValueError(f"Unsupported vector database type: {self.db_type}")
                
            logger.info(f"Successfully created {self.db_type} vector store")
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise
    
    def load_vectorstore(
        self, 
        embeddings: Embeddings,
        persist_directory: Optional[str] = None
    ):
        """
        Load existing vector store
        
        Args:
            embeddings: Embeddings model
            persist_directory: Directory where the database is persisted
        """
        try:
            if self.db_type == "faiss":
                if not persist_directory:
                    raise ValueError("persist_directory is required for FAISS")
                self.vectorstore = FAISS.load_local(persist_directory, embeddings)
                
            elif self.db_type == "chroma":
                persist_directory = persist_directory or "./data/knowledge_base/chroma"
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embeddings
                )
                
            elif self.db_type == "qdrant":
                collection_name = self.kwargs.get("collection_name", "documents")
                self.vectorstore = Qdrant(
                    client=None,  # Will use default local client
                    collection_name=collection_name,
                    embeddings=embeddings
                )
            else:
                raise ValueError(f"Unsupported vector database type: {self.db_type}")
                
            logger.info(f"Successfully loaded {self.db_type} vector store")
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform similarity search
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional filter for search results
            
        Returns:
            List of similar documents
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        try:
            if filter:
                return self.vectorstore.similarity_search(query, k=k, filter=filter)
            else:
                return self.vectorstore.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        Perform similarity search with scores
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional filter for search results
            
        Returns:
            List of (document, score) tuples
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        try:
            if filter:
                return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter)
            else:
                return self.vectorstore.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            raise
    
    def add_documents(self, documents: List[Document]):
        """
        Add new documents to the vector store
        
        Args:
            documents: List of documents to add
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        try:
            self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def get_retriever(self, search_type: str = "similarity", **kwargs):
        """
        Get a retriever from the vector store
        
        Args:
            search_type: Type of search ('similarity', 'mmr', etc.)
            **kwargs: Additional arguments for retriever
            
        Returns:
            VectorStoreRetriever instance
        """
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        return self.vectorstore.as_retriever(search_type=search_type, **kwargs) 