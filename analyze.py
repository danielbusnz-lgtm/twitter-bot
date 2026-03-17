import json
import sqlite3
import os
from datetime import datetime
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

conn = sqlite3.connect('tweets.db')
df = pd.read_sql('SELECT * FROM tweets', conn)
conn.close()

# Drop retweets
df = df[~df['text'].str.startswith('RT @')]

# Parse posted_at
df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
df['hour'] = df['posted_at'].dt.hour
df['length'] = df['text'].str.len()

# 1. Average likes per account
avg_likes = df.groupby('handle')['likes'].mean().round(0).sort_values(ascending=False).to_dict()

# 2. Best time to post (hour with highest avg likes)
best_hours = df.groupby('hour')['likes'].mean().sort_values(ascending=False)
top_hours = best_hours.head(3).index.tolist()

# 3. Tweet length vs engagement
df['length_bucket'] = pd.cut(df['length'], bins=[0, 100, 200, 280], labels=['short', 'medium', 'long'])
length_perf = df.groupby('length_bucket', observed=True)['likes'].mean().round(0).to_dict()

# 4. Views-to-likes ratio
df['views'] = pd.to_numeric(df['views'], errors='coerce')
df['engagement_rate'] = (df['likes'] / df['views'].replace(0, None)).round(4)
avg_engagement = df.groupby('handle')['engagement_rate'].mean().round(4).sort_values(ascending=False).to_dict()

# 5. Top 20% tweets for style analysis
threshold = df['likes'].quantile(0.8)
top_tweets = df[df['likes'] >= threshold].sort_values('likes', ascending=False)
top_tweet_samples = top_tweets[['handle', 'likes', 'text']].head(30).to_dict(orient='records')

# 6. Claude style analysis
client = Anthropic()
tweets_text = '\n\n'.join([f"[{t['handle']} - {t['likes']} likes]\n{t['text']}" for t in top_tweet_samples])

response = client.messages.create(
    model='claude-sonnet-4-6',
    max_tokens=1024,
    messages=[{
        'role': 'user',
        'content': f"""Analyze these top-performing tweets and extract writing style patterns that make them successful.

{tweets_text}

Return a JSON object with these fields:
- tone: overall tone (e.g. "direct", "conversational", "opinionated")
- common_structures: list of sentence/post structures that appear often
- topics_that_perform: list of topic types that get high engagement
- things_to_avoid: list of patterns that seem absent from top posts
- style_tips: 3-5 actionable tips for writing tweets in this style

Return only valid JSON, no explanation."""
    }]
)

raw = response.content[0].text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
style = json.loads(raw)

# Build insights
insights = {
    'generated_at': datetime.now().isoformat(),
    'avg_likes_by_account': avg_likes,
    'best_hours_to_post_utc': top_hours,
    'likes_by_tweet_length': length_perf,
    'engagement_rate_by_account': avg_engagement,
    'style_analysis': style,
    'top_tweet_samples': top_tweet_samples[:10]
}

with open('insights.json', 'w') as f:
    json.dump(insights, f, indent=2)

print('insights.json saved.')
print(f"\nTop accounts by avg likes: {list(avg_likes.items())[:3]}")
print(f"Best hours to post (UTC): {top_hours}")
print(f"Likes by length: {length_perf}")
print(f"\nStyle tips:")
for tip in style.get('style_tips', []):
    print(f"  - {tip}")
