# PDF Upload Guide

This guide explains how to upload PDF files (like Biology.pdf) to the vector database for use with the Study Buddy chat application.

## Prerequisites

1. **Docker/TimescaleDB Running**
   ```bash
   cd docker
   docker-compose up -d
   ```

2. **Environment Variables Set**
   - Make sure `.env` file exists with:
     - `GEMINI_API_KEY` - Your Gemini API key
     - `TIMESCALE_SERVICE_URL` - Database connection string (e.g., `postgresql://postgres:password@localhost:5432/postgres`)

3. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Option 1: Use the Simple Upload Script (Recommended)

```bash
cd app
python upload_pdf.py ../data/Biology.pdf
```

Or with a custom book title:
```bash
python upload_pdf.py ../data/Biology.pdf --book-title "Biology Textbook"
```

### Option 2: Use the Original Script

```bash
cd app
python insert_vectors.py --pdf ../data/Biology.pdf --book-title "Biology"
```

## Step-by-Step Process

### 1. Validate PDF First (Optional but Recommended)

Before uploading, validate that the PDF can be processed:

```bash
cd app
python validate_pdf.py ../data/Biology.pdf
```

This will:
- Check if text can be extracted from the PDF
- Show sample chunks
- Estimate processing time
- Identify any issues (e.g., scanned images that need OCR)

### 2. Upload the PDF

Run the upload script:

```bash
cd app
python upload_pdf.py ../data/Biology.pdf --book-title "Biology"
```

The process includes:
1. **PDF Processing**: Extracts text and creates chunks (1000 characters each with 200 character overlap)
2. **Embedding Generation**: Creates vector embeddings for each chunk using Gemini API
3. **Database Setup**: Creates tables if they don't exist
4. **Index Creation**: Creates search index (can take time for large PDFs)
5. **Data Insertion**: Inserts all records into the database

### 3. Verify Upload

After upload, test the chat application:

1. Start the server:
   ```bash
   python run_server.py
   ```

2. Open http://localhost:8000 in your browser

3. Ask a question about biology content, e.g.:
   - "What is photosynthesis?"
   - "Explain cell division"
   - "What are the main parts of a cell?"

## Command Options

### upload_pdf.py

```bash
python upload_pdf.py <pdf_path> [options]

Options:
  --book-title TEXT    Custom book title (optional)
  --skip-index        Skip index creation (if index already exists)
```

### insert_vectors.py

```bash
python insert_vectors.py --pdf <pdf_path> [options]

Options:
  --book-title TEXT    Custom book title (optional)
  --skip-index        Skip index creation
  --pdf-dir PATH      Process all PDFs in a directory
```

## Troubleshooting

### Error: "PDF file not found"

**Solution**: Use absolute path or ensure you're in the correct directory:
```bash
# From project root
cd app
python upload_pdf.py ../data/Biology.pdf

# Or use absolute path
python upload_pdf.py "C:\Users\ngwen\Documents\GitHub\artexo-study-buddy\data\Biology.pdf"
```

### Error: "No text could be extracted" or "Cannot find Root object"

**Possible causes**:
- PDF is image-based (scanned) and needs OCR
- PDF is corrupted or has structural issues
- PDF is password-protected
- PDF was created with incompatible software

**Solutions**: 
1. **If PDF is corrupted**:
   - Open PDF in a PDF viewer (Adobe Reader, Chrome, Edge)
   - Re-save it as a new PDF file
   - Use a PDF repair tool
   - Try converting using an online PDF converter

2. **If PDF is scanned (image-based)**:
   - Use OCR software (Adobe Acrobat, Tesseract, online OCR tools)
   - Convert to text-based PDF first
   - Ensure text is selectable in a PDF viewer

3. **General checks**:
   - Verify PDF opens correctly in a PDF viewer
   - Check if text is selectable (not just images)
   - Try opening and re-saving the PDF

### Error: "Database connection failed"

**Solution**: 
1. Check Docker is running: `docker ps`
2. Verify `TIMESCALE_SERVICE_URL` in `.env` file
3. Test connection: `psql -h localhost -U postgres -d postgres`

### Slow Processing

Large PDFs (like Biology.pdf with 175K+ lines) will take time:
- **Text extraction**: Fast
- **Chunking**: Fast
- **Embedding generation**: ~2-3 seconds per chunk (API rate limits apply)
- **Index creation**: Can take several minutes for large datasets

**Tip**: Use `--skip-index` on subsequent uploads if index already exists.

### Memory Issues

For very large PDFs:
- Process in smaller batches
- Increase system memory
- Consider processing PDFs separately and combining later

## File Structure

```
artexo-study-buddy/
├── app/
│   ├── upload_pdf.py          # Simple upload script (recommended)
│   ├── insert_vectors.py       # Original upload script
│   ├── validate_pdf.py         # PDF validation utility
│   └── ...
├── data/
│   └── Biology.pdf            # Your PDF file
└── ...
```

## Tips

1. **Validate First**: Always run `validate_pdf.py` before uploading large PDFs
2. **Use Descriptive Titles**: Set meaningful book titles for better organization
3. **Monitor Progress**: The upload script shows progress for large files
4. **Skip Index on Re-uploads**: Use `--skip-index` if you're re-uploading and index exists
5. **Check Database**: Verify records were inserted correctly after upload

## Next Steps

After successful upload:
1. Test the chat interface with biology questions
2. Verify search is working correctly
3. Consider uploading additional PDFs if needed
4. Monitor API usage (embedding generation uses API credits)

