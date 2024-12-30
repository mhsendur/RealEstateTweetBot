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
    """Use OpenAI to generate a creative and engaging tweet text."""
    try:
        prompt = (
            "You are a creative real estate assistant generating tweets for property listings in Turkish. "
            "Your goal is to make the tweet engaging, human-like, and avoid spam-like behavior. Each tweet must:\n"
            "1. Be concise (under 280 characters).\n"
            "2. Include the price of the listing explicitly.\n"
            "3. Highlight key details (title, location, features, and unique selling points).\n"
            "4. Use emojis to make the tweet visually appealing but not excessive (2-4 emojis is ideal).\n"
            "5. Contain a compelling call-to-action encouraging engagement or exploration.\n"
            "6. Be in Turkish and must NOT include any link or placeholder for a link.\n\n"
            "Here is the property information:\n"
            f"{raw_data}\n\n"
            "Generate a creative tweet text following these guidelines. Ensure the tweet feels human, engaging, and unique."
        )

        # OpenAI API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        # Extracting the generated tweet text
        tweet_text = response.choices[0].message.content.strip()

        # Ensuring price is included in the text (basic check)
        if "TL" not in tweet_text:
            tweet_text += "\n💵 Fiyatı kontrol etmeyi unutmayın!"

        return tweet_text

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return "İlan hakkında daha fazla bilgi alın! 🏡"

