from pathlib import Path
from typing import List, Union

from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFDirectoryLoader,
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain.schema import Document


def load_from_url(url: str) -> List[Document]:
    loader = WebBaseLoader(url)
    return loader.load()


def load_from_pdf_dir(directory: Union[str, Path]) -> List[Document]:
    loader = PyPDFDirectoryLoader(str(directory))
    return loader.load()


def load_from_txt(file_path: Union[str, Path]) -> List[Document]:
    loader = TextLoader(str(file_path), encoding="utf-8")
    return loader.load()


def load_from_pdf_file(file_path: Union[str, Path]) -> List[Document]:
    """Load a single PDF file."""
    loader = PyPDFLoader(str(file_path))
    return loader.load()


def load_from_docx(file_path: Union[str, Path]) -> List[Document]:
    """Load a Word document (.docx)."""
    loader = Docx2txtLoader(str(file_path))
    return loader.load()


