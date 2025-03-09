import time
import sqlite3
from services.send_message import send_imessage
from services.get_messages import get_messages
from services.chatbot import generate_reply
from dotenv import load_dotenv
from typing import List
import itertools
import contextlib
import os


load_dotenv()

DEBUG = False

PHONE_NUMBER = os.getenv("PHONE_NUMBER")
DATABASE_PATH = "messages.db"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def wait_for_database(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Wait for database to become available"""
    for attempt in range(max_retries):
        try:
            # Try to make a quick connection to check if db is available
            conn = sqlite3.connect(DATABASE_PATH, timeout=1.0)
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database locked, waiting {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                print("Could not access database after maximum retries")
                raise
    return False

@contextlib.contextmanager
def get_db_connection():
    """Context manager for database connections with proper timeout and error handling"""
    # First ensure we can access the database
    wait_for_database()
    
    # If database file doesn't exist, we don't need WAL mode immediately
    is_new_db = not os.path.exists(DATABASE_PATH)
    
    # Connect with a longer timeout
    conn = sqlite3.connect(DATABASE_PATH, timeout=60.0)
    
    try:
        if not is_new_db:
            # Only set WAL mode if database already exists
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")  # 60 second busy timeout
        yield conn
    finally:
        try:
            conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")

def setup_database():
    """Ensure database has correct schema without dropping existing data"""
    for attempt in range(MAX_RETRIES):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                
                # Create the messages table only if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time TEXT,
                        sender TEXT,
                        message TEXT,
                        processed INTEGER DEFAULT 0,
                        UNIQUE(time, sender, message)
                    )
                """)
                
                # Now that table exists, we can safely set WAL mode
                cur.execute("PRAGMA journal_mode=WAL")
                
                # Verify table structure
                cur.execute("PRAGMA table_info(messages)")
                columns = cur.fetchall()
                print("Database initialized with structure:", columns)
                
                conn.commit()
                return
        except sqlite3.OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Failed to setup database, retrying in {RETRY_DELAY} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                raise

def chunk_messages(messages: List[tuple], chunk_size: int = 10):
    """Group messages into chunks for batch processing."""
    return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]

def combine_messages(messages: List[tuple]) -> str:
    """Combine multiple messages into a single context string."""
    combined = []
    for msg_id, time_str, sender, message in messages:
        combined.append(f"Time: {time_str}\nSender: {sender}\nMessage: {message}")
    return "\n\n".join(combined)

def process_new_messages(phone_number):
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        try:
            print("Starting to process new messages...")
            
            # First, verify table structure
            cur.execute("PRAGMA table_info(messages)")
            columns = cur.fetchall()
            print("Table structure:", columns)
            
            # Retrieve messages that haven't been processed yet, ordered by time
            cur.execute("""
                SELECT id, time, sender, message 
                FROM messages 
                WHERE processed = 0 OR processed IS NULL
                ORDER BY time ASC
            """)
            new_messages = cur.fetchall()
            
            print(f"Found {len(new_messages)} unprocessed messages")
            
            if not new_messages:
                return
            
            # Process messages in chunks
            message_chunks = chunk_messages(new_messages)
            print(f"Split into {len(message_chunks)} chunks")
            
            for i, chunk in enumerate(message_chunks):
                print(f"\nProcessing chunk {i+1}/{len(message_chunks)}")
                print(f"Chunk contains {len(chunk)} messages")
                
                # Combine messages in the chunk for context
                combined_message = combine_messages(chunk)
                
                # Generate reply for the combined messages
                reply = generate_reply(combined_message)
                
                if reply is not None and reply.text.strip() != "None":
                    print("Generated reply:", reply.text)
                    # Wait before sending the reply
                    time.sleep(5)
                    send_imessage(phone_number, reply.text, debug=DEBUG)
                
                # Mark all messages in this chunk as processed
                chunk_ids = [msg[0] for msg in chunk]
                print(f"Marking messages as processed: {chunk_ids}")
                
                # Update all messages in the chunk in a single transaction
                cur.execute("BEGIN TRANSACTION")
                try:
                    # Update all messages in chunk at once
                    cur.executemany(
                        "UPDATE messages SET processed = 1 WHERE id = ?",
                        [(id,) for id in chunk_ids]
                    )
                    
                    # Verify all updates
                    for msg_id in chunk_ids:
                        cur.execute("SELECT processed FROM messages WHERE id = ?", (msg_id,))
                        result = cur.fetchone()
                        print(f"Message {msg_id} processed status: {result[0] if result else 'not found'}")
                    
                    conn.commit()
                    print(f"Committed changes for chunk {i+1}")
                except Exception as e:
                    conn.rollback()
                    print(f"Error processing chunk {i+1}: {e}")
                    raise
                
                # Wait between chunks
                time.sleep(5)
            
            print("\nAll messages processed successfully")
            
            # Final verification of all processed messages
            cur.execute("SELECT COUNT(*) FROM messages WHERE processed = 0 OR processed IS NULL")
            remaining = cur.fetchone()[0]
            print(f"Remaining unprocessed messages: {remaining}")
            
        except Exception as e:
            print(f"Error processing messages: {e}")
            raise

def main():
    # Setup database with correct schema
    setup_database()
    
    while True:
        try:
            # Retrieve new messages using imessage-exporter
            get_messages(PHONE_NUMBER)
            # Process any unhandled messages
            process_new_messages(PHONE_NUMBER)
            # Wait before next check
            time.sleep(30)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    main()
