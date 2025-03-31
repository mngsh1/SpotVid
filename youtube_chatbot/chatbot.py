from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from .database import get_db_url, pgvector_query

class VideoChatBot:
    def __init__(self):
        load_dotenv()
        openai = os.getenv("OPENAI_API_KEY")
        if not openai:
            openai = input("OPENAI_API_KEY is missing. Please enter your API key: ").strip()
            os.environ["OPENAI_API_KEY"] = openai  # Set the key for the session

        self.embeddings = OpenAIEmbeddings(
            # model="text-embedding-3-large"
        )
        self.db_type = os.getenv("DB_TYPE", "ChromaDB")  # Default to ChromaDB
        self.db_connection:str = get_db_url()  # Default to ChromaDB
        self.llm = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo")

        if self.db_type == "ChromaDB":
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory="./chroma_db"
            )
    def query(self, question):
        if self.db_type == "pgvector":
            print('Using pgvector for similarity search')
            docs = pgvector_query(embeddings=self.embeddings, question= question)
        else:
            print('Using ChromaDB for similarity search')
            docs = self.vectorstore.similarity_search(question, k=3)

        results = []
        for doc in docs:
            metadata = doc.get('metadata',None)
            if not metadata:
                continue
            results.append({
                'title': metadata['title'],
                'url': metadata['url'],
                'start': metadata['start'],
                'end': metadata['end'],
                'summary': metadata['summary'],
            })
        # Provide reference of video and timeline if applicable hyperlinked with url
        context = "\n".join([f"Video: {r['title']}\nSummary: {r['summary']}\n Video Time: start:{r['start']} end: {r['end']}\n Video snipped url: {r['url']}" for r in results])
        prompt = f"""
         <<Instructions>>
        - Answer the question based strictly on the following context. 
        - Do not include any information outside of this context.
        - Answer in a helpful and concise manner. Use bullets for multi-point answers. 
        - [MUST]  If question is not discussed in below <<context>> then add this string <<TOPIC_NOT_FOUND>> at the end.
        <<Instructions>>
         
        <<context>> 
        Context: {context}
        <<context>>
        
        <<User's Question>>
        Question: {question}
        <<User's Question>> 
        """
        # print(f"Prompt: {prompt}")

        response = self.llm.invoke(prompt)
        return {
            'answer': response,
            'references': results
        }
