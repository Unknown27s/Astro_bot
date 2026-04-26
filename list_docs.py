from database.db import get_all_documents

docs = get_all_documents()
for doc in docs:
    print(f"ID: {doc['id']} | File: {doc['original_name']}")