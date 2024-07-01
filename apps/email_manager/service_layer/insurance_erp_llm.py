from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
    SystemMessage
)
import json
import torch


class InsuranceERPLLM:
    def __init__(self):
        torch.cuda.empty_cache()

        # Load embeddings model
        model_name = 'sentence-transformers/paraphrase-mpnet-base-v2'

        # Create FAISS index from documents
        self.embeddings_model = HuggingFaceEmbeddings(model_name=model_name)
        self.documents_vector_store = None

        self.num_of_choices = 3

        self.queries = {
            "net_premium": "What is the net premium amount? It wll usually be the last value of a breakdown",
            "issue_date": "What is the starting date of the coverage period?",
            "covernote_number": "What is the cover note number which starts with 'COV'? Rule: It must start with 'COV'",
            "policy_number": "What is the policy number which starts with 'PL'? Rule: It must start with 'PL'"
        }

        systm_msgs = [
            "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
            f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
            "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
            "The answer will be singular. use an '=' sign before the answer.",
            "If you cannot find the answer easily, say the following: '404 Not Found'.",
            "There should be only one '=' sign in the answer if it is found.",
            "for any date that is found, convert it into the following format: YYYY-MM-DD.",
            "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
            "If the answer or amount or date is found, use an '=' sign before the answer or amount or date."
        ]
        self.systm_msg = "\n".join(systm_msgs)
        self.doc_chunk_size = 1000
        self.doc_chunk_overlap=200
        self.convo_chunk_size = 500
        self.convo_chunk_overlap=100
        self.document_query_results = {}
        self.convo_query_results = {}

    def store_documents_in_vector_store(self, file_paths):
        all_documents = []
        
        for path in file_paths:
            # Load PDF and split into documents
            loader = PyPDFLoader(path)
            raw_documents = loader.load()

            # Split documents into smaller chunks
            text_splitter = CharacterTextSplitter(chunk_size=self.doc_chunk_size, chunk_overlap=self.doc_chunk_overlap, separator="\n")
            documents = text_splitter.split_documents(raw_documents)
            all_documents.extend(documents)

            # Debug: Print the number of documents and their lengths
            # print(f"Number of documents from {path}: {len(documents)}")
            # for i, doc in enumerate(documents):
            #     print(f"Document {i} length: {len(doc.page_content)}")
            #     print(f"Document {i} content: {doc.page_content[:200]}...")

        # Create FAISS index from all documents
        self.documents_vector_store = FAISS.from_documents(all_documents, self.embeddings_model)

    def store_convo_in_vector_store(self, convo):
        all_texts = []
        
        # Load PDF and split into documents

        # Split documents into smaller chunks
        text_splitter = CharacterTextSplitter(chunk_size=self.convo_chunk_size, chunk_overlap=self.convo_chunk_overlap, separator=" ")
        texts_chunks = text_splitter.split_text(convo)
        all_texts.extend(texts_chunks)

        # Debug: Print the number of documents and their lengths
        # print(f"Number of documents from {path}: {len(documents)}")
        # for i, doc in enumerate(documents):
        #     print(f"Document {i} length: {len(doc.page_content)}")
        #     print(f"Document {i} content: {doc.page_content[:200]}...")

        self.convo_vector_store = FAISS.from_texts(all_texts, self.embeddings_model)


    def get_vectors(self, vector_store):
        vectors_dict = {}
        if vector_store and vector_store.index:
            vectors = vector_store.index.reconstruct_n(0, vector_store.index.ntotal)
            for i, vector in enumerate(vectors):
                vectors_dict[i] = vector
        return vectors_dict

    def search_documents_vector_store(self):

        # Retrieve and print the top three relevant chunks for each query
        results = {}
        for key, query in self.queries.items():
            retrieved_docs = self.documents_vector_store.similarity_search(query, k=self.num_of_choices)
            results[key] = [doc.page_content for doc in retrieved_docs] if retrieved_docs else ["Not found"]

        # Print the top three relevant chunks for each query
        self.document_query_results = {}
        for key, contents in results.items():
            self.document_query_results[key] = {}
            for i, content in enumerate(contents):
                self.document_query_results[key][f"Choice {i+1}"] = content

        print(json.dumps(self.document_query_results, indent=4))
        print("Number of tokens:", len(str(self.document_query_results).split()))

    def search_convo_vector_store(self):

        # Retrieve and print the top three relevant chunks for each query
        results = {}
        for key, query in self.queries.items():
            retrieved_chunks = self.convo_vector_store.similarity_search(query, k=self.num_of_choices)
            results[key] = [text_chunk.page_content for text_chunk in retrieved_chunks] if retrieved_chunks else ["Not found"]

        # Print the top three relevant chunks for each query
        self.convo_query_results = {}
        for key, contents in results.items():
            self.convo_query_results[key] = {}
            for i, content in enumerate(contents):
                self.convo_query_results[key][f"Choice {i+1}"] = content

        print(json.dumps(self.convo_query_results, indent=4))
        print("Number of tokens:", len(str(self.convo_query_results).split()))

    def query_from_final_results(self, similarity_search_results: dict):
        llm = ChatOpenAI(model_name='gpt-3.5-turbo')

        for key, content in similarity_search_results.items():
            # Truncate content to fit within token limits
            messages = [
                SystemMessage(content=self.systm_msg),
                HumanMessage(content=f"query: {self.queries[key]}, content: {content}")
            ]

            response = llm(messages)
            print(response.content)
            print("-----")