#!/usr/bin/env python3
"""Test Reddit API connection with your credentials"""

import os
from dotenv import load_dotenv
import praw
from datetime import datetime

def test_reddit_credentials():
    """Test Reddit API credentials"""
    
    print("🔍 Testing Reddit API Connection")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    print(f"Client ID: {client_id[:10]}...{client_id[-4:] if client_id else 'Not found'}")
    print(f"Client Secret: {'✅ Found' if client_secret else '❌ Not found'}")
    
    if not client_id or not client_secret:
        print("❌ Reddit credentials not found in .env file")
        print("Make sure your .env file contains:")
        print("REDDIT_CLIENT_ID=your_client_id")
        print("REDDIT_CLIENT_SECRET=your_client_secret")
        return False
    
    try:
        # Initialize Reddit instance
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="ResumeIntelligenceBot/1.0"
        )
        
        print(f"\n🔗 Connecting to Reddit API...")
        
        # Test basic access
        subreddit = reddit.subreddit('python')
        print(f"✅ Successfully connected to Reddit!")
        print(f"   Subreddit: r/python")
        print(f"   Subscribers: {subreddit.subscribers:,}")
        
        # Test API limits
        try:
            limits = reddit.auth.limits
            print(f"\n📊 API Rate Limits:")
            print(f"   Remaining requests: {limits['remaining']}")
            print(f"   Reset time: {datetime.fromtimestamp(limits['reset_timestamp'])}")
        except:
            print(f"   Rate limit info not available (normal for read-only access)")
        
        # Test scraping a few posts
        print(f"\n📄 Testing post access...")
        posts = list(subreddit.hot(limit=3))
        
        for i, post in enumerate(posts, 1):
            print(f"   {i}. {post.title[:50]}...")
            print(f"      Score: {post.score}, Comments: {post.num_comments}")
        
        print(f"\n✅ Reddit API test successful!")
        print(f"   You can scrape Reddit with these credentials")
        
        return True
        
    except Exception as e:
        print(f"❌ Reddit API test failed: {e}")
        return False

if __name__ == "__main__":
    test_reddit_credentials()