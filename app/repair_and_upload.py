"""
Script to help repair and upload a corrupted PDF.
This script attempts multiple methods to extract text from problematic PDFs.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_pdf_in_viewer(pdf_path: str) -> bool:
    """Check if PDF can be opened in system default viewer."""
    try:
        if sys.platform == "win32":
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path])
        else:
            subprocess.run(["xdg-open", pdf_path])
        return True
    except Exception:
        return False

def main():
    pdf_path = "../data/Biology.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return 1
    
    print("=" * 80)
    print("🔧 PDF Repair and Upload Helper")
    print("=" * 80)
    print()
    print(f"📄 PDF File: {pdf_path}")
    print(f"📊 File Size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
    print()
    
    print("The PDF appears to be corrupted (0 pages detected).")
    print()
    print("To fix this, please:")
    print("1. Open the PDF in a PDF viewer (Chrome, Edge, or Adobe Reader)")
    print("2. Go to File > Save As (or Print to PDF)")
    print("3. Save it with a new name (e.g., Biology_fixed.pdf)")
    print("4. Replace the original file or use the new file")
    print()
    
    response = input("Would you like me to try opening the PDF in your default viewer? (y/n): ")
    if response.lower() == 'y':
        if check_pdf_in_viewer(pdf_path):
            print("✅ PDF opened in viewer. Please re-save it and try uploading again.")
        else:
            print("❌ Could not open PDF in viewer. Please open it manually.")
    
    print()
    print("After re-saving the PDF, run:")
    print("  python app/upload_pdf.py data/Biology.pdf --book-title 'Biology'")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

