import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, Text, desc
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from pgvector.sqlalchemy import Vector

# Define the database models
Base = declarative_base()
# Set up the database engine and session only for pgvector
load_dotenv()
DB_TYPE = os.getenv("DB_TYPE", "pgvector")  # Set to "pgvector" or "chroma"
database_url = None
session:Session
def connect_db():
    global session, database_url
    database_url = os.getenv("DATABASE_URL")
    # Update with actual URL chromaDB it should be sqllite and pgvector its postgres

    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if not database_url:
        raise ValueError("DATABASE_URL is missing. Please provide the PostgreSQL connection string.")

    # Create an SQLAlchemy engine using the DATABASE_URL
    engine = create_engine(database_url)
    session_local = sessionmaker(bind=engine)
    session = session_local()

if DB_TYPE in ('pgvector', 'sqlite'):
    connect_db()


# Video model for storing complete video summary
class Video(Base):
    __tablename__ = 'videos'
    video_id = Column(Text, primary_key=True)
    title = Column(Text)
    length = Column(Integer)
    summary = Column(Text)
    embedding =Column(Vector(1536))

    def print_details(self):
        print(f"Video ID: {self.video_id}")
        print(f"Title: {self.title}")
        print(f"Length: {self.length} seconds")
        print(f"Summary: {self.summary}")
        print(f"Embedding: {self.embedding[:30]}...")


# VideoChunk model for storing chunk data
class VideoChunk(Base):
    __tablename__ = 'video_chunks'
    video_id = Column(Text, primary_key=True)
    title = Column(Text)
    video_chunk_id = Column(Text, primary_key=True)
    summary = Column(Text)
    embedding = Column(Vector(1536))
    start_time = Column(Integer)
    end_time = Column(Integer)
    url = Column(Text)

    def print_details(self):
        print(f"Video ID: {self.video_id}")
        print(f"Video Chunk ID: {self.video_chunk_id}")
        print(f"Title: {self.title}")
        print(f"Start Time: {self.start_time}s")
        print(f"End Time: {self.end_time}s")
        print(f"Summary: {self.summary}")
        print(f"Embedding: {self.embedding[:30]}...")


# Function to store data into ChromaDB or PostgresSQL (pgvector)
def store_to_db(**kwargs):
    if DB_TYPE == "pgvector":
        # Step 1: Store to relational DB with Vector enabled
        store_to_relational_database(**kwargs)
    elif DB_TYPE == "chromaDB":
        # Step 1: Store to Chroma DB
        store_to_chroma(**kwargs)
        #Step 2: Store to relational DB
        store_to_relational_database(**kwargs)
    else:
        print("Unsupported DB_TYPE!")


# Function to store video or chunk data into ChromaDB
def store_to_chroma(**kwargs):
    # Get the args
    video_id = kwargs.get("video_id")
    title = kwargs.get("title")
    summary = kwargs.get("summary")
    chunk_id = kwargs.get("chunk_id", None)
    start_time = kwargs.get("start_time", None)
    end_time = kwargs.get("end_time", None)
    url = kwargs.get("url", None)

    embeddings = OpenAIEmbeddings()

    metadata = {
        "title": title,
        "summary": summary,
        "video_id": video_id,
    }

    # If it's a chunk, add chunk-specific metadata
    if chunk_id:
        metadata.update({
            "video_chunk_id": chunk_id,
            "start_time": start_time,
            "end_time": end_time,
            "url": url
        })

    # Create the document
    doc = Document(page_content=summary, metadata=metadata)

    # Store the document in ChromaDB
    Chroma.from_documents(
        documents=[doc],
        embedding=embeddings,
        ids=[f"{video_id}_{chunk_id}" if chunk_id else video_id],
        persist_directory="./chroma_db"
    )

    # Print details
    print(f"Stored to ChromaDB for Video ID: {video_id}")
    if chunk_id:
        print(f"Chunk ID: {chunk_id}, Start: {start_time}s, End: {end_time}s")
    else:
        print(f"Video Summary: {summary[:100]}...")


