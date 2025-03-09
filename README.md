# AiMessages

This is an automated messaging tool designed to simulate natural, affectionate, and casual conversations, mimicking the style of "Arda" messaging his partner. Built with Python, it leverages AI (Google's Gemini model via LangChain) to analyze incoming iMessages, decide if a reply is needed, and generate short, personalized responses. It integrates with macOS's iMessage system to fetch and send messages seamlessly.

## Features

- **Message Retrieval**: Fetches new iMessages from a specified phone number using `imessage-exporter`.
- **AI-Powered Replies**: Uses a language model to analyze messages and generate natural, short replies (≤6 words) in a warm, casual tone.
- **Automation**: Continuously monitors for new messages and responds when appropriate.
- **Database Storage**: Stores messages in a SQLite database (`messages.db`) to track processed/unprocessed messages.

## Prerequisites

- **Python**: Version 3.13 or higher.
- **macOS**: Required for iMessage integration via AppleScript.
- **Dependencies**: Listed in `pyproject.toml` (managed with Poetry).
- **imessage-exporter**: A tool to export iMessages (must be installed separately).

## Installation

1. **Clone the Repository**:

2. **Install Poetry**
    ```bash
    pip install poetry
    poetry install
    ```

3. **Set Up Environment Variables**
    - Check .env.example

4. **Install imessage Exporter**
    - https://github.com/ReagentX/imessage-exporter

## Usage
```bash
poetry run python ardamessage/main.py
```