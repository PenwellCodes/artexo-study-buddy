import argparse
import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from database.vector_store import VectorStore
from services.pdf_processor import PDFProcessor

# Initialize VectorStore
vec = VectorStore()


def prepare_record_from_csv(row):
    """Prepare a record from CSV row for insertion into the vector store.

    This function creates a record with a UUID version 1 as the ID, which captures
    the current time or a specified time.

    Note:
        - By default, this function uses the current time for the UUID.
        - To use a specific time:
          1. Import the datetime module.
          2. Create a datetime object for your desired time.
          3. Use uuid_from_time(your_datetime) instead of uuid_from_time(datetime.now()).

        Example:
            from datetime import datetime
            specific_time = datetime(2023, 1, 1, 12, 0, 0)
            id = str(uuid_from_time(specific_time))

        This is useful when your content already has an associated datetime.
    """
    content = f"Question: {row['question']}\nAnswer: {row['answer']}"
    embedding = vec.get_embedding(content)
    return pd.Series(
        {
            "id": str(uuid.uuid1()),
            "metadata": {
                "category": row["category"],
                "created_at": datetime.now().isoformat(),
            },
            "contents": content,
            "embedding": embedding,
        }
    )


def prepare_record_from_pdf_chunk(chunk_data: dict, book_title: str):
    """Prepare a record from PDF chunk for insertion into the vector store.

    Args:
        chunk_data: Dictionary containing 'content' and 'chunk_index'.
        book_title: The title of the book.

    Returns:
        A pandas Series with the record data.
    """
    content = chunk_data["content"]
    embedding = vec.get_embedding(content)
    return pd.Series(
        {
            "id": str(uuid.uuid1()),
            "metadata": {
                "book_title": book_title,
                "chunk_index": chunk_data["chunk_index"],
                "created_at": datetime.now().isoformat(),
            },
            "contents": content,
            "embedding": embedding,
        }
    )


def process_csv_file(csv_path: str):
    """Process a CSV file and return records DataFrame."""
    df = pd.read_csv(csv_path, sep=";")
    records_df = df.apply(prepare_record_from_csv, axis=1)
    return records_df


def process_pdf_file(pdf_path: str, book_title: str = None, show_progress: bool = True):
    """Process a PDF file and return records DataFrame.

    Args:
        pdf_path: Path to the PDF file.
        book_title: Optional book title. If not provided, will be extracted from PDF.
        show_progress: Whether to show progress indicators.

    Returns:
        A pandas DataFrame with records ready for insertion.
    """
    if show_progress:
        print(f"📄 Processing PDF: {os.path.basename(pdf_path)}")

    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    chunks = processor.process_pdf(pdf_path, book_title=book_title)

    if show_progress:
        print(f"✅ Extracted {len(chunks)} chunks")
        print("🔄 Generating embeddings (this may take a while for large PDFs)...")

    records = []
    total_chunks = len(chunks)
    for idx, chunk in enumerate(chunks):
        if show_progress and (idx + 1) % 10 == 0:
            print(
                f"   Progress: {idx + 1}/{total_chunks} chunks processed ({((idx + 1) / total_chunks * 100):.1f}%)"
            )

        try:
            record = prepare_record_from_pdf_chunk(chunk, chunk["book_title"])
            records.append(record)
        except Exception as e:
            print(f"⚠️  Warning: Failed to process chunk {idx + 1}: {str(e)}")
            continue

    if show_progress:
        print(f"✅ Successfully processed {len(records)}/{total_chunks} chunks")

    return pd.DataFrame(records)


def process_pdf_directory(pdf_directory: str):
    """Process all PDF files in a directory and return combined records DataFrame.

    Args:
        pdf_directory: Path to directory containing PDF files.

    Returns:
        A pandas DataFrame with records from all PDFs ready for insertion.
    """
    pdf_dir = Path(pdf_directory)
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        raise ValueError(f"No PDF files found in directory: {pdf_directory}")

    all_records = []
    for pdf_file in pdf_files:
        print(f"Processing PDF: {pdf_file.name}")
        records_df = process_pdf_file(str(pdf_file))
        all_records.append(records_df)

    return pd.concat(all_records, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(
        description="Insert vectors into the database from CSV or PDF files"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file to process (legacy support)",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to PDF file to process",
    )
    parser.add_argument(
        "--pdf-dir",
        type=str,
        help="Path to directory containing PDF files to process",
    )
    parser.add_argument(
        "--book-title",
        type=str,
        help="Book title (for PDF processing, optional)",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip creating index (useful if index already exists)",
    )

    args = parser.parse_args()

    # Determine which mode to use
    try:
        if args.csv:
            print("📊 Processing CSV file...")
            records_df = process_csv_file(args.csv)
        elif args.pdf:
            print("📄 Processing PDF file...")
            # Resolve path - handle both relative and absolute paths
            pdf_path = args.pdf
            if not os.path.isabs(pdf_path):
                # Try relative to current directory first
                if not os.path.exists(pdf_path):
                    # Try relative to app directory
                    app_dir = os.path.dirname(os.path.abspath(__file__))
                    alt_path = os.path.join(app_dir, pdf_path)
                    if os.path.exists(alt_path):
                        pdf_path = alt_path
                    else:
                        # Try relative to parent directory
                        parent_dir = os.path.dirname(app_dir)
                        alt_path = os.path.join(parent_dir, pdf_path.lstrip("../"))
                        if os.path.exists(alt_path):
                            pdf_path = alt_path

            if not os.path.exists(pdf_path):
                print(f"❌ Error: PDF file not found: {args.pdf}")
                print(f"   Tried: {pdf_path}")
                return 1

            records_df = process_pdf_file(pdf_path, book_title=args.book_title)
        elif args.pdf_dir:
            print("📁 Processing PDF directory...")
            records_df = process_pdf_directory(args.pdf_dir)
        else:
            # Default: try to process CSV for backward compatibility
            csv_path = "../data/faq_dataset.csv"
            if os.path.exists(csv_path):
                print("📊 Processing default CSV file...")
                records_df = process_csv_file(csv_path)
            else:
                parser.print_help()
                return 1

        if records_df.empty:
            print("❌ Error: No records to insert")
            return 1

        # Create tables and insert data
        print("\n🗄️  Setting up database...")
        print("   Creating tables...")
        vec.create_tables()

        if not args.skip_index:
            print("   Creating index (this may take a while)...")
            vec.create_index()  # DiskAnnIndex
        else:
            print("   Skipping index creation (using existing index)...")

        print(f"\n💾 Inserting {len(records_df)} records into database...")
        vec.upsert(records_df)
        print("✅ Done! Data successfully uploaded to database.")
        print(f"   Total records inserted: {len(records_df)}")
        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
