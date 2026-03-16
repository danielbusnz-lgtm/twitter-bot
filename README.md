# twitter-bot

A personal Claude Code slash command (`/twitter`) that fetches my latest GitHub activity and posts a tweet about it.

## How it works

1. Run `/twitter` inside Claude Code
2. Claude fetches recent GitHub activity for [@danielbusnz-lgtm](https://github.com/danielbusnz-lgtm)
3. Drafts a tweet and asks for confirmation
4. Posts to X/Twitter on approval

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your API keys
3. Install dependencies: `pip install -r requirements.txt`

## Required API Keys

- GitHub Personal Access Token
- X/Twitter API v2 keys (Consumer Key/Secret, Access Token/Secret)
