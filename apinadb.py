import sqlite3

# Manage local data storage.
class ApinaDB:

    con=None
    cur=None

    def __init__(self):
        self.con = sqlite3.connect('bottiapina.db')
        self.cur = self.con.cursor()
        # The bot runs off a Raspberry Pi SD card and now commits on every
        # message, so keep the write path cheap.
        self.con.execute('PRAGMA journal_mode=WAL')
        self._ensure_schema()

    # Create the tables that are added after the initial release. Runs on every
    # start so deploying to an existing database does NOT require db-reset
    # (which would destroy the followed channel list).
    def _ensure_schema(self):
        cur = self.con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS messages
                    (message_id INTEGER PRIMARY KEY,
                     channel_id INTEGER NOT NULL,
                     parent_id INTEGER,
                     is_thread INTEGER NOT NULL,
                     author_id INTEGER NOT NULL,
                     author_name TEXT,
                     channel_name TEXT,
                     is_bot INTEGER NOT NULL,
                     created_at TEXT NOT NULL)''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)')
        cur.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
        self.con.commit()

    # Drop databases and recreate. DESTROYS ALL DATA! BUAHAHAH!
    def reset(self):
        self.cur.execute('''DROP TABLE IF EXISTS channels''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS channels
                    (channel_id UNIQUE, channel_name, upload_playlist_id, video_id, video_title, video_url, video_description)''')
        self.con.commit()

    # Get all channels from database.
    def get_channels(self):
        # Returns rows, not the cursor: the caller iterates this while other
        # queries (message logging, stats) run against the same connection.
        return self.cur.execute('SELECT * FROM channels').fetchall()

    # Check if channel exists.
    def channel_exists(self, channel_id):
        self.cur.execute('SELECT channel_id FROM channels WHERE channel_id = ?', (channel_id,))
        return self.cur.fetchone() is not None

    # Add channel.
    def add_channel(self, channel_id, channel_name, upload_playlist_id):
        self.cur.execute("INSERT INTO channels VALUES (?, ?, ?, '', '', '', '')",
            (channel_id, channel_name, upload_playlist_id))
        self.con.commit()

    def update_latest_video(self, channel_id, video_id, video_title, video_url, video_description):
        self.cur.execute('''
            UPDATE      channels
            SET         video_id = ?, video_title = ?, video_url = ?, video_description = ?
            WHERE       channel_id = ? ''',
            (video_id, video_title, video_url, video_description, channel_id))
        self.con.commit()

    # Remove channel.
    def remove_channel(self, channel_id):
        self.cur.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
        self.con.commit()
        return self.cur.rowcount > 0

    #
    # Message statistics. Only metadata is stored, never message content.
    #

    # Store a single message. INSERT OR IGNORE because the live listener and the
    # backfill can see the same message.
    def log_message(self, message_id, channel_id, parent_id, is_thread, author_id,
                    author_name, channel_name, is_bot, created_at):
        cur = self.con.cursor()
        cur.execute('''INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (message_id, channel_id, parent_id, int(is_thread), author_id,
             author_name, channel_name, int(is_bot), created_at))
        self.con.commit()

    # Store a batch of messages (backfill). Returns the number of new rows.
    def log_messages(self, rows):
        cur = self.con.cursor()
        cur.executemany('''INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', rows)
        self.con.commit()
        return cur.rowcount

    # Most active channels in [start_utc, end_utc). Messages posted in a thread
    # count towards the thread's parent channel. Bots are excluded.
    def top_channels(self, start_utc, end_utc, limit=5):
        cur = self.con.cursor()
        return cur.execute('''
            SELECT      COALESCE(parent_id, channel_id) AS ch,
                        COUNT(*) AS n,
                        MAX(channel_name) AS name
            FROM        messages
            WHERE       created_at >= ? AND created_at < ? AND is_bot = 0
            GROUP BY    ch
            ORDER BY    n DESC
            LIMIT       ?''', (start_utc, end_utc, limit)).fetchall()

    # Most active members in [start_utc, end_utc). Bots are excluded.
    def top_members(self, start_utc, end_utc, limit=5):
        cur = self.con.cursor()
        return cur.execute('''
            SELECT      author_id,
                        COUNT(*) AS n,
                        MAX(author_name) AS name
            FROM        messages
            WHERE       created_at >= ? AND created_at < ? AND is_bot = 0
            GROUP BY    author_id
            ORDER BY    n DESC
            LIMIT       ?''', (start_utc, end_utc, limit)).fetchall()

    # Message counts per channel in [start_utc, end_utc), keyed by the channel
    # the message was actually posted in (threads stay separate here). Bots are
    # excluded.
    def message_counts_by_channel(self, start_utc, end_utc):
        cur = self.con.cursor()
        rows = cur.execute('''
            SELECT      channel_id, COUNT(*)
            FROM        messages
            WHERE       created_at >= ? AND created_at < ? AND is_bot = 0
            GROUP BY    channel_id''', (start_utc, end_utc)).fetchall()
        return {row[0]: row[1] for row in rows}

    # Total number of (non-bot) messages in [start_utc, end_utc).
    def message_count(self, start_utc, end_utc):
        cur = self.con.cursor()
        row = cur.execute('''
            SELECT      COUNT(*)
            FROM        messages
            WHERE       created_at >= ? AND created_at < ? AND is_bot = 0''',
            (start_utc, end_utc)).fetchone()
        return row[0] if row else 0

    # Total number of stored message rows, bots included.
    def total_messages(self):
        cur = self.con.cursor()
        return cur.execute('SELECT COUNT(*) FROM messages').fetchone()[0]

    # Drop message rows older than before_utc.
    def prune_messages(self, before_utc):
        cur = self.con.cursor()
        cur.execute('DELETE FROM messages WHERE created_at < ?', (before_utc,))
        self.con.commit()
        return cur.rowcount

    #
    # Simple key/value state.
    #

    def get_state(self, key, default=None):
        cur = self.con.cursor()
        row = cur.execute('SELECT value FROM state WHERE key = ?', (key,)).fetchone()
        return row[0] if row else default

    def set_state(self, key, value):
        cur = self.con.cursor()
        cur.execute('INSERT OR REPLACE INTO state VALUES (?, ?)', (key, value))
        self.con.commit()
