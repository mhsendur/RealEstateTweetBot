from openai import OpenAI
import credentials

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key= credentials.api_key,
)

def create_tweet_text(raw_data, url):
    """Use OpenAI to generate a tweet text."""
   
    try:

        prompt = (
            "You are a real estate assistant generating tweets for property listings. "
            "Each tweet should be engaging, concise (under 280 characters), and include: "
            "1. Key details like title, price, location, and highlights. "
            "2. A call-to-action encouraging readers to click the link. "
            "3. Emojis to make it visually appealing.\n\n"
            f"Here is the property information:\n{raw_data}\n\n"
            f"URL: {url}\n"
            "Generate a tweet for this listing in turkish."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract response content using `message.content`
        tweet_text = response.choices[0].message.content.strip()
        return tweet_text

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        raise