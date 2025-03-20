from googleapiclient.discovery import build
from .utility import append_response_to_json, read_json_file
import isodate
from dotenv import load_dotenv
import os
from .database import Session, Video

def get_youtube_service():
    """Initialize and return a YouTube API client."""
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        api_key = input("YOUTUBE_API_KEY is missing. Please enter your API key: ").strip()

    return build('youtube', 'v3', developerKey=api_key)

def get_channel_videos(channel_id, max_results=1):
    """
        Fetches videos from a specified YouTube channel.

        :param channel_id: ID of the YouTube channel
        :param max_results: Number of videos to fetch (default is 1)
        :return: List of video details (ID and title)
    """
    youtube = get_youtube_service()
    request = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        maxResults=max_results,
        type="video",
        eventType="completed"
    )
    videos = []
    while request:
        response = request.execute()
        print(f"response={response}")
        videos.extend(
            {'id': item['id']['videoId'], 'title': item['snippet']['title']}
            for item in response.get('items', [])
        )
        request = youtube.search().list_next(request, response)

    print(f"videos={videos}")
    append_response_to_json(videos, f'{channel_id}-video-list.json')
    return videos

def get_video_details(video_id):
    """
      Retrieves video details either from the database or the YouTube API.

      :param video_id: The ID of the video
      :return: Dictionary containing video details (ID, length, title)
      """
    return get_video_by_id_from_api(video_id)

def get_video_by_id_from_api(video_id):
    """
      Fetches video details from the YouTube API.

      :param video_id: The ID of the video to fetch
      :return: Dictionary containing video ID, length, and title
    """
    youtube = get_youtube_service()
    # Below is temp code to save quota
    response = youtube.videos().list(
        part="contentDetails,snippet",
        id=video_id
    ).execute()
    append_response_to_json(response, f'{video_id}-video-details.json')

    if response is None:
        return {}
    video_data = response['items'][0]
    return {
        'video_id': video_id,
        'length': isodate.parse_duration(video_data['contentDetails']['duration']).total_seconds(),
        'title': video_data['snippet']['title']
    }

