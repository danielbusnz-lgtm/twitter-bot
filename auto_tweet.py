"""
auto_tweet.py — generates and posts a high-engagement tweet using Claude.
Designed to be run on a cron schedule.

Tracks posted tweets in posted.log to avoid repeats.
"""

import os
import json
import anthropic
import tweepy
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
INSIGHTS    = os.path.join(SCRIPT_DIR, "insights.json")
POSTED_LOG  = os.path.join(SCRIPT_DIR, "posted.log")
GITHUB_USER = "danielbusnz-lgtm"

X_CONSUMER_KEY        = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET     = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN        = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
ANTHROPIC_API_KEY     = os.getenv("ANTHROPIC_API_KEY")


def load_posted() -> set[str]:
    if not os.path.exists(POSTED_LOG):
        return set()
    with open(POSTED_LOG) as f:
        return {line.strip() for line in f if line.strip()}


def save_posted(text: str) -> None:
    with open(POSTED_LOG, "a") as f:
        f.write(text.strip() + "\n")


def generate_tweet(insights: dict, posted: set[str]) -> str:
    top_samples = "\n".join(
        f'- "{t["text"]}" ({t["likes"]} likes)'
        for t in insights["top_tweet_samples"][:5]
    )
    style_tips = "\n".join(f"- {t}" for t in insights["style_analysis"]["style_tips"])
    topics     = "\n".join(f"- {t}" for t in insights["style_analysis"]["topics_that_perform"])
    avoid      = "\n".join(f"- {t}" for t in insights["style_analysis"]["things_to_avoid"])
    posted_list = "\n".join(f'- "{p}"' for p in list(posted)[-20:]) if posted else "None yet"

    prompt = f"""You are writing a tweet for a software developer and builder.
Your goal is to write a single tweet that will get maximum engagement (likes, replies, reposts).

Top performing tweets for reference:
{top_samples}

Style tips:
{style_tips}

Topics that perform well:
{topics}

Things to avoid:
{avoid}

Recently posted tweets (DO NOT repeat these ideas):
{posted_list}

Write ONE tweet. Rules:
- Under 100 characters if possible, never more than 280
- No emojis
- No hashtags
- No em dashes
- State the conclusion first, no throat-clearing
- Pick a side hard — ambivalence kills engagement
- Declarative sentences only, no hedging language
- Use concrete numbers whenever possible (MRR, users, hours saved, etc.)
- Structural contrast works well: old vs new, expected vs actual
- Must be on a different topic/angle than the recently posted tweets above
- Topics that perform: AI reframing industries, contrarian takes, tech predictions stated as facts, product/market insights with numbers

Reply with only the tweet text, nothing else."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip().strip('"')


def post_tweet(text: str) -> str:
    client = tweepy.Client(
        consumer_key=X_CONSUMER_KEY,
        consumer_secret=X_CONSUMER_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return f"https://twitter.com/{GITHUB_USER}/status/{tweet_id}"


def main():
    with open(INSIGHTS) as f:
        insights = json.load(f)

    posted = load_posted()
    tweet  = generate_tweet(insights, posted)

    print(f"Tweet: {tweet}")
    url = post_tweet(tweet)
    save_posted(tweet)
    print(f"Posted: {url}")


if __name__ == "__main__":
    main()
