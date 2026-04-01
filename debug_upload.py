#!/usr/bin/env python3
"""
Diagnostic script to debug PDF upload issues and 422 errors.
Run this to test each step of the upload pipeline.
"""

import sys
from pathlib import Path

print("=" * 80)
print("🔍 AstroBot Upload Pipeline Diagnostic")
print("=" * 80)

# Test 1: Check dependencies
print("\n[1/6] Checking dependencies...")
try:
    import PyPDF2
    print("✅ PyPDF2 installed")
except ImportError:
    print("❌ PyPDF2 NOT installed - install with: pip install PyPDF2")
    sys.exit(1)

try:
    from ingestion.parser import parse_document, parse_pdf
    print("✅ Parser module imported")
except ImportError as e:
    print(f"❌ Cannot import parser: {e}")
    sys.exit(1)

# Test 2: Check upload directory
print("\n[2/6] Checking upload directory...")
from config import UPLOAD_DIR, CHROMA_PERSIST_DIR

if UPLOAD_DIR.exists():
    files = list(UPLOAD_DIR.glob("*"))
    pdf_files = [f for f in files if f.suffix.lower() == ".pdf"]
    print(f"✅ Upload directory exists: {UPLOAD_DIR}")
    print(f"   Total files: {len(files)}")
    print(f"   PDF files: {len(pdf_files)}")
    if pdf_files:
        print(f"   Sample PDFs: {[f.name for f in pdf_files[:3]]}")
else:
    print(f"❌ Upload directory missing: {UPLOAD_DIR}")
    sys.exit(1)

# Test 3: Check ChromaDB
print("\n[3/6] Checking ChromaDB...")
if CHROMA_PERSIST_DIR.exists():
    size_mb = sum(f.stat().st_size for f in CHROMA_PERSIST_DIR.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"✅ ChromaDB directory exists: {CHROMA_PERSIST_DIR}")
    print(f"   Size: {size_mb:.1f} MB")
    try:
        from ingestion.embedder import get_collection
        col = get_collection()
        print(f"   Vectors in ChromaDB: {col.count()}")
        print(f"   Collection: {col.name}")
    except Exception as e:
        print(f"⚠️  ChromaDB connection error: {e}")
else:
    print(f"⚠️  ChromaDB directory missing (will be created on first use): {CHROMA_PERSIST_DIR}")

# Test 4: Test parser with existing PDF
print("\n[4/6] Testing PDF parser with existing file...")
pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
if pdf_files:
    test_pdf = pdf_files[0]
    print(f"Testing with: {test_pdf.name}")
    try:
        text, error = parse_document(str(test_pdf))
        if text:
            print(f"✅ Parse SUCCESS")
            print(f"   Extracted: {len(text)} characters")
            print(f"   First 100 chars: {text[:100]}")
        else:
            print(f"❌ Parse FAILED")
            print(f"   Error: {error}")
    except Exception as e:
        print(f"❌ Parser exception: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  No PDF files in upload directory to test")

# Test 5: Test database
print("\n[5/6] Checking SQLite database...")
try:
    from database.db import get_connection
    conn = get_connection()

    # Check tables
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    print(f"✅ Database connected")
    print(f"   Tables: {', '.join([t[0] for t in tables])}")

    # Count documents
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print(f"   Documents: {doc_count}")
    print(f"   Users: {user_count}")

    conn.close()
except Exception as e:
    print(f"❌ Database error: {e}")

# Test 6: Test chunker
print("\n[6/6] Testing document chunker...")
if pdf_files:
    try:
        text, _ = parse_document(str(pdf_files[0]))
        if text:
            from ingestion.chunker import chunk_document
            chunks = chunk_document(text, source_name=pdf_files[0].name)
            if chunks:
                print(f"✅ Chunking SUCCESS")
                print(f"   Generated chunks: {len(chunks)}")
                print(f"   Average chunk size: {len(text) // len(chunks)} characters")
            else:
                print(f"❌ No chunks generated (text too short?)")
                print(f"   Text length: {len(text)}")
    except Exception as e:
        print(f"❌ Chunker error: {e}")

print("\n" + "=" * 80)
print("📋 SUMMARY OF FILES INVOLVED IN UPLOAD PROCESS:")
print("=" * 80)
print("""
MAIN FILES:
  1. api_server.py          - FastAPI upload endpoint (lines 329-410)
  2. views/admin.py         - Streamlit upload UI (lines 38-151)

PARSING:
  3. ingestion/parser.py    - Document parser (lines 1-200)
     - parse_pdf()         - PDF text extraction (lines 13-23)
     - parse_docx()        - DOCX parsing (lines 26-42)
     - parse_txt()         - TXT parsing (lines 45-56)
     - parse_document()    - Main entry point (lines 138-154)

CHUNKING:
  4. ingestion/chunker.py   - Text chunking (lines 1-150)
     - chunk_document()    - Main chunking function

EMBEDDING/STORAGE:
  5. ingestion/embedder.py  - Embeddings & ChromaDB (lines 1-200)
     - store_chunks()      - Store in ChromaDB (lines 74-109)
     - get_collection()    - Get ChromaDB collection (lines 24-32)

DATABASE:
  6. database/db.py         - SQLite operations (lines 1-500)
     - add_document()      - Record document metadata (lines 312-322)
     - get_connection()    - Database connection (lines 18-30)

CONFIGURATION:
  7. config.py              - All settings (lines 1-100)
     - UPLOAD_DIR          - Where files are saved
     - SUPPORTED_EXTENSIONS - Allowed file types
     - CHUNK_SIZE          - Text chunk size
     - EMBEDDING_MODEL     - Embedding model name
""")

print("\n✅ Diagnostic complete!")
