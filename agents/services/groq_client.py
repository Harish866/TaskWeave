
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Find the project's root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from the .env file")

client = Groq(api_key=api_key)


def ask_groq(prompt, json_mode=False):
    """
    Send a prompt to Groq and return the AI response.
    """

    response = client.chat.completions.create(
        response_format={"type": "json_object"} if json_mode else {"type": "text"},
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content
