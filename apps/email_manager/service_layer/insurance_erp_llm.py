from datetime import datetime
from os import environ
import re
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
    SystemMessage,
    AIMessage
)
import json
import torch
from transformers import pipeline
from statistics import mode

from apps.account_manager.models.user import User
from apps.claim_manager.models.claim import Claim
from apps.claim_manager.models.claim_debited import ClaimDebited
from apps.client_manager.models.client import Client
from apps.risk_manager.models.policy import Policy, PolicyFile
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from apps.risk_manager.models.premium_credited import PremiumCredited
from apps.risk_manager.models.risk import Risk
from db_tables import Base, SQLClaimDocument, SQLPolicyFile, SQLPremiumCreditedFile, SQLClaimDebitedFile
from django.db.models import Q

class InsuranceERPLLM:
    def __init__(self):
        torch.cuda.empty_cache()

        # Load embeddings model
        model_name = 'sentence-transformers/paraphrase-mpnet-base-v2'

        # Create FAISS index from documents
        self.embeddings_model = HuggingFaceEmbeddings(model_name=model_name)
        self.documents_vector_store = None

        self.num_of_choices = 3

        self.event_type = None

        self.event_types = [
            "policy_issued", 
            "premium_paid", 
            "claim_intimated", 
            "claim_paid",
        ]

        self.queries = {
            "net_premium": "What is the net premium amount?",
            "issue_date": "What is the starting date of the coverage period?",
            "covernote_number": "What is the cover note number which starts with 'COV'? Rule: It must start with 'COV'",
            "policy_number": "What is the policy number which starts with 'PL'? Rule: It must start with 'PL'",
            "claim_number": "What is the claim number which starts with 'CL'? Rule: It must start with 'CL'",
            "customer_name": "what is the name of the customer(insured)? Hint: It will appear after the 'insured' word",
            "risk_type": "what is the type of the risk?",
            "event_type": "what is the type of event?",
            "sum_insured": "what is the total sum insured?",
            "premium_paid_amount": "what is the amount of premium paid?",
            "claim_intimation_amount": "what is the amount of claim intimated?",
            "claim_paid_amount": "what is the amount of claim paid?",
            "premium_paid_date": "what is the date of premium paid?",
            "claim_intimation_date": "what is the date of claim intimated?",
            "claim_paid_date": "what is the date of claim paid?",
        }

        self.convo_skip_keys = {
            "issue_date": "issue_date",
            "policy_number": "policy_number",
            "covernote_number": "covernote_number",
            "claim_number": "claim_number",
        }

        self.convo_priority_keys = {
            "risk_type": "risk_type",
            "event_type": "event_type",
        }

        self.queries_results = {
            "net_premium": {
                "value": None,
                "type": "double"
            },
            "issue_date": {
                "value": None,
                "type": "datetime"
            },
            "covernote_number": {
                "value": None,
                "type": "string"
            },
            "policy_number": {
                "value": None,
                "type": "string"
            },
            "claim_number": {
                "value": None,
                "type": "string"
            },
            "customer_name": {
                "value": None,
                "type": "string"
            },
            "risk_type": {
                "value": None,
                "type": "string"
            },
            "event_type": {
                "value": None,
                "type": "string"
            },
            "sum_insured": {
                "value": None,
                "type": "double"
            },
            "premium_paid_amount": {
                "value": None,
                "type": "double"
            },
            "claim_intimation_amount": {
                "value": None,
                "type": "double"
            },
            "claim_paid_amount": {
                "value": None,
                "type": "double"
            },
            "premium_paid_date": {
                "value": None,
                "type": "datetime"
            },
            "claim_intimation_date": {
                "value": None,
                "type": "datetime"
            },
            "claim_paid_date": {
                "value": None,
                "type": "datetime"
            },
        }

        self.raw_results = {
            "net_premium": None,
            "issue_date": None,
            "covernote_number": None,
            "policy_number": None,
            "claim_number": None,
            "customer_name": None,
            "risk_type": None,
            "event_type": None,
            "sum_insured": None,
            "premium_paid_amount": None,
            "claim_intimation_amount": None,
            "claim_paid_amount": None,
            "premium_paid_date": None,
            "claim_intimation_date": None,
            "claim_paid_date": None,
        }

        self.similarity_queries = {
            "event_type": "\n".join([
                    "event type can only belong to any one of the following"
                    "policy_issued", 
                    "premium_paid", 
                    "claim_intimated", 
                    "claim_paid",
                ]),
            "customer_name": "insured name?",
            "net_premium": "Net Premium / Premium Computation?",
            "issue_date": "Issue date / print date?",
            "sum_insured": "sum insured?"
        }

        self.systm_query_msgs = {
            "issue_date": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "for any date that is found, convert it into the following format: YYYY-MM-DD.",
                "If the date is found, use an '=' sign before the answer or amount or date."
            ]),
            "net_premium": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any net premium amount would appear along a list of other amounts"
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "If the answer or amount found, use an '=' sign before the answer or amount or date."
                "do not use the amount in the example provided in the query"
            ]),
            "covernote_number": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer is found, use an '=' sign before the answer."
            ]),
            "policy_number": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer is found, use an '=' sign before the answer."
            ]),
            "claim_number": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer is found, use an '=' sign before the answer."
            ]),
            "customer_name": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer is found, use an '=' sign before the answer.",
            ]),
            "risk_type": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer or amount or date is found, use an '=' sign before the answer or amount or date."
                "\n".join([
                    "Risk type can only belong to one of the following:",
                    "Fire Insurance",
                    "Homeowners Insurance",
                    "Commercial Property Insurance",
                    "Liability Insurance",
                    "Auto Insurance",
                    "Workers' Compensation Insurance",
                    "Term Life Insurance",
                    "Whole Life Insurance",
                    "Universal Life Insurance",
                    "Individual Health Insurance",
                    "Group Health Insurance",
                    "Medicare Supplement Insurance",
                    "Marine Insurance",
                    "Aviation Insurance",
                    "Cyber Insurance",
                    "Electronic Equipment Insurance",
                    "Fidelity Bonds",
                    "Surety Bonds",
                ]),
            ]),
            "event_type": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Any answer will be contained within the choices.",
                "If the answer or amount or date is found, use an '=' sign before the answer or amount or date."
                "\n".join([
                    "event type can only belong to any one of the following"
                    "policy_issued", 
                    "premium_paid", 
                    "claim_intimated", 
                    "claim_paid",
                ]),
            ]),
            "sum_insured": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "If the answer or amount found, use an '=' sign before the answer or amount or date."
            ]),
            "premium_paid_amount": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "If the answer or amount found, use an '=' sign before the answer or amount or date."
            ]),
            "premium_paid_date": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "for any date that is found, convert it into the following format: YYYY-MM-DD.",
                "If the date is found, use an '=' sign before the answer or amount or date."
            ]),
            "claim_intimation_amount": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "If the answer or amount found, use an '=' sign before the answer or amount or date."
            ]),
            "claim_intimation_date": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "for any date that is found, convert it into the following format: YYYY-MM-DD.",
                "If the date is found, use an '=' sign before the answer or amount or date."
            ]),
            "claim_paid_amount": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "Do not perform any mathematical operations on your own, all the data will be contained within the choices.",
                "If the answer or amount found, use an '=' sign before the answer or amount or date."
            ]),
            "claim_paid_date": "\n".join([
                "You are a helpful assistant that will help the user to figure out the answer to the related query given the content-data.",
                f"The content data will contain {self.num_of_choices} choices for the most relevant data, you have to use a combination of the choices to answer the query.",
                "The answer will be singular. use an '=' sign before the answer.",
                "If you cannot find the answer easily, say the following: '404 Not Found'.",
                "There should be only one '=' sign in the answer if it is found.",
                "for any date that is found, convert it into the following format: YYYY-MM-DD.",
                "If the date is found, use an '=' sign before the answer or amount or date."
            ]),
        }

        self.events_query_dict = {
            "policy_issued": {
                "policy_number": "policy_number",
                "issue_date": "issue_date",
                "net_premium": "net_premium",
                "customer_name": "customer_name",
                "risk_type": "risk_type",
                "sum_insured": "sum_insured"
            },
            "premium_paid": {
                "policy_number": "policy_number",
                "premium_paid_amount": "premium_paid_amount",
                "premium_paid_date": "premium_paid_date",
                "customer_name": "customer_name",
                "risk_type": "risk_type",
                "sum_insured": "sum_insured"
            },
            "claim_intimated": {
                "policy_number": "policy_number",
                "claim_intimation_amount": "claim_intimation_amount",
                "claim_intimation_date": "claim_intimation_date",
                "customer_name": "customer_name",
                "risk_type": "risk_type",
                "sum_insured": "sum_insured"
            },
            "claim_paid": {
                "policy_number": "policy_number",
                "claim_paid_amount": "claim_paid_amount",
                "claim_paid_date": "claim_paid_date",
                "claim_number": "claim_number",
                "customer_name": "customer_name",
                "risk_type": "risk_type",
                "sum_insured": "sum_insured"
            }
        }
        self.ai_query_msgs = {
            "net_premium": [
                "\n".join([
                    "An example of the premium contained is the following",
                    f"Premium Computation\nAmount(Rs) Premium Details Amount(Rs)\nMarine\nWAR & SRCC\nGROSS PREMIUM\nASC\nSUB TOTAL\nFIF\nSales Tax On Services/F.E.D.\nSTAMP DUTY\nNET PREMIUM             2,683.00\n1,825.00\n4,508.00\n225.00\n4,733.00\n47.00\n615.00\n274.00\n5,669.22222",
                    "This shows two columns one for labels and one for amounts. the last label is net premium which corresponds to the amount 5,669.00",
                    "this is just an example, the values and format will vary.",
                    "donot use the values of this message as your answer."
                ]),
                "\n".join([
                    "Another example of the premium contained is the following",
                    f"10,000\n10,000\n10,000\n10,000\n10,000\n10,000\n10,000\n70,000"
                    "This shows one column, the last row corresponds to the net premium amount = 70,000",
                    "this is just an example, the values and format will vary.",
                    "donot use the values of this message as your answer."
                ])
            ],
            # "customer_name": [
            #     "\n".join([
            #         "An example of the way the insured name can appear in the content is this:",
            #         f"Broker :ZZXXXXXXXXXX. of Days. : 365Insured :Z_INsued.",
            #         "The insured name appears right after the '365Insured' word",
            #         "this is just an example, the values and format will vary.",
            #         "donot use the values of this example as your answer."
            #     ]),
            # ],
            
        }
        self.doc_chunk_size = 500
        self.doc_chunk_overlap=100
        self.convo_chunk_size = 500
        self.convo_chunk_overlap=100
        self.document_query_results = {}
        self.convo_query_results = {}
        self.event_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.doc_label = None
        self.convo_label = None


    def format_string(input_string):
        import re
        
        # Replace \n with actual newlines
        formatted_string = input_string.replace("\\n", "\n")
        
        # Handle additional formatting rules if needed
        # Example: remove multiple spaces
        formatted_string = re.sub(r' +', ' ', formatted_string)
        
        # Example: clean up multiple newlines
        formatted_string = re.sub(r'\n+', '\n', formatted_string)
        
        return formatted_string
    
    def format_text(self, text):
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        formatted_text = '\n'.join(cleaned_lines)
        return formatted_text
    
    def store_documents_in_vector_store(self, file_paths):
        all_documents = []
        
        for path in file_paths:
            # Load PDF and split into documents
            loader = PyPDFLoader(path)
            raw_documents = loader.load()

            # Split documents into smaller chunks
            text_splitter = CharacterTextSplitter(chunk_size=self.doc_chunk_size, chunk_overlap=self.doc_chunk_overlap, separator="\n")
            documents = text_splitter.split_documents(raw_documents)
            for doc in documents:
                doc.page_content = self.format_text(doc.page_content)
            all_documents.extend(documents)

            # Debug: Print the number of documents and their lengths
            # print(f"Number of documents from {path}: {len(documents)}")
            # for i, doc in enumerate(documents):
            #     print(f"Document {i} length: {len(doc.page_content)}")
            #     print(f"Document {i} content: {doc.page_content[:200]}...")

        # Create FAISS index from all documents
        try:
            self.documents_vector_store = FAISS.from_documents(all_documents, self.embeddings_model)
            self.all_documents = all_documents
        except Exception as err:
            print(err)
            self.all_documents = []
    
    def label_documents(self):
        labeled_data = []
        for doc in self.all_documents:
            text = doc.page_content
            result = self.event_classifier(text, self.event_types)
            label = result['labels'][0]
            labeled_data.append(label)
        if labeled_data:
            self.doc_label = mode(labeled_data)
        

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
        self.texts_chunks = texts_chunks

    def label_texts(self):
        labeled_data = []
        for text in self.texts_chunks:
            result = self.event_classifier(text, self.event_types)
            label = result['labels'][0]
            labeled_data.append({'text': text, 'label': label})
        if labeled_data:
            self.convo_label = mode(labeled_data)
    
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
            qry = None
            similarity_query = self.similarity_queries.get(key, None)
            # similarity_query = None
            if similarity_query is not None:
                qry = similarity_query
            else:
                qry = query
            retrieved_docs = self.documents_vector_store.similarity_search(qry, k=self.num_of_choices)
            results[key] = [doc.page_content for doc in retrieved_docs] if retrieved_docs else ["Not found"]

        # Print the top three relevant chunks for each query
        self.document_query_results = {}
        for key, contents in results.items():
            self.document_query_results[key] = {}
            for i, content in enumerate(contents):
                self.document_query_results[key][f"Choice {i+1}"] = content

        # print(json.dumps(self.document_query_results, indent=4))
        # print("Number of tokens:", len(str(self.document_query_results).split()))

    def search_convo_vector_store(self):

        # Retrieve and print the top three relevant chunks for each query
        results = {}
        for key, query in self.queries.items():
            if key in self.convo_skip_keys:
                continue
            retrieved_chunks = self.convo_vector_store.similarity_search(query, k=self.num_of_choices)
            results[key] = [text_chunk.page_content for text_chunk in retrieved_chunks] if retrieved_chunks else ["Not found"]

        # Print the top three relevant chunks for each query
        self.convo_query_results = {}
        for key, contents in results.items():
            self.convo_query_results[key] = {}
            for i, content in enumerate(contents):
                self.convo_query_results[key][f"Choice {i+1}"] = content

        # print(json.dumps(self.convo_query_results, indent=4))
        # print("Number of tokens:", len(str(self.convo_query_results).split()))

    def format_similarity_search_results(self, similarity_search_results):
        formatted_results = {}
        for key, content in similarity_search_results.items():
            if isinstance(content, dict):
                formatted_sub_results = {}
                for sub_key, sub_content in content.items():
                    formatted_sub_results[sub_key] = self.format_text(sub_content)
                formatted_results[key] = formatted_sub_results
            else:
                formatted_results[key] = self.format_text(content)
        return formatted_results
    
    def query_from_final_results(self, similarity_search_results: dict):
        llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
        formatted_results = self.format_similarity_search_results(similarity_search_results)

        messages = [
            SystemMessage(content=self.systm_query_msgs["event_type"]),
            HumanMessage(content=f"query: {self.queries["event_type"]}, content: {formatted_results["event_type"]}"),
        ]
        if self.ai_query_msgs.get("event_type", None):
            for a_msg in self.ai_query_msgs["event_type"]:
                messages.append(AIMessage(content=a_msg))

        if self.event_type is None:
            response = llm(messages)
            if "404 N" not in response.content:
                for a_type in self.event_types:
                    if a_type in response.content:
                        self.event_type = a_type
        self.queries_results["event_type"]["value"] =  self.event_type
        for key, content in formatted_results.items():
            # print(key, self.queries_results[key]["value"], not self.queries_results[key]["value"])
                curr_val = self.queries_results[key]["value"]
            # if not curr_val or (type(curr_val) is str and "404 N" in curr_val):
                # Truncate content to fit within token limits
                if self.event_type is not None:
                    allowed_queries_keys = self.events_query_dict[self.event_type]
                    if key not in allowed_queries_keys:
                        continue
                else:
                    break

                messages = [
                    SystemMessage(content=self.systm_query_msgs[key]),
                    HumanMessage(content=f"query: {self.queries[key]}, content: {content}"),
                ]
                if self.ai_query_msgs.get(key, None):
                    for a_msg in self.ai_query_msgs[key]:
                        messages.append(AIMessage(content=a_msg))

                response = llm(messages)
                if "404 N" not in response.content and (
                    curr_val is None 
                    or (curr_val is not None and key not in self.convo_priority_keys)
                ):
                    self.raw_results[key] = response.content
                    self.queries_results[key]["value"] =  response.content
                # print(key, self.queries_results[key])

    def clean_query_results(self):
        for key, value_dict in self.queries_results.items():
            data_type = value_dict["type"]
            data_value = value_dict["value"]
            # value_dict["value"] = self.raw_results[key]
            # continue
            if data_value is not None and type(data_value) is str and "404 Not Found" not in data_value:
                # Clean the data value
                data_values = data_value.split("=")
                cleaned_value = data_values[-1].strip().replace("'", "")

                # Convert the cleaned data value to the specified type
                if data_type == "double":
                    try:
                        # Extract numbers from the string using regex
                        cleaned_value = cleaned_value.replace(',', '')
                        cleaned_value = cleaned_value.replace('.', '') 
                        cleaned_value = re.sub(r'[^\d.]', '', cleaned_value)
                        cleaned_value = float(cleaned_value)
                    except ValueError:
                        cleaned_value = None
                        raise Exception
                elif data_type == "datetime":
                    try:
                        # Extract date in the format YYYY-MM-DD using regex
                        match = re.search(r'\d{4}-\d{2}-\d{2}', cleaned_value)
                        if match:
                            cleaned_value = datetime.strptime(match.group(), "%Y-%m-%d")
                        else:
                            cleaned_value = None
                    except ValueError:
                        cleaned_value = None
                        raise Exception
                elif data_type == "string":
                    cleaned_value = str(cleaned_value)
                
                # Update the value in the dictionary
                value_dict["value"] = cleaned_value

    def record_data(self, file_paths: list[str]):
        DATABASE_URL = f'postgresql://{environ.get("POSTGRES_USER")}:{environ.get("POSTGRES_PASSWORD")}@{environ.get("DB_HOST")}:{environ.get("DB_PORT")}/{environ.get("POSTGRES_DB")}'

        engine = create_engine(DATABASE_URL)

        Session = sessionmaker(bind=engine)
        session = Session()
        net_premium = self.queries_results["net_premium"]["value"]
        issue_date = self.queries_results["issue_date"]["value"]
        covernote_number = self.queries_results["covernote_number"]["value"]
        policy_number = self.queries_results["policy_number"]["value"]
        claim_number = self.queries_results["claim_number"]["value"]
        customer_name = self.queries_results["customer_name"]["value"]
        risk_type = self.queries_results["risk_type"]["value"]
        event_type = self.queries_results["event_type"]["value"]
        sum_insured = self.queries_results["sum_insured"]["value"]
        premium_paid_amount = self.queries_results["premium_paid_amount"]["value"]
        claim_intimation_amount = self.queries_results["claim_intimation_amount"]["value"]
        claim_paid_amount = self.queries_results["claim_paid_amount"]["value"]
        premium_paid_date = self.queries_results["premium_paid_date"]["value"]
        claim_intimation_date = self.queries_results["claim_intimation_date"]["value"]
        claim_paid_date = self.queries_results["claim_paid_date"]["value"]
        
        existing_risk = None
        existing_policy = None
        existing_client = None
        existing_user = None
        existing_customer = None

        # self.event_type = "premium_paid"
        if customer_name is not None:
            existing_customer = Client.objects.filter(name=customer_name).first()
            if existing_customer is None:
                existing_customer = Client.objects.create(
                    name=customer_name
                )
        if self.event_type == 'policy_issued':
            if policy_number is not None:
                existing_policy = Policy.objects.filter(number=policy_number).first()
                if existing_policy is None:
                    existing_policy = Policy.objects.create(
                        issue_date=issue_date,
                        number=policy_number,
                        net_premium=net_premium,
                        client=existing_customer
                    )
                    existing_client = existing_customer
                else:
                    if existing_policy.issue_date is None and issue_date is not None:
                        existing_policy.issue_date = issue_date
                    if existing_policy.net_premium is None and net_premium:
                        existing_policy.net_premium = net_premium
                    if existing_policy.number is None and policy_number:
                        existing_policy.number = policy_number
                    if existing_policy.client is None and existing_customer is not None:
                        existing_policy.client = existing_customer
                    elif existing_policy.client is not None:
                        existing_client = existing_policy.client
                    existing_policy.save()
                    existing_risk = existing_policy.risk

                if existing_risk is None:
                    existing_risk = Risk.objects.create(
                        sum_insured=sum_insured,
                        type = risk_type,
                        client=existing_client
                    )
                else:
                    if sum_insured and existing_risk.sum_insured is None:
                        existing_risk.sum_insured = sum_insured
                    if risk_type and existing_risk.type is None:
                        existing_risk.type = risk_type
                    if existing_client is not None and existing_risk.client is None:
                        existing_risk.client = existing_client
                if existing_risk is not None:
                    existing_policy.risk = existing_risk
                    existing_policy.save()
                if existing_client is None:
                    existing_client = existing_customer
                if existing_client is not None:
                    existing_risk.client=existing_client
                    existing_policy.client=existing_client

                if existing_risk:
                    if existing_risk.client is None:
                        existing_risk.client = existing_client
                    existing_risk.save()
                if existing_policy:
                    if existing_policy.client is None:
                        existing_policy.client = existing_client
                    existing_policy.save()

                for file_path in file_paths:
                    final_path = file_path.replace("/Users/mirbilal/Desktop/minsir/media/", "")
                    name = final_path.replace("email_attachments/", "")
                    file = SQLPolicyFile(
                        policy_id=existing_policy.id,
                        name = name,
                        file = final_path
                    )
                    session.add(file)
                session.commit()

        if self.event_type == 'premium_paid':
            existing_premium_credited: PremiumCredited = None
            if policy_number is not None or (customer_name is not None and (net_premium is not None or premium_paid_amount is not None)):
                if policy_number:
                    existing_policy = Policy.objects.filter(number=policy_number).first()
                if not existing_policy and customer_name is not None and (net_premium is not None or premium_paid_amount is not None):
                    existing_policy = Policy.objects.filter(
                        (
                            Q(risk__client__name=customer_name)
                            |Q(client__name=customer_name)
                        )
                        &(
                            Q(net_premium=net_premium)
                            |Q(net_premium=premium_paid_amount)
                        )
                    ).first()

                if existing_policy:
                    existing_client = existing_policy.client
                    existing_risk = existing_policy.risk
                    if existing_client is None:
                        existing_client = existing_risk.client
                    existing_premium_credited = PremiumCredited.objects.filter(
                        Q(policy__number=existing_policy.number)
                        &Q(amount=premium_paid_amount)
                    ).first()
                if existing_client is None and existing_premium_credited is not None:
                    existing_client = existing_premium_credited.client
                if existing_client is None:
                    existing_client = existing_customer
                
                if existing_policy.client is None:
                    existing_policy.client = existing_client
                if existing_risk.client is None:
                    existing_risk.client = existing_client
                if existing_premium_credited is None:
                    existing_premium_credited = PremiumCredited.objects.create(
                        policy=existing_policy,
                        date=premium_paid_date,
                        amount=premium_paid_amount,
                        client=existing_client
                    )
                else:
                    if premium_paid_date is not None and existing_premium_credited.date is None:
                        existing_premium_credited.date = premium_paid_date
                    if existing_client is not None and existing_premium_credited.client is None:
                        existing_premium_credited.client = existing_client
                    existing_premium_credited.save()

                if existing_risk:
                    if existing_risk.client is None:
                        existing_risk.client = existing_client
                    existing_risk.save()
                if existing_policy:
                    if existing_policy.client is None:
                        existing_policy.client = existing_client
                    existing_policy.save()
                if existing_premium_credited:
                    if existing_premium_credited.client is None:
                        existing_premium_credited.client = existing_client
                    existing_premium_credited.save()
                
                for file_path in file_paths:
                    final_path = file_path.replace("/Users/mirbilal/Desktop/minsir/media/", "")
                    name = final_path.replace("email_attachments/", "")
                    file = SQLPremiumCreditedFile(
                        premium_credited_id=existing_premium_credited.id,
                        name = name,
                        file = final_path
                    )
                    session.add(file)
                session.commit()
        
        if self.event_type == 'claim_intimated':
            existing_claim_intimated: Claim = None
            if policy_number is not None or customer_name is not None:
                if policy_number:
                    existing_policy = Policy.objects.filter(number=policy_number).first()
                if existing_policy:
                    existing_risk = existing_policy.risk
                    existing_client = existing_policy.client
                if existing_client is None and existing_risk is not None and existing_risk.client is not None:
                        existing_client = existing_risk.client
                if existing_policy and claim_intimation_amount:
                    fltr_qry = Q(cash_call_amount=claim_intimation_amount)
                    if existing_client is not None:
                        fltr_qry = fltr_qry & (
                            (
                                Q(policy__number=policy_number)
                                &~Q(policy__number=None)
                            ) 
                            | Q(client_id=existing_client.id)
                        )
                    else:
                        fltr_qry = fltr_qry & (
                            Q(policy__number=policy_number)
                            &~Q(policy__number=None)
                        )
                    existing_claim_intimated = Claim.objects.filter(fltr_qry).first()
                    if existing_claim_intimated and existing_client is None:
                        existing_client = existing_claim_intimated.client
                if existing_claim_intimated is None:
                    existing_claim_intimated = Claim.objects.create(
                        policy=existing_policy,
                        date_of_intimation=claim_intimation_date,
                        cash_call_amount=claim_intimation_amount,
                        client=existing_client
                    )
                else:
                    if claim_intimation_date is not None and existing_claim_intimated.date_of_intimation is None:
                        existing_claim_intimated.date_of_intimation = claim_intimation_date
                    if claim_intimation_amount is not None and existing_claim_intimated.cash_call_amount is None:
                        existing_claim_intimated.cash_call_amount = claim_intimation_amount
                    if existing_client is not None and existing_claim_intimated.client is None:
                        existing_claim_intimated.client = existing_client
                    existing_claim_intimated.save()
                
                if existing_risk:
                    if existing_risk.client is None:
                        existing_risk.client = existing_client
                    existing_risk.save()
                if existing_policy:
                    if existing_policy.client is None:
                        existing_policy.client = existing_client
                    existing_policy.save()
                if existing_claim_intimated:
                    if existing_claim_intimated.client is None:
                        existing_claim_intimated.client = existing_client
                    existing_claim_intimated.save()

                for file_path in file_paths:
                    final_path = file_path.replace("/Users/mirbilal/Desktop/minsir/media/", "")
                    name = final_path.replace("email_attachments/", "")
                    file = SQLClaimDocument(
                        claim_id=existing_claim_intimated.id,
                        name = name,
                        file = final_path
                    )
                    session.add(file)
                session.commit()

        if self.event_type == 'claim_paid':
            existing_claim_paid: ClaimDebited = None
            existing_claim = None
            if policy_number is not None or customer_name is not None:
                if policy_number:
                    existing_policy = Policy.objects.filter(number=policy_number).first()
                if existing_policy:
                    existing_client = existing_policy.client
                    existing_risk = existing_policy.risk
                    if existing_risk and existing_client is None:
                        existing_client = existing_risk.client
                    if claim_paid_amount is not None:
                        existing_claim = Claim.objects.filter(
                            Q(policy__number=existing_policy.number)
                            &Q(cash_call_amount__gte=claim_paid_amount)
                        ).first()
                        if existing_claim:
                            existing_claim.settlement_amount = claim_paid_amount
                    if existing_claim and existing_client is None:
                        existing_client = existing_claim.client

                if existing_claim and claim_paid_amount:
                    existing_claim_paid = ClaimDebited.objects.filter(
                        Q(claim_id=existing_claim.id)
                        &Q(amount=claim_paid_amount)
                    )
                    if existing_claim_paid and existing_client is None:
                        existing_client = existing_claim_paid.client
                if existing_client is None:
                    existing_client = existing_customer
                if existing_claim_paid is None:
                    existing_claim_paid = ClaimDebited.objects.create(
                        claim=existing_claim,
                        date=claim_paid_date,
                        amount=claim_paid_amount,
                        client=existing_client
                    )
                else:
                    if claim_paid_date is not None and existing_claim_paid.date is None:
                        existing_claim_paid.date = claim_paid_date
                    if claim_paid_amount is not None and existing_claim_paid.amount is None:
                        existing_claim_paid.amount = claim_paid_amount
                    if existing_client is not None and existing_claim_paid.client is None:
                        existing_claim_paid.client = existing_client
                    existing_claim_paid.save()

                if existing_risk:
                    if existing_risk.client is None:
                        existing_risk.client = existing_client
                    existing_risk.save()
                if existing_policy:
                    if existing_policy.client is None:
                        existing_policy.client = existing_client
                    existing_policy.save()
                if existing_claim:
                    if existing_claim.client is None:
                        existing_claim.client = existing_client
                    existing_claim.save()
                if existing_claim:
                    if existing_claim.client is None:
                        existing_claim.client = existing_client
                    existing_claim.save()
                if existing_claim_paid:
                    if existing_claim_paid.client is None:
                        existing_claim_paid.client = existing_client
                    existing_claim_paid.save()

                for file_path in file_paths:
                    final_path = file_path.replace("/Users/mirbilal/Desktop/minsir/media/", "")
                    name = final_path.replace("email_attachments/", "")
                    file = SQLClaimDebitedFile(
                        claim_debited_id=existing_claim_paid.id,
                        name = name,
                        file = final_path
                    )
                    session.add(file)
                session.commit()
                


