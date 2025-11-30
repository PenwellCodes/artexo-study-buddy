"""
Script to check and display data stored in the vector database.
This helps verify that PDFs/books were uploaded correctly.
"""

import sys
import os
import pandas as pd

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.vector_store import VectorStore
from config.settings import get_settings


def check_database():
    """Check what data is stored in the database."""
    print("=" * 80)
    print("📊 Database Content Check")
    print("=" * 80)
    print()
    
    try:
        vec = VectorStore()
        settings = get_settings()
        table_name = settings.vector_store.table_name
        
        print(f"📋 Table Name: {table_name}")
        db_url = settings.database.service_url
        if db_url:
            db_info = db_url.split('@')[-1] if '@' in db_url else db_url
            print(f"🔗 Database: {db_info}")
        else:
            print("🔗 Database: Not configured (check .env file)")
        print()
        
        # Query to get all records (limited to first 100 for display)
        print("🔍 Querying database...")
        
        # Use a simple search to get some records
        # We'll search for a common word to get results
        try:
            results = vec.search("biology", limit=100)
            
            if results.empty:
                print("❌ No records found in the database!")
                print()
                print("Possible reasons:")
                print("1. No data has been uploaded yet")
                print("2. Database connection issue")
                print("3. Table doesn't exist")
                return False
            
            print(f"✅ Found {len(results)} records (showing first 100)")
            print()
            
            # Show summary by book
            if "book_title" in results.columns:
                book_counts = results["book_title"].value_counts()
                print("📚 Books in database:")
                print("-" * 80)
                for book, count in book_counts.items():
                    print(f"  • {book}: {count} chunks")
                print()
            
            # Show sample records
            print("📄 Sample Records (first 5):")
            print("=" * 80)
            for idx, row in results.head(5).iterrows():
                print(f"\nRecord {idx + 1}:")
                if "book_title" in row:
                    print(f"  Book: {row['book_title']}")
                if "chunk_index" in row:
                    print(f"  Chunk Index: {row['chunk_index']}")
                if "content" in row:
                    content_preview = str(row['content'])[:200].replace('\n', ' ')
                    print(f"  Content Preview: {content_preview}...")
                if "created_at" in row:
                    print(f"  Created: {row['created_at']}")
                print("-" * 80)
            
            # Get total count using a different approach
            print()
            print("💡 To see all data in TablePlus:")
            print(f"   1. Connect to: {settings.database.service_url.split('@')[-1] if '@' in settings.database.service_url else 'your database'}")
            print(f"   2. Look for table: {table_name}")
            print(f"   3. Query: SELECT * FROM {table_name} LIMIT 100;")
            print()
            print("   The table has these columns:")
            print("   - id: Unique identifier")
            print("   - metadata: JSON with book_title, chunk_index, created_at")
            print("   - contents: The actual text content")
            print("   - embedding: Vector embedding (768 dimensions)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error querying database: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        print()
        print("Check:")
        print("1. Docker/TimescaleDB is running")
        print("2. TIMESCALE_SERVICE_URL is set correctly in .env file")
        print("3. Database connection string format: postgresql://user:password@host:port/database")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)

