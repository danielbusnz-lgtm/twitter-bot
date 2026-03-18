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

    prompt = f"""You are writing a tweet for a software engineering student at UChicago who builds AI projects and side projects.
Your goal is to write a single tweet that gets maximum engagement (likes, replies, reposts).

Recently posted tweets (DO NOT repeat these ideas):
{posted_list}

Style — write in ONE of these formats, rotating between them:

1. Engagement question: conversational, "Be real...", "honest question:", pulls people into debate
   Example: "Be real... does learning to code even matter anymore with AI everywhere?"

2. Specific numbers story: a real-sounding person with specific financial/career details, end with "what do you think?"
   Example: "a dev I know is 23. He has: - $0 in savings - 3 SaaS apps - $8k MRR. Is he cooked?"

3. Community hook: invite people to connect around a shared identity
   Example: "If you're into AI, automation, or shipping 10x faster as a solo dev - let's connect"

Rules:
- Casual, conversational tone — sound like a real person, not a thought leader
- Use specific numbers and concrete details
- Emojis allowed sparingly (1 max)
- No hashtags
- No em dashes
- No corporate language or buzzwords
- Under 280 characters
- Must be on a different topic/angle than the recently posted tweets above
- Topics: AI tools, solo dev life, building in public, career, money, coding, side projects

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
