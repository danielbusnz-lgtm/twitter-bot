import os
import sys
import argparse
import tweepy
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "danielbusnz-lgtm"

X_CONSUMER_KEY        = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET     = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN        = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")


def get_github_context():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(
        f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=5",
        headers=headers,
    )
    repos = res.json()
    lines = []
    for repo in repos:
        lines.append(f"- {repo['name']}: {repo['description'] or 'no description'} ({repo['html_url']})")
    return "\n".join(lines)


def post_tweet(text, image_path=None):
    media_ids = None

    if image_path:
        # v1.1 API — only way to upload media
        auth = tweepy.OAuth1UserHandler(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET,
        )
        api = tweepy.API(auth)
        media = api.media_upload(filename=image_path)
        media_ids = [media.media_id_string]

    # v2 Client — posts the tweet
    client = tweepy.Client(
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    response = client.create_tweet(text=text, media_ids=media_ids)
    tweet_id = response.data["id"]
    print(f"https://twitter.com/{GITHUB_USER}/status/{tweet_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("text",          nargs="?", default=None, help="Tweet text")
    parser.add_argument("--image", "-i", default=None,            help="Path to image file")
    args = parser.parse_args()

    if args.text is None:
        print(get_github_context())
    else:
        post_tweet(args.text, image_path=args.image)
