from langchain.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    MarkdownLoader,
    CSVLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.schema import Document
from typing import List, Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Document loader for various file types"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document loader
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Load PDF document
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of documents
        """
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return self._split_documents(documents)
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise
    
    def load_text(self, file_path: str) -> List[Document]:
        """
        Load text document
        
        Args:
            file_path: Path to text file
            
        Returns:
            List of documents
        """
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return self._split_documents(documents)
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            raise
    
    def load_markdown(self, file_path: str) -> List[Document]:
        """
        Load Markdown document
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            List of documents
        """
        try:
            loader = MarkdownLoader(file_path)
            documents = loader.load()
            return self._split_documents(documents)
        except Exception as e:
            logger.error(f"Error loading Markdown file {file_path}: {e}")
            raise
    
    def load_csv(self, file_path: str, csv_args: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Load CSV document
        
        Args:
            file_path: Path to CSV file
            csv_args: Additional arguments for CSV loader
            
        Returns:
            List of documents
        """
        try:
            csv_args = csv_args or {}
            loader = CSVLoader(file_path, **csv_args)
            documents = loader.load()
            return self._split_documents(documents)
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            raise
    
    def load_unstructured(self, file_path: str) -> List[Document]:
        """
        Load unstructured document (auto-detect format)
        
        Args:
            file_path: Path to file
            
        Returns:
            List of documents
        """
        try:
            loader = UnstructuredFileLoader(file_path)
            documents = loader.load()
            return self._split_documents(documents)
        except Exception as e:
            logger.error(f"Error loading unstructured file {file_path}: {e}")
            raise
    
    def load_file(self, file_path: str) -> List[Document]:
        """
        Load file based on extension
        
        Args:
            file_path: Path to file
            
        Returns:
            List of documents
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.load_pdf(file_path)
        elif file_extension == '.txt':
            return self.load_text(file_path)
        elif file_extension == '.md':
            return self.load_markdown(file_path)
        elif file_extension == '.csv':
            return self.load_csv(file_path)
        else:
            # Try unstructured loader for other formats
            return self.load_unstructured(file_path)
    
    def load_directory(self, directory_path: str, file_extensions: Optional[List[str]] = None) -> List[Document]:
        """
        Load all files in a directory
        
        Args:
            directory_path: Path to directory
            file_extensions: List of file extensions to include (e.g., ['.pdf', '.txt'])
            
        Returns:
            List of documents from all files
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        documents = []
        file_extensions = file_extensions or ['.pdf', '.txt', '.md', '.csv']
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()
                
                if file_extension in file_extensions:
                    try:
                        file_docs = self.load_file(file_path)
                        documents.extend(file_docs)
                        logger.info(f"Loaded {len(file_docs)} documents from {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {e}")
                        continue
        
        return documents
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of split documents
        """
        try:
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Error splitting documents: {e}")
            raise
    
    def create_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Create a document from text
        
        Args:
            text: Document text
            metadata: Document metadata
            
        Returns:
            Document object
        """
        metadata = metadata or {}
        return Document(page_content=text, metadata=metadata)
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error splitting text: {e}")
            raise 