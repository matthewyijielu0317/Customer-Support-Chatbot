"""Document ingestion utilities: loaders, preprocessing, pipelines."""

from .loaders import load_from_url, load_from_pdf_dir, load_from_pdf_file, load_from_txt, load_from_docx
from .preprocess import preprocess_documents
from .pipeline import (
    infer_source_type,
    load_documents,
    split_documents,
    ingest_sources,
    ingest_files_with_preprocessing,
)

__all__ = [
    "load_from_url",
    "load_from_pdf_dir",
    "load_from_pdf_file",
    "load_from_txt",
    "load_from_docx",
    "preprocess_documents",
    "infer_source_type",
    "load_documents",
    "split_documents",
    "ingest_sources",
    "ingest_files_with_preprocessing",
]
