"""
Utility script to validate PDF quality before uploading to database.
Checks if text extraction works and displays sample content.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_processor import PDFProcessor


def validate_pdf(pdf_path: str, sample_chunks: int = 3):
    """
    Validate a PDF file by extracting and displaying sample text.
    
    Args:
        pdf_path: Path to the PDF file
        sample_chunks: Number of sample chunks to display
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return False
    
    print(f"📄 Validating PDF: {pdf_path}")
    print("=" * 80)
    
    try:
        # Initialize processor
        processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
        
        # Extract book title
        book_title = processor.extract_book_title(pdf_path)
        print(f"📚 Book Title: {book_title}")
        print()
        
        # Extract text
        print("📖 Extracting text from PDF...")
        text = processor.extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) == 0:
            print("❌ Error: No text could be extracted from the PDF.")
            print("   This might be a scanned PDF (image-based) that needs OCR.")
            return False
        
        print(f"✅ Successfully extracted {len(text):,} characters")
        print(f"   Text length: {len(text):,} characters")
        print()
        
        # Create chunks
        print("✂️  Creating chunks...")
        chunks = processor.chunk_text(text)
        print(f"✅ Created {len(chunks)} chunks")
        print()
        
        # Display sample chunks
        print(f"📋 Sample of first {min(sample_chunks, len(chunks))} chunks:")
        print("=" * 80)
        for i, chunk in enumerate(chunks[:sample_chunks]):
            print(f"\n--- Chunk {i+1} ({len(chunk)} characters) ---")
            # Display first 300 characters of each chunk
            preview = chunk[:300].replace('\n', ' ')
            print(preview + ("..." if len(chunk) > 300 else ""))
        
        print()
        print("=" * 80)
        print("✅ PDF validation successful!")
        print(f"   Ready to upload: {len(chunks)} chunks will be created")
        print(f"   Estimated processing time: ~{len(chunks) * 2} seconds (rough estimate)")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error validating PDF: {error_msg}")
        
        if "Root object" in error_msg or "corrupted" in error_msg.lower():
            print()
            print("=" * 80)
            print("⚠️  PDF Structure Issue Detected")
            print("=" * 80)
            print()
            print("The PDF appears to be corrupted or has structural issues.")
            print()
            print("Possible solutions:")
            print("1. Open the PDF in a PDF viewer (Adobe Reader, Chrome, etc.)")
            print("   and re-save it as a new PDF file")
            print("2. Use a PDF repair tool to fix the file")
            print("3. If the PDF is scanned (image-based), use OCR software")
            print("   to convert it to text-based PDF first")
            print("4. Try converting the PDF using an online PDF converter")
            print()
            print("Note: The PDF may still contain readable content, but the")
            print("structure needs to be repaired for automated extraction.")
            print("=" * 80)
        else:
            import traceback
            traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_pdf.py <path_to_pdf>")
        print("Example: python validate_pdf.py ../data/Biology.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    success = validate_pdf(pdf_path)
    sys.exit(0 if success else 1)

