from langchain_community.vectorstores import chroma
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredHTMLLoader,
)
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os, chromadb

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")


def demo(course, resume, reindex):
    db = chromadb.PersistentClient("./chroma_db")

    try:
        collection_exists = db.get_collection(
            course.name.lower().strip().replace(" ", "_")
        )
    except ValueError:
        collection_exists = False
    # load the pdf and split it into chunks
    all_documents = []

    db = chromadb.PersistentClient("./chroma_db")

    if not collection_exists or reindex:
        if resume:
            loader = PyPDFLoader("./data/Mushui Zhu Extended Resume March 2024.pdf")
            data = loader.load()
            all_documents.extend(data)

        else:
            # Create an empty list to store all documents

            def collect_files(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith(".pptx"):
                            file_path = os.path.join(root, file)
                            loader = UnstructuredPowerPointLoader(file_path)
                            data = loader.load()

                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)
                        elif file.endswith(".pdf"):
                            file_path = os.path.join(root, file)
                            loader = PyPDFLoader(file_path, extract_images=True)
                            data = loader.load()

                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)
                        elif file.endswith(".html"):
                            file_path = os.path.join(root, file)
                            loader = UnstructuredHTMLLoader(file_path)
                            data = loader.load()

                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)

            start_directory = f"./data/{course.name}"
            collect_files(start_directory)

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    data = text_splitter.split_documents(all_documents)

    if not collection_exists or reindex:
        # Update the collection
        vectorstore = chroma.Chroma.from_documents(
            documents=data,
            embedding=embeddings,
            persist_directory="./chroma_db",
            collection_name=f'{course.name.lower().strip().replace(" ", "_")}',
        )
    else:
        # Use existing collection
        vectorstore = chroma.Chroma(
            collection_name=f'{course.name.lower().strip().replace(" ", "_")}',
            persist_directory="./chroma_db",
            embedding_function=embeddings,
        )

    while True:
        query = input("\nQuery: ")
        if query == "exit":
            break
        if query.strip() == "":
            continue

        # Prompt
        template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer. 
        Use three sentences maximum and keep the answer as concise as possible. 
        {context}
        Question: {question}
        Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=template,
        )

        llm = Ollama(
            model="llama2:13b",
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        )

        result = qa_chain.invoke({"query": query})
