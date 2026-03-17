# twitter-bot

A personal Claude Code slash command (`/twitter`) that fetches my latest GitHub activity, analyzes top tweet performance, and posts to X/Twitter.

## How it works

1. Run `/twitter` inside Claude Code
2. Claude fetches recent GitHub repos for [@danielbusnz-lgtm](https://github.com/danielbusnz-lgtm)
3. Loads engagement insights from `insights.json` (style tips, best posting hours, top tweet samples)
4. Drafts a tweet following high-engagement patterns and asks for confirmation
5. Posts to X/Twitter on approval — optionally with an image attachment

## Scripts

| Script | What it does |
|---|---|
| `post.py` | Post a tweet, optionally with an image (`--image path`) |
| `scraper.py` | Scrape tweets from followed accounts and store in `tweets.db` |
| `analyze.py` | Analyze `tweets.db` and regenerate `insights.json` |

## Usage

```bash
# Post a tweet
python3 post.py "Your tweet text"

# Post with an image
python3 post.py "Your tweet text" --image /path/to/image.png

# Refresh engagement insights
python3 scraper.py
python3 analyze.py
```

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your API keys
3. Install dependencies: `pip install -r requirements.txt`

## Required API Keys

- GitHub Personal Access Token
- X/Twitter API v2 keys (Consumer Key, Consumer Secret, Access Token, Access Token Secret)
