import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("Please install pypdf or PyPDF2: pip install pypdf")


class PDFProcessor:
    """A class for processing PDF files: extracting text and chunking."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the PDFProcessor.

        Args:
            chunk_size: The size of each text chunk in characters (default: 1000).
            chunk_overlap: The number of characters to overlap between chunks (default: 200).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            A string containing all extracted text from the PDF.
        """
        try:
            reader = PdfReader(pdf_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            full_text = "\n".join(text_parts)
            logging.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except Exception as e:
            logging.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: The text to chunk.

        Returns:
            A list of text chunks.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap

        logging.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def extract_book_title(self, pdf_path: str) -> str:
        """
        Extract book title from PDF filename or metadata.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            The book title (filename without extension if metadata not available).
        """
        try:
            reader = PdfReader(pdf_path)
            metadata = reader.metadata
            if metadata and metadata.title:
                title = metadata.title.strip()
                if title:
                    return title
        except Exception as e:
            logging.warning(f"Could not extract metadata from PDF: {str(e)}")

        # Fallback to filename without extension
        filename = Path(pdf_path).stem
        return filename

    def process_pdf(
        self, pdf_path: str, book_title: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Process a PDF file: extract text, chunk it, and return structured data.

        Args:
            pdf_path: Path to the PDF file.
            book_title: Optional book title. If not provided, will be extracted from PDF.

        Returns:
            A list of dictionaries, each containing:
            - content: The chunk text
            - book_title: The book title
            - chunk_index: The index of the chunk (0-based)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if book_title is None:
            book_title = self.extract_book_title(pdf_path)

        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)

        processed_chunks = []
        for idx, chunk in enumerate(chunks):
            processed_chunks.append(
                {
                    "content": chunk,
                    "book_title": book_title,
                    "chunk_index": idx,
                }
            )

        logging.info(
            f"Processed PDF {pdf_path}: {len(processed_chunks)} chunks for book '{book_title}'"
        )
        return processed_chunks

