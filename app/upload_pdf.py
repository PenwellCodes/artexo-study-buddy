"""
Simple script to upload a PDF file to the vector database.
This is a convenience wrapper around insert_vectors.py.
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from insert_vectors import process_pdf_file, vec


def upload_pdf(pdf_path: str, book_title: str = None, skip_index: bool = False):
    """
    Upload a PDF file to the vector database.
    
    Args:
        pdf_path: Path to the PDF file
        book_title: Optional book title
        skip_index: Whether to skip index creation
    """
    print("=" * 80)
    print("📚 PDF Upload to Vector Database")
    print("=" * 80)
    print()
    
    # Validate PDF path
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return False
    
    # Resolve absolute path
    pdf_path = os.path.abspath(pdf_path)
    print(f"📄 PDF File: {pdf_path}")
    print()
    
    try:
        # Process PDF
        print("Step 1/3: Processing PDF and generating embeddings...")
        records_df = process_pdf_file(pdf_path, book_title=book_title, show_progress=True)
        
        if records_df.empty:
            print("❌ Error: No records generated from PDF")
            return False
        
        print()
        print("Step 2/3: Setting up database...")
        vec.create_tables()
        
        if not skip_index:
            print("   Creating index (this may take a while for large PDFs)...")
            vec.create_index()
        else:
            print("   Skipping index creation...")
        
        print()
        print("Step 3/3: Inserting records into database...")
        vec.upsert(records_df)
        
        print()
        print("=" * 80)
        print("✅ Upload Complete!")
        print(f"   Records inserted: {len(records_df)}")
        print(f"   Book title: {book_title or 'Auto-detected'}")
        print("=" * 80)
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Upload Failed: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload a PDF file to the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload Biology.pdf with auto-detected title
  python upload_pdf.py ../data/Biology.pdf
  
  # Upload with custom title
  python upload_pdf.py ../data/Biology.pdf --book-title "Biology Textbook"
  
  # Upload and skip index creation (if index already exists)
  python upload_pdf.py ../data/Biology.pdf --skip-index
        """
    )
    
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file to upload"
    )
    
    parser.add_argument(
        "--book-title",
        type=str,
        default=None,
        help="Book title (optional, will be extracted from PDF if not provided)"
    )
    
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip creating index (useful if index already exists)"
    )
    
    args = parser.parse_args()
    
    success = upload_pdf(args.pdf_path, args.book_title, args.skip_index)
    sys.exit(0 if success else 1)

