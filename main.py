from youtube_chatbot import VideoChatBot, get_channel_videos, process_video, read_complete_table, read_chroma_db
import os
from dotenv import load_dotenv

def get_transcript_and_process_video(videos):
    for idx, video in enumerate(videos):
        print(f"Processing video {video['id']} -- {idx + 1}/{len(videos)}: {video['title']}")
        process_video(video['id'])

def get_transcript_and_process_by_video_id(video_ids):
    for vid in video_ids:
        print(f"Processing video {vid}")
        process_video(vid)

def initiate_question_answer_bot():
    bot = VideoChatBot()
    # Chat interface
    print("\nChatbot ready! Ask questions about the channel's content.")
    while True:
        query = input("\nYou: ")
        if query.lower() in ['exit', 'quit']:
            break

        response = bot.query(query)
        print("\nBot:")
        pretty_response:str = response['answer'].pretty_print()
        if response['answer'].content in "<TOPIC_NOT_FOUND>>":
            return
        print("\nReferences:")
        for ref in response['references']:
            print(f"- {ref['title']} ({ref['url']}) [{ref['start']}-{ref['end']}s]")

def crawl_channel_by_channel_id():
    """
    Crawl by channel by channel_id, this will ask user channel id before crawling
    :return: None
    """
    channel_id = input(f"Enter the YouTube Channel ID you want to crawl")
    print(f"Fetching channel videos for {channel_id} ...")
    videos = get_channel_videos(channel_id) # Temp comment to save quota
    if videos:
        get_transcript_and_process_video(videos)
    else:
        print('No Video found check you channel id')


def crawl_videos_of_channel_by_video_id():
    # Example channel ID (replace with actual) [vbp7EjCck4M]
    video_id = input(f"Enter the YouTube video ID that you want to crawl for transcript building?\n")
    get_transcript_and_process_by_video_id([video_id])


def print_env_file():
    print("\n All environment variables:")
    for key, value in os.environ.items():
        print(f"{key}: {value}")


def get_user_choice():
    options = {
        "1": "Option 1: Process Youtube Video by Video Id",
        "2": "Option 2: Ask Bot Question",
        "3": "Option 3: Process a Youtube video by Channel Id",
        "4": "Option 4: See existing Table information",
        "5": "Option 5: See Chroma DB information[Vector Information]",
        "6": "Option 6: Add to .env",
        "7": "Option 7: Print .env"
    }

    print("Please choose an option:")
    for key, value in options.items():
        print(f"{key}. {value}")

    choice = input("Enter your choice (1/2/3/4/5): \n").strip()
    print(f'choice: {choice}')
    return process_user_input(choice)

def add_env_variable():
    env_list = ['OPENAI_API_KEY','YOUTUBE_API_KEY']
    for key in env_list:
        # Get environment variable from user
        if os.environ[key]:
            value = input(f"Enter the value for {key}: \n")
            # Set the environment variable
            os.environ[key] = value

def process_user_input(choice):
    choice = choice.lower()
    match choice:
        case '1':
            crawl_videos_of_channel_by_video_id()
        case '2':
            initiate_question_answer_bot()
        case '3':
            crawl_channel_by_channel_id()
        case '4':
            read_complete_table()
        case '5':
            read_chroma_db()
        case '6':
            add_env_variable()
        case '7':
            print_env_file()
        case 'exit':
            exit()
        case _:
            print('Invalid Selection')


if __name__ == "__main__":
    load_dotenv()
    openai = os.getenv("OPENAI_API_KEY")
    if not openai:
        openai = input("OPENAI_API_KEY is missing. Please enter your API key: \n").strip()
        os.environ["OPENAI_API_KEY"] = openai  # Set the key for the session

    db_type = os.getenv("DB_TYPE")
    if not db_type:
        db_type = input("DB_TYPE is missing. Please enter your API key: \n").strip()
        os.environ["DB_TYPE"] = db_type  # Set the key for the session

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = input("DATABASE_URL is missing. Please enter your API key: \n").strip()
        os.environ["DATABASE_URL"] = db_url  # Set the key for the session
    while True:
        get_user_choice()
