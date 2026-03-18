"""
auto_reply.py — finds recent tweets from target accounts and posts thoughtful replies.
Designed to be run on a cron schedule (e.g. twice a day).

Tracks replied tweet IDs in replied.log to avoid double-replying.
"""

import os
import json
import random
import anthropic
import tweepy
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
TARGETS_FILE    = os.path.join(SCRIPT_DIR, "reply_targets.json")
REPLIED_LOG     = os.path.join(SCRIPT_DIR, "replied.log")
COOLDOWN_FILE   = os.path.join(SCRIPT_DIR, "reply_cooldown.json")
GITHUB_USER     = "danielbusnz-lgtm"

X_CONSUMER_KEY        = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET     = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN        = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN        = os.getenv("X_BEARER_TOKEN")
ANTHROPIC_API_KEY     = os.getenv("ANTHROPIC_API_KEY")

# How many accounts to sample per run, and max replies to post
ACCOUNTS_PER_RUN  = 8
REPLIES_PER_RUN   = 3
COOLDOWN_DAYS     = 7


def load_replied() -> set[str]:
    if not os.path.exists(REPLIED_LOG):
        return set()
    with open(REPLIED_LOG) as f:
        return {line.strip() for line in f if line.strip()}


def save_replied(tweet_id: str) -> None:
    with open(REPLIED_LOG, "a") as f:
        f.write(tweet_id.strip() + "\n")


def load_cooldowns() -> dict:
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    with open(COOLDOWN_FILE) as f:
        return json.load(f)


def save_cooldown(username: str, cooldowns: dict) -> None:
    cooldowns[username] = datetime.now(timezone.utc).isoformat()
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(cooldowns, f, indent=2)


def is_on_cooldown(username: str, cooldowns: dict) -> bool:
    if username not in cooldowns:
        return False
    last = datetime.fromisoformat(cooldowns[username])
    return datetime.now(timezone.utc) - last < timedelta(days=COOLDOWN_DAYS)


def fetch_recent_tweets(usernames: list[str], already_replied: set[str], cooldowns: dict) -> list[dict]:
    client = tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )

    candidates = []
    for username in usernames:
        if is_on_cooldown(username, cooldowns):
            print(f"  Skipping @{username} — replied within last {COOLDOWN_DAYS} days")
            continue
        query = f"from:{username} -is:retweet -is:reply"
        try:
            response = client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=["author_id", "created_at", "text", "reply_settings"],
                expansions=["author_id"],
                user_fields=["username"],
            )
        except Exception as e:
            print(f"Search failed for @{username}: {e}")
            continue

        if not response.data:
            continue

        users = {u.id: u.username for u in (response.includes.get("users") or [])}
        for tweet in response.data:
            if tweet.id in already_replied:
                continue
            # Skip tweets with restricted replies
            if getattr(tweet, "reply_settings", "everyone") != "everyone":
                print(f"  Skipping @{username} tweet {tweet.id} — reply_settings: {tweet.reply_settings}")
                continue
            # Skip very short tweets (not worth replying to)
            if len(tweet.text) < 30:
                continue
            candidates.append({
                "id": str(tweet.id),
                "username": users.get(tweet.author_id, username),
                "text": tweet.text,
            })

    return candidates


def generate_reply(tweet: dict) -> str:
    prompt = f"""You are replying to a tweet from @{tweet['username']} as a UChicago software engineering student who builds AI projects and side projects.

Tweet:
"{tweet['text']}"

Write a casual, conversational reply that sounds like a real person. Add genuine value with a personal take, relevant experience, or a question that continues the conversation.

Rules:
- Casual tone, sound like a real person not a thought leader
- Under 280 characters
- No hashtags
- No em dashes
- No sycophancy ("great point!", "love this!", "this is so true!")
- Emojis allowed sparingly (1 max)
- Can ask a follow-up question to spark conversation
- Use specific numbers or personal experience when relevant
- If you have nothing useful to add, reply with: SKIP

Reply with only the reply text or SKIP."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip().strip('"')


def post_reply(text: str, reply_to_id: str) -> str:
    client = tweepy.Client(
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    response = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_id)
    tweet_id = response.data["id"]
    return f"https://twitter.com/{GITHUB_USER}/status/{tweet_id}"


def main():
    with open(TARGETS_FILE) as f:
        targets = json.load(f)

    all_accounts = targets.get("big_accounts", []) + targets.get("peers", [])
    if not all_accounts:
        print("No target accounts configured in reply_targets.json")
        return

    sample = random.sample(all_accounts, min(ACCOUNTS_PER_RUN, len(all_accounts)))
    print(f"Sampling accounts: {sample}")

    already_replied = load_replied()
    cooldowns = load_cooldowns()
    candidates = fetch_recent_tweets(sample, already_replied, cooldowns)

    if not candidates:
        print("No new tweets to reply to.")
        return

    random.shuffle(candidates)
    posted = 0

    for tweet in candidates:
        if posted >= REPLIES_PER_RUN:
            break

        print(f"\nConsidering @{tweet['username']}: {tweet['text'][:80]}...")
        reply = generate_reply(tweet)

        if reply.upper() == "SKIP":
            print("Claude skipped this one.")
            continue

        print(f"Reply: {reply}")
        try:
            url = post_reply(reply, tweet["id"])
            save_replied(tweet["id"])
            save_cooldown(tweet["username"], cooldowns)
            print(f"Posted: {url}")
            posted += 1
        except Exception as e:
            print(f"Failed to post reply: {e}")

    print(f"\nDone. Posted {posted} replies.")


if __name__ == "__main__":
    main()
