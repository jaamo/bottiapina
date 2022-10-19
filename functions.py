# Load channel list from database and then check against YouTube API 
# if there are any new videos.
def check_for_new_videos(youtube, apinaDB):

    new_videos = []

    # Get list of channels.
    for channel in apinaDB.get_channels():
        channel_id = channel[0]
        channel_name = channel[1]
        upload_playlist_id = channel[2]
        latest_video_id = channel[3]

        print("Get videos for playlist %s" % (upload_playlist_id))

        try:
            # Get latest video id from YouTube.
            new_latest_video = youtube.get_latest_upload(upload_playlist_id)

            # Check if video is new.
            if latest_video_id != new_latest_video["video_id"]:
                # print("New video %s for channel %s." % (new_latest_video_id, upload_playlist_id))
                new_videos.append({
                    "channel_id": channel_id, 
                    "channel_name": channel_name, 
                    "video_id": new_latest_video["video_id"],
                    "video_url": new_latest_video["video_url"],
                    "video_title": new_latest_video["video_title"],
                    "video_description": new_latest_video["video_description"],
                })
        except:
            print("Failed to load latest upload.")

    return new_videos