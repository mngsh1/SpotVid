from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(String, primary_key=True)
    title = Column(String)
    length = Column(Integer)
    summary = Column(Text)
    embedding = Column(Text)

    def print_details(self):
        print(f"Video ID: {self.id}")
        print(f"Title: {self.title}")
        print(f"Length: {self.length} seconds")
        print(f"Summary: {self.summary}")
        print(f"Embedding: {self.embedding[:30]}...")

engine = create_engine('sqlite:///videos.db')
Session = sessionmaker(bind=engine)
