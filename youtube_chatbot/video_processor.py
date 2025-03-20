from langchain.chains.summarize import load_summarize_chain
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from youtube_transcript_api import YouTubeTranscriptApi

from .config_templates import CHUNK_SUMMARY_TEMPLATE
from .data_fetcher import get_video_details
from .database import Session, Video
from .utility import append_response_to_json, merge_transcript_text, split_text_with_metadata, get_video_by_id_from_db


def process_video(video_id):

    if get_video_by_id_from_db(video_id):
        print('Video is already processed')
        return
    details = get_video_details(video_id)
    print(f"Processing video Id: {details['video_id']} title: {details['title']} duration: {details['length']}")
    append_response_to_json(details, filename=f'{video_id}-video-detail-short.json')

    # Temp comment to read from file to avoid consume quota
    # details = read_json_file('/Users/mchimankar/PycharmProjects/youtube-chatbot-project/temp-folder/EmyqOyCXnt0
    # -video-details.json')
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        append_response_to_json(transcript, f'{video_id}-transcript.json')

        full_text = ' '.join([t['text'] for t in transcript])
        print(f"transcript: {transcript}")
        # Step 1: Merge transcript into a single text block
        full_text, segment_map = merge_transcript_text(transcript)

        # Step 2: Split using LangChain's optimized text splitter
        chunked_transcript = split_text_with_metadata(full_text, segment_map, chunk_size=500, overlap=50)
        append_response_to_json(chunked_transcript, f'{video_id}-chunked_transcript.json')
    except Exception as e:
        print(f"Error getting transcript for {video_id}: {e}")
        return False

    llm = ChatOpenAI(temperature=0.1, model_name="gpt-3.5-turbo")  # gpt-3.5-turbo-instruct
    embeddings = OpenAIEmbeddings()

    # Step 3: Generate full video summary
    summary_chain = load_summarize_chain(llm, chain_type="map_reduce")
    docs = [Document(page_content=full_text)]
    summary = summary_chain.run(docs)

    session = Session()
    try:
        video = Video(
            id=video_id,
            title=details['title'],
            length=int(details['length']),
            summary=summary,
            embedding=str(embeddings.embed_query(summary))
        )
        session.merge(video)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()

    print(f'chunks to process: {len(chunked_transcript)}')
    # Step 4: Process chunked transcript
    # Store chunks in vector DB
    for i, chunk in enumerate(chunked_transcript):
        start_time = chunk['start']
        end_time = start_time + chunk['duration']

        prompt = ChatPromptTemplate.from_template(CHUNK_SUMMARY_TEMPLATE)
        chain = prompt | ChatOpenAI() | StrOutputParser()
        chunk_summary = chain.invoke(chunk["text"])
        print(f'{i} --> {start_time}-{end_time} summary: {chunk_summary}')

        metadata = {
            'title': details['title'],
            'summary': chunk_summary,
            'start': start_time,
            'end': end_time,
            'video_id': video_id,
            'url': f"https://youtu.be/{video_id}?t={int(start_time)}"
        }
        doc = Document(page_content=chunk["text"], metadata=metadata)

        Chroma.from_documents(
            documents=[doc],
            embedding=embeddings,
            ids=[f"{video_id}_{i}"],
            persist_directory="./chroma_db"
        )

    return True