# Function to store video or chunk data into PostgreSQL (pgvector)
def store_to_relational_database(**kwargs):
    try:
        video_id = kwargs.get("video_id")
        title = kwargs.get("title")
        length = kwargs.get("length", 0)  # Default to 0 if length is not provided
        summary = kwargs.get("summary")
        embedding_vector = kwargs.get("embedding_vector")
        chunk_id = kwargs.get("chunk_id", None)
        start_time = kwargs.get("start_time", None)
        end_time = kwargs.get("end_time", None)
        url = kwargs.get("url", None)

        if chunk_id is None:
            # Storing video data
            video = Video(
                video_id=video_id,
                title=title,
                length=length,
                summary=summary,
                embedding=embedding_vector  # Store the vector embedding
            )
            session.merge(video)
        else:
            # Storing chunk data
            chunk = VideoChunk(
                video_id=video_id,
                title=title,
                video_chunk_id=chunk_id,
                summary=summary,
                embedding=embedding_vector,  # Store the vector embedding
                start_time=start_time,
                end_time=end_time,
                url=url
            )
            session.merge(chunk)

        session.commit()

        # Print details
        print(f"Stored to PostgresSQL (pgvector) for Video ID: {video_id}")
        if chunk_id:
            print(f"Chunk ID: {chunk_id}, Start: {start_time}s, End: {end_time}s")
        else:
            print(f"Video Summary: {summary[:100]}...")

    except Exception as e:
        if session:
            session.rollback()
        print(f"Database error: {e}")
    finally:
        if session:
            session.close()

# Function to retrieve video or chunk data by video_id from ChromaDB or PostgresSQL (pgvector) or sqlite
def retrieve_from_db(video_id, chunk_id=None):
    if DB_TYPE in ("pgvector","chromaDB"):
        return retrieve_from_relational_database(video_id, chunk_id)
    else:
        print("Unsupported DB_TYPE!")
        return None
# Function to retrieve video or chunk data from PostgresSQL (pgvector) or sqlite
def retrieve_from_relational_database(video_id, chunk_id=None):
    try:
        if chunk_id is None:
            # Retrieve video data
            video = (
                session
                    .query(Video)
                    .filter(Video.video_id == video_id)
                    .first()
            )
            if video:
                print(f"Retrieved from PostgresSQL (pgvector) for Video ID: {video_id}")
                print(f"Title: {video.title}")
                print(f"Summary: {video.summary}")
                return video
            else:
                print(f"No video found in PostgresSQL (pgvector) for Video ID: {video_id}")
                return None
        else:
            # Retrieve chunk data
            chunk = (
                session
                    .query(VideoChunk)
                    .filter(VideoChunk.video_id == video_id,
                            VideoChunk.video_chunk_id == chunk_id)
                    .first()
            )
            if chunk:
                print(f"Retrieved from PostgresSQL (pgvector) for Video ID: {video_id}, Chunk ID: {chunk_id}")
                print(f"Start Time: {chunk.start_time}s, End Time: {chunk.end_time}s")
                print(f"Summary: {chunk.summary}")
                return chunk
            else:
                print(f"No chunk found in PostgreSQL (pgvector) for Video ID: {video_id}, Chunk ID: {chunk_id}")
                return None
    except Exception as e:
        print(f"Database error: {e}")
        raise e
    finally:
        if session:
            session.close()

def pgvector_query(embeddings:OpenAIEmbeddings, question, video_id = None, threshold = .5):
    # Assuming the vector search using pgvector is done using cosine similarity
    # query_embedding = embeddings.embed_query(question)
    # Get embedding for the query
    query_embedding = embeddings.embed_query(question)
    # # Convert NumPy array to Python list (pgvector uses arrays, not bytearrays)
    # query_vector = query_embedding.tolist()

    # Build query with optional video_id filter
    query = session.query(VideoChunk, VideoChunk.embedding.cosine_distance(query_embedding).label("distance"))
    if video_id:
        query = query.filter(VideoChunk.video_id == video_id)
    if threshold:
        query = query.filter(VideoChunk.embedding.cosine_distance(query_embedding) < threshold)

    query = query.order_by(VideoChunk.embedding.cosine_distance(query_embedding))
    query = query.limit(3)
    print('Query:',str(query))

    # Execute query, limit to top 3 results
    results = query.all()
    # Format the output
    docs = [{
        'metadata': {
            'video_id': row.video_id,
            'title': row.title,
            'url': row.url,
            'start': row.start_time,
            'end': row.end_time,
            'summary': row.summary,
        }
    } for row,distance in results]

    for row,distance in results:
        print(f'distance: {distance}')
        print(row.print_details())

    return docs

def get_db_url():
    return database_url