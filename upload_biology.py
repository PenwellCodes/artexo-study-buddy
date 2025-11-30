"""
Convenience script to upload Biology.pdf from the project root.
Run this from the project root directory.
"""

import sys
import os
from pathlib import Path

# Add app directory to path
app_dir = os.path.join(os.path.dirname(__file__), "app")
sys.path.insert(0, app_dir)

# Change to app directory for imports
os.chdir(app_dir)

from upload_pdf import upload_pdf

if __name__ == "__main__":
    # Get the Biology.pdf path
    project_root = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(project_root, "data", "Biology.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Biology.pdf not found at {pdf_path}")
        print("   Please ensure the file exists in the data/ directory")
        sys.exit(1)
    
    print("📚 Uploading Biology.pdf to vector database...")
    print()
    
    success = upload_pdf(pdf_path, book_title="Biology", skip_index=False)
    sys.exit(0 if success else 1)

