"""Vector store module for document embedding and retrieval"""

from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

class VectorStore:
    """Manages vector store operations"""
    
    def __init__(self):
        """Initialize vector store with OpenAI embeddings"""
        self.embedding = OpenAIEmbeddings()
        self.vectorstore = None
        self.retriever = None
    
    def create_vectorstore(self, documents: List[Document]):
        """
        Create vector store from documents
        
        Args:
            documents: List of documents to embed
        """
        self.vectorstore = FAISS.from_documents(documents, self.embedding)
        self.retriever = self.vectorstore.as_retriever()
    
    def get_retriever(self):
        """
        Get the retriever instance
        
        Returns:
            Retriever instance
        """
        if self.retriever is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        return self.retriever
    
    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if self.retriever is None:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        return self.retriever.invoke(query)