from typing import List

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document


class FAISSStore:
    def __init__(self):
        self.embedding = OpenAIEmbeddings()
        self.vectorstore: FAISS | None = None

    def index(self, documents: List[Document]) -> None:
        self.vectorstore = FAISS.from_documents(documents, self.embedding)

    def retriever(self):
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized")
        return self.vectorstore.as_retriever()


