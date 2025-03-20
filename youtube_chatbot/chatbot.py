from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os


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
        self.vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )
        self.llm = ChatOpenAI(temperature=0.1)

    def query(self, question):
        docs = self.vectorstore.similarity_search(question, k=3)

        results = []
        for doc in docs:
            metadata = doc.metadata
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
        prompt = f"""Answer the question based on this context:
        {context}

        Question: {question}
        Answer in a helpful and concise manner, user bullets for multi point answers. 
        """
        # print(f"Prompt: {prompt}")

        response = self.llm.invoke(prompt)
        return {
            'answer': response,
            'references': results
        }
