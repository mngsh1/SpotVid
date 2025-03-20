import requests
import os
from .database import Session, Video
from chromadb import PersistentClient
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter


def append_response_to_json(response, filename='data.json', append=False, directory='temp-folder'):
    """
    Appends or writes JSON response data to a file, ensuring the directory exists.

    Args:
        response (dict or list): The JSON-compatible data to store.
        filename (str): The name of the JSON file.
        append (bool): Whether to append data to an existing file.
        directory (str): The directory where the file is stored.
    """
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)

    complete_path = os.path.join(directory, filename)

    try:
        if append and os.path.exists(complete_path):
            try:
                with open(complete_path, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]  # Ensure it's a list
            except json.JSONDecodeError:
                existing_data = []

            existing_data.append(response)  # Append new data
        else:
            existing_data = response  # Overwrite with new data

        # Write updated data back to file
        with open(complete_path, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4)

        print(f"Data successfully written to {complete_path}")

    except Exception as e:
        print(f"Error handling JSON file: {e}")


def read_json_file(file_path):
    """
    Read and parse a JSON file.

    Args:
        file_path (str): Path to the JSON file

    Returns:
        dict/list: Parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return find_json_error(content)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        raise

    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")
        raise


def find_json_error(json_str):
    """
    Attempts to locate where the JSON parsing fails
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Get the line where error occurred
        lines = json_str.split('\n')
        line_no = e.lineno - 1  # JSON decoder line numbers are 1-based
        print(f"Error on line {e.lineno}: {lines[line_no]}")
        print(f"Position in line: {e.colno}")
        print(f"Error message: {e.msg}")

        # Show the problematic line with a pointer
        print(lines[line_no])
        print(" " * (e.colno - 1) + "^")


def fix_json_quotes(json_str):
    """
    Convert single quotes to double quotes in a JSON string.
    Also handles nested quotes properly.
    """
    return json_str.replace("'", '"')


def read_complete_table():
    con = Session()
    try:
        videos =con.query(Video).all()
        for video in videos:
            video.print_details()  # Call the print_details method for each video
    finally:
        con.close()

def read_chroma_db():
    # Connect to the database
    client = PersistentClient(path="./chroma_db")

    # List all collections
    collections = client.list_collections()
    print("Collections in ChromaDB:", collections)
    for col_name in collections:
        collection = client.get_collection(col_name)
        print(collection.get())  # Retrieves all stored documents


def merge_transcript_text(transcript):
    """Merge transcript into a single text block while preserving metadata mapping."""
    merged_text = ""
    segment_map = []

    for segment in transcript:
        start_idx = len(merged_text)
        merged_text += segment["text"] + " "
        end_idx = len(merged_text)
        segment_map.append(
            {"start": segment["start"], "duration": segment["duration"], "start_idx": start_idx, "end_idx": end_idx})

    return merged_text.strip(), segment_map


def split_text_with_metadata(text, segment_map, chunk_size=500, overlap=50):
    """Use LangChain's text splitter while mapping to original timestamps."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(text)

    split_segments = []
    for chunk in chunks:
        start_idx = text.find(chunk)
        start_time, duration = None, 0

        for segment in segment_map:
            if segment["start_idx"] <= start_idx < segment["end_idx"]:
                start_time = segment["start"]
                break

        if start_time is None:
            start_time = segment_map[0]["start"]

        for segment in segment_map:
            if segment["start_idx"] <= start_idx + len(chunk) <= segment["end_idx"]:
                duration += segment["duration"]

        split_segments.append({"text": chunk, "start": start_time, "duration": duration})

    return split_segments

def get_video_by_id_from_db(video_id) -> Video:
    """
     Retrieve a video from the database by its ID.

     :param video_id: The ID of the video to fetch
     :return: The Video object if found, else None
     """
    session = Session()
    try:
        video = session.query(Video).filter_by(id=video_id).first()
        print(f"Video Found in DB: {video.print_details()}")
        return video
    finally:
        session.close()