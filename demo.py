from langchain_community.vectorstores import chroma
from langchain_community.llms.ollama import Ollama

# from langchain_community.llms.anthropic import Anthropic
# from langchain_anthropic import AnthropicLLM
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings


from langchain.chains.combine_documents import create_stuff_documents_chain

# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredHTMLLoader,
)
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os, chromadb
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=OPENAI_API_KEY)


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
                            try:
                                file_path = os.path.join(root, file)
                                loader = UnstructuredPowerPointLoader(file_path)
                                data = loader.load()
                            except Exception as e:
                                print(e)
                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)
                        elif file.endswith(".pdf"):
                            try:
                                file_path = os.path.join(root, file)
                                loader = PyPDFLoader(file_path, extract_images=True)
                                data = loader.load()
                            except Exception as e:
                                print(e)
                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)
                        elif file.endswith(".html"):
                            try:
                                file_path = os.path.join(root, file)
                                loader = UnstructuredHTMLLoader(file_path)
                                data = loader.load()
                            except Exception as e:
                                print(e)
                            # Add the documents to the list
                            print(f"Loaded {file_path}")
                            all_documents.extend(data)

            start_directory = f"./data/{course.name}"
            collect_files(start_directory)

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    data = text_splitter.split_documents(all_documents)
    print("Collection name:")
    print(course.name.lower().strip().replace(" ", "_"))
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
        template = """You are a helpful assistant who has context to a specific course in
        the Learning Management System called Canvas. 
        Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer. 
        Make sure to keep the answer concise and easy to understand, only further expanding when requested to by the user. 
        {context}
        Question: {input}
        Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate(
            input_variables=["input", "context"],
            template=template,
        )

        # llm = Ollama(
        #     model="llama2:13b",
        #     callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        # )
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            anthropic_api_key=ANTHROPIC_API_KEY,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        )

        combine_docs_chain = create_stuff_documents_chain(llm, QA_CHAIN_PROMPT)

        qa_chain = create_retrieval_chain(
            retriever=vectorstore.as_retriever(), combine_docs_chain=combine_docs_chain
        )

        result = qa_chain.invoke({"input": query})
        print(result["answer"])
