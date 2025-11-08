import os
import json

import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

load_dotenv()
YOUTUBE_APY_KEY = os.getenv('YOUTUBE_APY_KEY')

# Manage YouTube API queries.
class YouTube:
    api_service_name = "youtube"
    api_version = "v3"
    youtube = None

    def __init__(self):
        self.youtube = googleapiclient.discovery.build(
            self.api_service_name, self.api_version, developerKey=YOUTUBE_APY_KEY)

    def get_channel(self, channel_id):
        request = self.youtube.channels().list(
            part="snippet,contentDetails",
            id=channel_id
        )
        return request.execute()

    def get_channel_by_handle(self, handle):
        # Remove @ if present
        handle = handle.lstrip('@')
        request = self.youtube.channels().list(
            part="snippet,contentDetails",
            forHandle=handle
        )
        return request.execute()

    def get_latest_upload_id(self, playlist_id):
        request = self.youtube.playlistItems().list(
            part="id,contentDetails,snippet",
            maxResults=1,
            playlistId=playlist_id
        )
        latest_upload = request.execute()
        return latest_upload['items'][0]['id']

    def get_latest_upload(self, playlist_id):
        request = self.youtube.playlistItems().list(
            part="id,contentDetails,snippet",
            maxResults=1,
            playlistId=playlist_id
        )
        latest_upload = request.execute()
        #print(json.dumps(latest_upload, indent=2))
        return {
            "video_id": latest_upload['items'][0]['id'],
            "video_title": latest_upload['items'][0]['snippet']['title'],
            "video_description": latest_upload['items'][0]['snippet']['description'],
            "video_url": "https://www.youtube.com/watch?v=%s" % (latest_upload['items'][0]['snippet']['resourceId']['videoId']),
        }
