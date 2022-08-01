import sqlite3

# Manage local data storage.
class ApinaDB:

    con=None
    cur=None

    def __init__(self):
        self.con = sqlite3.connect('bottiapina.db')
        self.cur = self.con.cursor()

    # Drop databases and recreate. DESTROYS ALL DATA! BUAHAHAH!
    def reset(self):
        self.cur.execute('''DROP TABLE IF EXISTS channels''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS channels
                    (channel_id UNIQUE, channel_name, upload_playlist_id, video_id, video_title, video_url, video_description)''')
        self.con.commit()

    # Get all channels from database.
    def get_channels(self):
        return self.cur.execute('SELECT * FROM channels')

    # Add channel.
    def add_channel(self, channel_id, channel_name, upload_playlist_id):
        # No idea if this is safe :shrug:
        self.cur.execute("INSERT INTO channels VALUES ('%s', '%s', '%s', '', '', '', '')" % (channel_id, channel_name, upload_playlist_id))
        self.con.commit()

    def update_latest_video(self, channel_id, video_id, video_title, video_url, video_description):
        self.cur.execute('''
            UPDATE      channels 
            SET         video_id = '%s', video_title = '%s', video_url = '%s', video_description = '%s' 
            WHERE       channel_id = '%s' ''' 
            % (video_id, video_title, video_url, video_description, channel_id))
        self.con.commit()
