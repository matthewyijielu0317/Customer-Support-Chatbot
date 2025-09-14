from pathlib import Path
from typing import List, Union

from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFDirectoryLoader,
    TextLoader,
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


