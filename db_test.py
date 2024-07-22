import chromadb
import appwrite


db = chromadb.PersistentClient("./chroma_db")

print(db.list_collections())
print(
    db.get_or_create_collection(
        "asdf", metadata={"asdf": "asdf", "asdf": "asdf", "0ofk": "1323"}
    )
)
print(db.get_collection("asdf").metadata)

collection = db.get_collection("asdf")

collection.add()
