import chromadb

db = chromadb.PersistentClient("./chroma_db")

print(db.list_collections())
