# How to View Data in TablePlus

The books/chunks are stored in the `embeddings` table in your PostgreSQL/TimescaleDB database.

## Table Structure

The table is named: **`embeddings`**

### Columns:

1. **`id`** - UUID (unique identifier for each chunk)
2. **`metadata`** - JSONB column containing:
   - `book_title`: Name of the book (e.g., "Introduction to Biology")
   - `chunk_index`: Index of the chunk within the book
   - `created_at`: Timestamp when the record was created
3. **`contents`** - TEXT column with the actual text content of the chunk
4. **`embedding`** - Vector column (768 dimensions) - the embedding vector

## Viewing Data in TablePlus

### Step 1: Connect to Database
1. Open TablePlus
2. Create a new connection:
   - **Host**: `localhost`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: `password` (or your docker-compose password)
   - **Database**: `postgres`

### Step 2: Find the Table
1. In the left sidebar, expand the `postgres` database
2. Look for the **`embeddings`** table
3. Double-click to open it

### Step 3: Query the Data

#### View All Records (Limited):
```sql
SELECT * FROM embeddings LIMIT 100;
```

#### View Records by Book:
```sql
SELECT 
    metadata->>'book_title' as book_title,
    metadata->>'chunk_index' as chunk_index,
    LEFT(contents, 200) as content_preview,
    created_at
FROM embeddings
WHERE metadata->>'book_title' = 'Introduction to Biology'
ORDER BY (metadata->>'chunk_index')::int;
```

#### Count Records by Book:
```sql
SELECT 
    metadata->>'book_title' as book_title,
    COUNT(*) as chunk_count
FROM embeddings
GROUP BY metadata->>'book_title';
```

#### View Sample Content:
```sql
SELECT 
    id,
    metadata->>'book_title' as book,
    metadata->>'chunk_index' as chunk,
    contents
FROM embeddings
WHERE metadata->>'book_title' = 'Introduction to Biology'
LIMIT 5;
```

## If You Don't See the Table

If the `embeddings` table doesn't appear in TablePlus:

1. **Check if Docker is running**:
   ```bash
   docker ps
   ```
   You should see the `timescaledb` container running.

2. **Verify connection**:
   - Test connection in TablePlus
   - Check if you can see the `postgres` database

3. **Check if table exists**:
   Run this query in TablePlus:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name = 'embeddings';
   ```

4. **If table doesn't exist**, run the upload script again:
   ```bash
   cd app
   python upload_pdf.py ../data/introduction_to_biology.pdf --book-title "Introduction to Biology"
   ```

## Understanding the Data

- Each **chunk** is a piece of text (1000 characters) from your PDF
- The **book_title** in metadata tells you which book the chunk came from
- The **chunk_index** shows the order of chunks within the book
- The **embedding** is a vector representation used for similarity search
- The **contents** column has the actual text that gets searched

## Quick Verification

To quickly check if data exists, run:
```bash
python app/check_database.py
```

This will show you:
- How many records are in the database
- Which books are stored
- Sample content

