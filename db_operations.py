import sqlite3
import logging
from datetime import datetime, timedelta

class DBOperations:
    def __init__(self, db_name='tweets.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.max_tweets = 10000  # Maximum number of tweets to keep

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.create_table()
            self.create_index()
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         content TEXT NOT NULL,
         status TEXT NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         posted_at TIMESTAMP)
        ''')
        self.conn.commit()

    def create_index(self):
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tweets (status)')
        self.conn.commit()

    def add_tweet(self, content):
        try:
            self.cursor.execute("INSERT INTO tweets (content, status) VALUES (?, ?)",
                                (content, 'pending'))
            self.conn.commit()
            self.check_and_cleanup()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error adding tweet to database: {e}")
            return None

    def bulk_add_tweets(self, tweets):
        try:
            self.cursor.executemany("INSERT INTO tweets (content, status) VALUES (?, ?)",
                                    [(tweet, 'pending') for tweet in tweets])
            self.conn.commit()
            self.check_and_cleanup()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            logging.error(f"Error adding tweets in bulk to database: {e}")
            return 0

    def get_pending_tweets(self):
        self.cursor.execute("SELECT id, content FROM tweets WHERE status = 'pending'")
        return self.cursor.fetchall()

    def authorize_tweet(self, tweet_id):
        try:
            self.cursor.execute("UPDATE tweets SET status = 'authorized' WHERE id = ?", (tweet_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error authorizing tweet: {e}")

    def remove_tweet(self, tweet_id):
        try:
            self.cursor.execute("DELETE FROM tweets WHERE id = ?", (tweet_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error removing tweet: {e}")

    def mark_as_posted(self, tweet_id):
        try:
            self.cursor.execute("UPDATE tweets SET status = 'posted', posted_at = ? WHERE id = ?",
                                (datetime.now(), tweet_id))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error marking tweet as posted: {e}")

    def get_next_authorized_tweet(self):
        self.cursor.execute("SELECT id, content FROM tweets WHERE status = 'authorized' ORDER BY created_at ASC LIMIT 1")
        return self.cursor.fetchone()

    def cleanup_old_tweets(self, days=30):
        try:
            self.cursor.execute("DELETE FROM tweets WHERE status = 'posted' AND posted_at < date('now', '-' || ? || ' days')", (days,))
            self.conn.commit()
            logging.info(f"Cleaned up tweets older than {days} days")
        except sqlite3.Error as e:
            logging.error(f"Error cleaning up old tweets: {e}")

    def check_and_cleanup(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM tweets")
            count = self.cursor.fetchone()[0]
            if count > self.max_tweets:
                excess = count - self.max_tweets
                self.cursor.execute("""
                    DELETE FROM tweets 
                    WHERE id IN (
                        SELECT id FROM tweets 
                        WHERE status = 'posted' 
                        ORDER BY posted_at ASC 
                        LIMIT ?
                    )
                """, (excess,))
                self.conn.commit()
                logging.info(f"Removed {excess} old tweets to maintain maximum capacity.")
        except sqlite3.Error as e:
            logging.error(f"Error during check and cleanup: {e}")

    def vacuum_database(self):
        try:
            self.conn.isolation_level = None
            self.cursor.execute("VACUUM")
            self.conn.isolation_level = ''
            logging.info("Database vacuumed successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error vacuuming database: {e}")

    def perform_maintenance(self):
        try:
            self.cleanup_old_tweets()
            self.check_and_cleanup()
            self.conn.commit()  # Ensure all changes are committed before vacuum
            self.vacuum_database()
            logging.info("Database maintenance completed successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error during database maintenance: {e}")
