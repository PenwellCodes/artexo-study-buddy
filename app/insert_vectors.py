import argparse
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from database.vector_store import VectorStore
from services.pdf_processor import PDFProcessor
from timescale_vector.client import uuid_from_time

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
            "id": str(uuid_from_time(datetime.now())),
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
            "id": str(uuid_from_time(datetime.now())),
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


def process_pdf_file(pdf_path: str, book_title: str = None):
    """Process a PDF file and return records DataFrame.

    Args:
        pdf_path: Path to the PDF file.
        book_title: Optional book title. If not provided, will be extracted from PDF.

    Returns:
        A pandas DataFrame with records ready for insertion.
    """
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    chunks = processor.process_pdf(pdf_path, book_title=book_title)
    
    records = []
    for chunk in chunks:
        record = prepare_record_from_pdf_chunk(chunk, chunk["book_title"])
        records.append(record)
    
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
    if args.csv:
        print("Processing CSV file...")
        records_df = process_csv_file(args.csv)
    elif args.pdf:
        print("Processing PDF file...")
        records_df = process_pdf_file(args.pdf, book_title=args.book_title)
    elif args.pdf_dir:
        print("Processing PDF directory...")
        records_df = process_pdf_directory(args.pdf_dir)
    else:
        # Default: try to process CSV for backward compatibility
        csv_path = "../data/faq_dataset.csv"
        if os.path.exists(csv_path):
            print("Processing default CSV file...")
            records_df = process_csv_file(csv_path)
        else:
            parser.print_help()
            return

    # Create tables and insert data
    print("Creating tables...")
    vec.create_tables()
    
    if not args.skip_index:
        print("Creating index...")
        vec.create_index()  # DiskAnnIndex
    else:
        print("Skipping index creation...")
    
    print(f"Inserting {len(records_df)} records...")
    vec.upsert(records_df)
    print("Done!")


if __name__ == "__main__":
    main()
