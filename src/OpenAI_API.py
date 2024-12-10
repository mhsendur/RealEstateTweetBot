from openai import OpenAI
from google.cloud import storage
import importlib.util
import os

# Define the bucket and credentials file name
BUCKET_NAME = "real-estate-bot-bucket"
CREDENTIALS_FILE = "credentials.py"

def download_credentials_from_gcs(bucket_name, file_name, local_path="credentials.py"):
    """Download the credentials.py file from Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    if not blob.exists():
        raise FileNotFoundError(f"Credentials file {file_name} not found in bucket {bucket_name}.")

    blob.download_to_filename(local_path)
    print(f"Downloaded {file_name} from bucket {bucket_name} to {local_path}")

def load_credentials_module(local_path="credentials.py"):
    """Dynamically load the credentials module."""
    spec = importlib.util.spec_from_file_location("credentials", local_path)
    credentials = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(credentials)
    return credentials

# Download the credentials file from GCS
download_credentials_from_gcs(BUCKET_NAME, CREDENTIALS_FILE)

# Load the credentials module
credentials = load_credentials_module()

# Initialize the OpenAI client using the API key
client = OpenAI(
    api_key=credentials.api_key
)

def create_tweet_text(raw_data):
    """Use OpenAI to generate a tweet text."""
    try:
        prompt = (
            "You are a real estate assistant generating tweets for property listings. "
            "Each tweet should be engaging, concise (under 280 characters), and include: "
            "1. Key details like title, price, location, and highlights. "
            "2. A call-to-action encouraging readers to check it out. "
            "3. Emojis to make it visually appealing.\n\n"
            f"Here is the property information:\n{raw_data}\n"
            "Generate a tweet for this listing in Turkish, but do NOT include any link or placeholder for a link in the tweet text."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        tweet_text = response.choices[0].message.content.strip()
        return tweet_text

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        raise
