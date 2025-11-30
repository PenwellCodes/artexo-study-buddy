import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

# Try multiple PDF libraries for better compatibility
PDF_READER = None
PDF_LIBRARY = None

try:
    import fitz  # PyMuPDF - best for corrupted PDFs
    PDF_READER = fitz
    PDF_LIBRARY = "pymupdf"
except ImportError:
    try:
        from pypdf import PdfReader
        PDF_READER = PdfReader
        PDF_LIBRARY = "pypdf"
    except ImportError:
        try:
            from PyPDF2 import PdfReader
            PDF_READER = PdfReader
            PDF_LIBRARY = "pypdf2"
        except ImportError:
            raise ImportError(
                "Please install a PDF library: pip install pymupdf (recommended) or pip install pypdf"
            )


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
        Extract all text from a PDF file using the best available method.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            A string containing all extracted text from the PDF.
        """
        # Try PyMuPDF first (best for corrupted PDFs)
        if PDF_LIBRARY == "pymupdf":
            return self._extract_with_pymupdf(pdf_path)
        # Fall back to pypdf/PyPDF2
        else:
            return self._extract_with_pypdf(pdf_path)
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (fitz) - handles corrupted PDFs well."""
        try:
            import fitz
            # Try to repair/recover the PDF
            doc = fitz.open(pdf_path)
            text_parts = []
            num_pages = len(doc)
            
            if num_pages == 0:
                doc.close()
                # Try opening with repair mode
                try:
                    logging.info("PDF shows 0 pages, attempting repair mode...")
                    doc = fitz.open(pdf_path, filetype="pdf", stream=None)
                    num_pages = len(doc)
                    if num_pages == 0:
                        doc.close()
                        raise ValueError(
                            "PDF has 0 pages - file may be corrupted, empty, or password-protected. "
                            "Please try:\n"
                            "1. Open the PDF in a PDF viewer and re-save it\n"
                            "2. Check if the PDF is password-protected\n"
                            "3. Verify the file is not corrupted"
                        )
                except Exception as repair_error:
                    raise ValueError(
                        f"PDF appears corrupted (0 pages detected). "
                        f"Error: {str(repair_error)}\n"
                        "Please open the PDF in a PDF viewer (Chrome, Edge, Adobe Reader) "
                        "and re-save it as a new file."
                    )
            
            logging.info(f"Processing {num_pages} pages from {pdf_path} using PyMuPDF")
            
            for page_num in range(num_pages):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    if text and text.strip():
                        text_parts.append(text)
                    if (page_num + 1) % 100 == 0:
                        logging.info(f"Processed {page_num + 1}/{num_pages} pages...")
                except Exception as e:
                    logging.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()
            full_text = "\n".join(text_parts)
            
            if not full_text or len(full_text.strip()) == 0:
                raise ValueError(
                    "No text could be extracted from the PDF. "
                    "The PDF might be image-based (scanned) and require OCR, "
                    "or all pages may be empty."
                )
            
            logging.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except ValueError:
            # Re-raise ValueError as-is (these are our custom error messages)
            raise
        except Exception as e:
            logging.warning(f"PyMuPDF extraction failed: {str(e)}, trying fallback...")
            # Try pypdf as fallback only if pypdf is available
            if PDF_LIBRARY in ["pypdf", "pypdf2"]:
                return self._extract_with_pypdf(pdf_path)
            else:
                raise ValueError(
                    f"PDF extraction failed with PyMuPDF: {str(e)}\n"
                    "The PDF file appears to be corrupted or unreadable. "
                    "Please try opening it in a PDF viewer and re-saving it."
                )
    
    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """Extract text using pypdf/PyPDF2."""
        try:
            # Try with strict=False to handle corrupted PDFs
            if PDF_LIBRARY == "pypdf" or PDF_LIBRARY == "pypdf2":
                reader = PDF_READER(pdf_path, strict=False)
            else:
                raise ValueError("pypdf/PyPDF2 not available")
            text_parts = []
            
            # Get number of pages safely
            try:
                num_pages = len(reader.pages)
                logging.info(f"Processing {num_pages} pages from {pdf_path} using {PDF_LIBRARY}")
            except Exception:
                # If we can't get page count, try to iterate anyway
                num_pages = None
                logging.warning("Could not determine page count, attempting to extract pages...")
            
            if num_pages:
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_parts.append(text)
                        if (i + 1) % 100 == 0:
                            logging.info(f"Processed {i + 1}/{num_pages} pages...")
                    except Exception as e:
                        logging.warning(f"Error extracting text from page {i + 1}: {str(e)}")
                        continue
            else:
                # Fallback: try to iterate pages without knowing count
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_parts.append(text)
                        if (i + 1) % 100 == 0:
                            logging.info(f"Processed {i + 1} pages...")
                    except (StopIteration, IndexError):
                        break
                    except Exception as e:
                        logging.warning(f"Error extracting text from page {i + 1}: {str(e)}")
                        continue
            
            full_text = "\n".join(text_parts)
            
            if not full_text or len(full_text.strip()) == 0:
                raise ValueError(
                    "No text could be extracted from the PDF. "
                    "The PDF might be image-based (scanned) and require OCR, "
                    "or it may be corrupted. Try installing PyMuPDF: pip install pymupdf"
                )
            
            logging.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except Exception as e:
            error_msg = str(e)
            if "Root object" in error_msg or "corrupted" in error_msg.lower():
                logging.error(
                    f"PDF appears to be corrupted or has structural issues: {error_msg}\n"
                    "Trying to install PyMuPDF for better PDF handling..."
                )
                # Suggest installing PyMuPDF
                raise ValueError(
                    "PDF has structural issues. Please install PyMuPDF for better compatibility:\n"
                    "  pip install pymupdf\n"
                    "Or try opening the PDF in a viewer and re-saving it."
                )
            else:
                logging.error(f"Error extracting text from PDF {pdf_path}: {error_msg}")
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
        # Try PyMuPDF first if available
        if PDF_LIBRARY == "pymupdf":
            try:
                import fitz
                doc = fitz.open(pdf_path)
                metadata = doc.metadata
                doc.close()
                if metadata and metadata.get("title"):
                    title = metadata["title"].strip()
                    if title:
                        return title
            except Exception as e:
                logging.warning(f"Could not extract metadata from PDF: {str(e)}")
        else:
            # Try pypdf/PyPDF2
            try:
                if PDF_LIBRARY == "pypdf" or PDF_LIBRARY == "pypdf2":
                    reader = PDF_READER(pdf_path, strict=False)
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

