#!/usr/bin/env python3
"""
hiring_bot.py — searches for hiring posts and auto-replies with a personalized message.
Runs via cron. Tracks replied tweet IDs to avoid duplicates.
"""
import os
import json
import time
import tweepy
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

REPLIED_LOG = os.path.join(os.path.dirname(__file__), "hiring_replied.json")

SEARCH_QUERIES = [
    "hiring developer -is:retweet lang:en",
    "looking to hire engineer -is:retweet lang:en",
    "we are hiring python rust -is:retweet lang:en",
    "hiring software engineer -is:retweet lang:en",
]

MY_BIO = (
    "I'm a software developer who builds AI agents, trading bots, Rust TUIs, and "
    "full-stack tools. I ship fast and work across Python, Rust, and JavaScript."
)


def load_replied() -> set:
    if os.path.exists(REPLIED_LOG):
        with open(REPLIED_LOG) as f:
            return set(json.load(f))
    return set()


def save_replied(replied: set):
    with open(REPLIED_LOG, "w") as f:
        json.dump(list(replied), f)


def generate_reply(tweet_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": (
                f"Someone posted this hiring tweet:\n\"{tweet_text}\"\n\n"
                f"Write a casual, natural reply under 240 chars. "
                f"Sound like a real person, not a bot. No hashtags, no emojis. "
                f"Reference what they posted specifically. "
                f"The tone should be like: 'Hey, came across your post and would love to chat about [role/opportunity], let me know if you're free this week.' "
                f"The person replying is: {MY_BIO}"
            )
        }]
    )
    return message.content[0].text.strip()


def run():
    client = tweepy.Client(
        bearer_token=os.getenv("X_BEARER_TOKEN"),
        consumer_key=os.getenv("X_CONSUMER_KEY"),
        consumer_secret=os.getenv("X_CONSUMER_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )

    replied = load_replied()
    new_replies = 0

    for query in SEARCH_QUERIES:
        try:
            results = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["author_id", "created_at", "text"],
            )
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            continue

        if not results.data:
            continue

        for tweet in results.data:
            tweet_id = str(tweet.id)

            if tweet_id in replied:
                continue

            # Skip our own tweets
            if str(tweet.author_id) == os.getenv("X_USER_ID", ""):
                continue

            print(f"Replying to tweet {tweet_id}: {tweet.text[:80]}...")

            try:
                reply_text = generate_reply(tweet.text)
                client.create_tweet(
                    text=reply_text,
                    in_reply_to_tweet_id=tweet.id,
                )
                replied.add(tweet_id)
                new_replies += 1
                print(f"  Replied: {reply_text}")
                time.sleep(10)  # pace replies to avoid rate limits
            except Exception as e:
                print(f"  Reply failed: {e}")

        time.sleep(2)

    save_replied(replied)
    print(f"Done. {new_replies} new replies sent.")


if __name__ == "__main__":
    run()
