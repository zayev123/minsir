from datetime import datetime
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import os
from langchain_community.chat_models import ChatOpenAI
from typing import List, Dict
from langchain.schema import HumanMessage, SystemMessage
from apps.email_manager.service_layer.email_linker import ConversationReader
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent

class InsuranceChatbot:
    def __init__(self):
        model_name = 'sentence-transformers/paraphrase-mpnet-base-v2'
        self.embeddings_model = SentenceTransformer(model_name)
        self.es = Elasticsearch("http://localhost:9200") # Connect to your Elasticsearch instance
        self.doc_index_name = 'document_embeddings'
        self.attachments_dir = "/Users/mirbilal/Desktop/minsir/media/email_attachments/"
        self.doc_chunk_size = 500
        self.doc_chunk_overlap = 100
        self.convo_index_name = 'conversation_embeddings'
        self.convo_chunk_size = 500  # Adjust as needed
        self.convo_chunk_overlap = 100  # Adjust as needed
        self.formatted_convos = []
        self.openai_llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0)
        self.agent_executor = None
        self.memory = None
        self.tool = None

        # Ensure index is created in Elasticsearch
        if not self.es.indices.exists(index=self.doc_index_name):
            self.create_index()

    def create_doc_index(self):
        # Define Elasticsearch index settings for k-NN search
        index_settings = {
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "page_content": {"type": "text"},
                    "embedding": {"type": "dense_vector", "dims": 768}  # Embedding dimension
                }
            }
        }
        self.es.indices.create(index=self.doc_index_name, body=index_settings)

    def create_convo_index(self):
        # Define Elasticsearch index settings and mappings for conversations
        index_mappings = {
            "mappings": {
                "properties": {
                    "convo_metadata": {
                        "type": "nested",  # Use nested for each email in the conversation
                        "properties": {
                            "from": {"type": "keyword"},
                            "to": {"type": "keyword"},
                            "date": {"type": "date"},
                            "subject": {"type": "text"},
                            "attachment_file_paths": {}
                        }
                    },
                    "attachment_file_paths": {"type": "keyword"},
                    "text_chunk": {"type": "text"},
                    "embedding": {"type": "dense_vector", "dims": 768}  # Embedding dimension
                }
            }
        }

        # Create the index if it does not exist
        if not self.es.indices.exists(index=self.convo_index_name):
            self.es.indices.create(index=self.convo_index_name, body=index_mappings)
            print(f"Index '{self.convo_index_name}' created successfully.")
        else:
            print(f"Index '{self.convo_index_name}' already exists.")

    def format_text(self, text):
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        formatted_text = '\n'.join(cleaned_lines)
        return formatted_text

    def store_documents_in_elasticsearch(self):
        file_paths = [os.path.join(self.attachments_dir, file) for file in os.listdir(self.attachments_dir) if file.endswith('.pdf')]

        if not file_paths:
            print("No PDF files found in the attachments directory.")
            return

        actions = []
        batch_size = 50
        count = 0  # Keep track of how many documents have been processed

        for path in file_paths:
            loader = PyPDFLoader(path)
            raw_documents = loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=self.doc_chunk_size, chunk_overlap=self.doc_chunk_overlap, separator="\n")
            documents = text_splitter.split_documents(raw_documents)

            for i, doc in enumerate(documents, start=1):
                doc_id = f"{path}+{i}"
                doc.metadata = {"doc_id": doc_id, "source": path}
                doc.page_content = self.format_text(doc.page_content)

                # Generate document embeddings
                embedding = self.embeddings_model.encode(doc.page_content)

                # Prepare data for Elasticsearch bulk insert
                action = {
                    "_index": self.doc_index_name,
                    "_source": {
                        "doc_id": doc_id,
                        "source": path,
                        "page_content": doc.page_content,
                        "embedding": embedding.tolist()  # Elasticsearch expects lists, not numpy arrays
                    }
                }
                actions.append(action)
                count += 1

                # If we have reached the batch size, insert the current batch and reset
                if count % batch_size == 0:
                    bulk(self.es, actions)
                    print(f" count: {count} Indexed {len(actions)} document chunks in Elasticsearch.")
                    actions = []  # Clear the actions for the next batch

        # Insert any remaining documents if they don't fill up a full batch
        if actions:
            bulk(self.es, actions)
            print(f"Indexed the remaining {len(actions)} document chunks in Elasticsearch.")

    def retrieve_and_format_conversations(self):
        convo_reader = ConversationReader(
            start_date=datetime(year=2024, month=7, day=10),
            end_date=datetime(year=2024, month=7, day=11),
        )
        convo_reader.extract_conversation()
        convos = []
        for a_convo_str, a_convo_data in convo_reader.conversations.items():
            # if 'Surveyor Appointed for Ticket No:' in a_convo_str:
                (full_convo, attachments_file_paths, all_files) = a_convo_data.get_full_convo()
                convos.append({
                        "convo": full_convo,
                        "attachment_file_paths": attachments_file_paths
                })
        self.formatted_convos = convos
    
    def store_conversations_in_elastic_search(self):
        # Extract conversations from the reader
        convos = []
        count = 0 
        batch_size = 50

        for a_convo_data in self.formatted_convos:

            # Each email in the conversation has fields: from, to, date, subject, and body
            emails = a_convo_data['convo']
            convo_metadata = emails  # Store the metadata for the whole conversation

            # Combine the body texts for chunking
            full_convo_text = ' '.join([str(email) for email in emails])
            attachments_file_paths = a_convo_data["attachment_file_paths"]

            emails_from = [email.get("from", "") for email in emails]
            emails_to = [to_email for email in emails for to_email in email.get("to", [])]
            prtcpnts = emails_from + emails_to
            convo_prtcpnts = list(set(prtcpnts))
            convo_participants = "=====".join(str(ptcpnt) for ptcpnt in convo_prtcpnts)

            sbjcts = [email.get("subject", "") for email in emails]
            subjcts = list(set(sbjcts))
            convo_sbjcts = "=====".join(str(sbjects) for sbjects in subjcts)
            print(subjcts)

            # Split the full conversation text into chunks
            text_splitter = CharacterTextSplitter(chunk_size=self.convo_chunk_size, chunk_overlap=self.convo_chunk_overlap, separator=" ")
            text_chunks = text_splitter.split_text(full_convo_text)

            # Generate embeddings and create documents for each chunk
            for chunk_id, chunk_text in enumerate(text_chunks, start=1):
                # Generate embedding for each chunk
                chunk_text = f"Conversation Participants: {convo_participants}.\n" + f"Email Subjects: {convo_sbjcts}.\n" + chunk_text
                embedding = self.embeddings_model.encode(chunk_text).tolist()

                # Prepare document for Elasticsearch
                action = {
                    "_index": self.convo_index_name,
                    "_source": {
                        "convo_metadata": convo_metadata,  # Store metadata for the whole conversation
                        "attachment_file_paths": attachments_file_paths,  # Store attachment file paths
                        "text_chunk": chunk_text,  # The text chunk
                        "embedding": embedding  # Embedding for the chunk
                    }
                }
                convos.append(action)
                count += 1

                # If we have reached the batch size, insert the current batch and reset
                if count % batch_size == 0:
                    bulk(self.es, convos)
                    print(f" count: {count} Indexed {len(convos)} document chunks in Elasticsearch.")
                    convos = []  # Clear the actions for the next batch

        # Bulk insert all conversation chunks into Elasticsearch
        if convos:
            bulk(self.es, convos)
            print(f"Indexed {len(convos)} conversation chunks in Elasticsearch.")

    def retrieve_document_by_doc_id(self, doc_id):
        query = {
            "query": {
                "term": {
                    "doc_id": doc_id
                }
            }
        }

        # Search Elasticsearch by doc_id
        response = self.es.search(index=self.doc_index_name, body=query)

        if response['hits']['hits']:
            return response['hits']['hits'][0]['_source']['page_content']
        else:
            print(f"Document with id {doc_id} not found.")
            return None

    def query_documents(self, query_text):
        # Generate embeddings for the query text and normalize
        query_embedding = self.embeddings_model.encode(query_text)

        # Cosine similarity approximation using script_score
        cosine_similarity_query = {
            "size": 50,  # Number of nearest neighbors to retrieve
            "query": {
                "script_score": {
                    "query": {"match_all": {}},  # Search all documents
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",  # Add 1.0 to avoid negative scores
                        "params": {
                            "query_vector": query_embedding.tolist()
                        }
                    }
                }
            }
        }

        response = self.es.search(index=self.doc_index_name, body=cosine_similarity_query)

        if response['hits']['hits']:
            return [hit['_source']['page_content'] for hit in response['hits']['hits']]
        else:
            print("No similar documents found.")
            return None
        
    def query_conversations(self, query_text):
        # Step 1: Generate embeddings for the query text and normalize
        query_embedding = self.embeddings_model.encode(query_text)

        # Step 2: Cosine similarity query for conversation retrieval
        cosine_similarity_query = {
            "size": 5,  # Number of nearest neighbors to retrieve
            "query": {
                "script_score": {
                    "query": {"match_all": {}},  # Search all documents
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",  # Add 1.0 to avoid negative scores
                        "params": {
                            "query_vector": query_embedding.tolist()
                        }
                    }
                }
            }
        }

        # Step 3: Search in the conversations index
        response = self.es.search(index=self.convo_index_name, body=cosine_similarity_query)

        if response['hits']['hits']:
            enriched_conversations = []

            # Step 4: For each hit (conversation), collect the conversation and attachment paths
            for hit in response['hits']['hits']:
                convo_metadata = hit['_source']['convo_metadata']
                attachment_file_paths = hit['_source']['attachment_file_paths']
                
                # Step 5: Retrieve the page content for each attachment file path
                page_contents = []
                if attachment_file_paths:
                    page_contents = self.get_page_contents_for_attachments(attachment_file_paths)

                # Step 6: Enrich the conversation with the attachment page contents
                enriched_conversations.append({
                    "convo": convo_metadata,
                    "attachment_file_paths": attachment_file_paths,
                    "attachment_page_contents": page_contents  # Adding the page contents for each attachment
                })

            return enriched_conversations
        else:
            print("No similar documents found.")
            return None

    def get_page_contents_for_attachments(self, attachment_file_paths):
        # This function will query the document_embeddings index for each attachment file path
        page_contents = []
        
        for file_path in attachment_file_paths:
            # Step 1: Query to match the 'source' field with the file_path
            query = {
                "size": 10,  # We only need the matching document
                "query": {
                    "term": {
                        "source": file_path  # Exact match on the 'source' field
                    }
                }
            }

            # Step 2: Search in the document_embeddings index
            response = self.es.search(index="document_embeddings", body=query)

            # Step 3: Extract the page content from the matching document, if it exists
            doc_data = response['hits']['hits']
            if doc_data:
                for data in doc_data:
                    page_content = data['_source']['page_content']
                    page_contents.append(page_content)
            else:
                page_contents.append(None)  # If no content found for the file path

        return page_contents
    
    def create_candidates_list(self, query_text: str) -> List[Dict]:
        resp = self.query_conversations(query_text=query_text)
        return resp
    
    def send_to_openai(self, email_data: List[Dict], query_text: str) -> str:

        prompt_template = """
        Find the answer to this query:
        Query: {query}
        Based on the following email content:
        Email Content: {email_content}
        
        Respond with a detailed analysis.
        """
        
        combined_content = "\n\n".join(
            f"From: {email['from']}, To: {email['to']}, Date: {email['date']}, Subject: {email['subject']}, Body: {email['body']}"
            for candidate in email_data
            for email in candidate['convo']
        )
        
        formatted_prompt = prompt_template.format(
            query=query_text,
            email_content=combined_content
        )
        
        # Send the formatted prompt as a HumanMessage object
        response = self.openai_llm(
            messages=[
                HumanMessage(content=formatted_prompt),
                SystemMessage(
                    content="""
                    You are a helpful assistant will look at the emails to and from clients and give possible responses and explanations.
                    If you can not find the answer from the searched emails, then say that you do not know.
                    You will mention To whom and from whom the communication took place, and answer the query from the subject, the body, and the attachments of the communication.
                    If asked about a certain person, then look at the names in the subject, the body, and the attachments, but also look at the emails and their domains i.e axy@domain.com.
                    If you can not find the answer from the searched emails, then say that you do not know.
                    """
                ),
            ]
        )
        
        return response.content
    

    def query_from_data_source(self, query):
        candidates = self.create_candidates_list(query_text=query)
        result = self.send_to_openai(email_data=candidates, query_text=query)
        result = result + f"reference data: {candidates}"
        return result
    
    def create_convo_agent(self):
        self.tool = Tool.from_function(
            func=self.query_from_data_source,
            name="search_emails",
            description="useful for when you need to search for new data inside the emails if you cannot find any answer yourself from the existing context"
        )

        self.memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key="output"
        )

        self.agent_executor = create_conversational_retrieval_agent(
            llm=self.openai_llm,
            tools=[self.tool],  # Our custom retrieval tool
            memory_key='chat_history',  # Conversational memory to hold chat history
            verbose=True
        )