# Llama Index
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    SummaryIndex,
)

from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.readers.web import SimpleWebPageReader

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext


documents = SimpleDirectoryReader("data", recursive=True).load_data()
# documents.append(
#     SimpleWebPageReader(html_to_text=True).load_data(
#         ["http://sharkeyphysics.weebly.com/faqcalendar.html"]
#     )
# )
# print(documents)
# print(len(documents))

# Set ollama embedding and LLM models
ollama_embedding = OllamaEmbedding(
    model_name="mxbai-embed-large:latest",
    base_url="http://localhost:11434",
    ollama_additional_kwargs={"mirostat": 0},
)
Settings.embed_model = ollama_embedding
Settings.llm = Ollama(model="mistral", request_timeout=30.0)

# Save index to disk
db = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db.get_or_create_collection("quickstart")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store, storage_context=storage_context
)

# Load index from disk
db2 = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db2.get_or_create_collection("quickstart")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store)


query_engine = index.as_query_engine()

# res = query_engine.query("Tell me about all the assignments for the 6th week")
# print(res)


def query(query):
    return query_engine.query(query)
