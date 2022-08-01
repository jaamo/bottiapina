import sys
import json
from apinadb import ApinaDB
from youtube import YouTube
from functions import check_for_new_videos

# Leaving this here for myself :)
# print(json.dumps(latest_upload, indent=2))

# Print help.
def print_help():
    print("Available commands:")
    print("")
    print("  db-channels                    List channel data from database.")
    print("  db-add-channel [channel id]    Add channel to database.")
    print("  get-new-videos                 Get new videos from YouTube and print.")
    print("  update-new-videos              Get new videos from YouTube and update to database.")
    print("  get-latest-video               Get latest video from the first channel from the list.")
    print("  reset-channel [channel id]     Reset latest video for channel")
    print("  db-reset                       DELETE EVERYTHING and recreate database.")

# Quit if not enough arguments.
if len(sys.argv) == 1:
    print_help()
    exit()

command = sys.argv[1]
apinaDB = ApinaDB()
youtube = YouTube()

# Get list of channels
if command == "db-channels":
    channels = apinaDB.get_channels()
    for channel in channels:
        print(channel)

# Add channel to local database.
elif command == "db-add-channel":
    if len(sys.argv) <= 2:
        print("Missing channel id.")
        exit()
    channel_id = sys.argv[2]
    channel_list = youtube.get_channel(channel_id)
    if "items" not in channel_list:
        print("Channel not found.")
        exit()
    print(json.dumps(channel_list, indent=2))
    channel_name = channel_list["items"][0]["snippet"]["title"]
    upload_playlist_id = channel_list["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    print("Channel name: %s" % (channel_name))
    print("Playlist id: %s" % (upload_playlist_id))
    apinaDB.add_channel(channel_id, channel_name, upload_playlist_id)

# Reset database.
elif command == "db-reset":
    print("Everything destroyed and recreated.")
    channels = apinaDB.reset()

# Get latest video
elif command == "get-latest-video":
    channels = apinaDB.get_channels()
    for channel in channels:
        new_latest_video = youtube.get_latest_upload(channel[2])
        print("Latest video")
        print(json.dumps(new_latest_video, indent=2))
        exit()

# Get list of new videos. Doesn't save anything.
elif command == "get-new-videos":
    new_videos = check_for_new_videos(youtube, apinaDB)
    print("New videos:")
    print(new_videos)

# Get list of new videos and save to db.
elif command == "update-new-videos":
    new_videos = check_for_new_videos(youtube, apinaDB)
    print("Updating new videos:")
    print(new_videos)
    for video in new_videos:
        apinaDB.update_latest_video(
            video["channel_id"], 
            video["video_id"],
            video["video_title"],
            video["video_url"],
            video["video_description"],
        )

# Get list of new videos and save to db.
elif command == "reset-channel":
    if len(sys.argv) <= 2:
        print("Missing channel id.")
        exit()
    channel_id = sys.argv[2]
    apinaDB.update_latest_video(
        channel_id, 
        '',
        '',
        '',
        '',
    )

else:
    print("Invalid command.")
    print("")
    print_help()
