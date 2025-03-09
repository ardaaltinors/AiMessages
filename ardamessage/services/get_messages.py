import subprocess
import datetime
import glob
import sqlite3
import os
import re

def get_messages(number):
    """
    Retrieves new iMessage messages using imessage-exporter, parses them in blocks of three lines:
      1) Time
      2) Sender
      3) Message
    and saves them to a SQLite database with columns (time, sender, message, processed).
    
    Steps:
    1. Runs: imessage-exporter -f txt -t "<number>" -s <2_days_ago> -o .
    2. Processes only files named '+*.txt'.
    3. Parses file content in blocks of exactly three lines; each block is inserted into the DB:
       - time = line 1
       - sender = line 2
       - message = line 3
    4. Cleans up all .txt files afterward.
    """

    # Calculate the start date: 2 days before today (YYYY-MM-DD).
    start_date = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    # 1. Run imessage-exporter command.
    command = [
        "imessage-exporter",
        "-f", "txt",
        "-t", number,
        "-s", start_date,
        "-o", "."
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running imessage-exporter: {e}")
        return

    # 2. Connect to (or create) SQLite database.
    conn = sqlite3.connect("messages.db")
    cur = conn.cursor()

    # Create messages table with time, sender, message and a processed flag.
    # The UNIQUE constraint ensures no duplicate rows based on (time, sender, message).
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

    # 3. Process only files whose names start with '+' (e.g. "+905335577110.txt").
    for filepath in glob.glob("+*.txt"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read().strip()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            continue

        # Remove outer bracket if present.
        if file_content.startswith("["):
            file_content = file_content[1:]
        if file_content.endswith("]"):
            file_content = file_content[:-1]

        # Split the content into blocks separated by one or more blank lines.
        blocks = re.split(r"\n\s*\n", file_content)

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]

            # Only process blocks with exactly 3 lines: (time, sender, message).
            if len(lines) != 3:
                continue

            time_line, sender_line, message_line = lines

            # 4. Insert each block into the DB.
            try:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO messages (time, sender, message)
                    VALUES (?, ?, ?)
                    """,
                    (time_line, sender_line, message_line)
                )
            except Exception as e:
                print(f"Error inserting block into DB from file {filepath}: {e}")

    # Commit changes and close the connection.
    conn.commit()
    conn.close()

    # 5. Clean up: remove all .txt files in the current directory.
    for txt_file in glob.glob("*.txt"):
        try:
            os.remove(txt_file)
        except Exception as e:
            print(f"Error removing file {txt_file}: {e}")

if __name__ == "__main__":
    get_messages("5555555555")
