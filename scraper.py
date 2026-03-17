import asyncio
import json
import sqlite3
from twikit import Client

ACCOUNTS = ['levelsio', 'jeresig', 'codinghorror', 'dhh', 'jasonfried', 'naval', 'kritikakodes', 'collision', 'reidhoffman', 'omarsar0', 'AndrewYNg']

def init_db():
    conn = sqlite3.connect('tweets.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY,
            handle TEXT,
            text TEXT,
            likes INTEGER,
            retweets INTEGER,
            replies INTEGER,
            views INTEGER,
            posted_at TEXT
        )
    ''')
    conn.commit()
    return conn

def save_tweet(conn, handle, tweet):
    conn.execute('''
        INSERT OR IGNORE INTO tweets (id, handle, text, likes, retweets, replies, views, posted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tweet.id,
        handle,
        tweet.text,
        tweet.favorite_count,
        tweet.retweet_count,
        tweet.reply_count,
        tweet.view_count,
        tweet.created_at,
    ))
    conn.commit()

async def main():
    with open('cookies.json') as f:
        raw = json.load(f)
    cookies = {c['name']: c['value'] for c in raw}

    client = Client('en-US')
    client.set_cookies(cookies)

    conn = init_db()

    for handle in ACCOUNTS:
        print(f'Scraping {handle}...')
        try:
            user = await client.get_user_by_screen_name(handle)
            tweets = await client.get_user_tweets(user.id, 'Tweets', count=50)
            for t in tweets:
                save_tweet(conn, handle, t)
            print(f'  Saved {len(tweets)} tweets')
        except Exception as e:
            print(f'  Error: {e}')

    conn.close()
    print('Done.')

asyncio.run(main())
