import requests
import datetime

subreddit = "disasterhazards"
url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=100"
headers = {'User-Agent': 'Mozilla/5.0 (compatible; Bot/0.1)'}
response = requests.get(url, headers=headers)

posts_last_hour = []

if response.status_code == 200:
    data = response.json()
    now = datetime.datetime.now(datetime.UTC)
    fifteen_minutes_ago = now - datetime.timedelta(minutes=15)

    for post in data['data']['children']:
        post_data = post['data']
        created_utc = datetime.datetime.fromtimestamp(post_data['created_utc'], datetime.UTC)
        if created_utc > fifteen_minutes_ago:
            post_info = {
                'title': post_data['title'],
                'selftext': post_data['selftext'],
                'url': f"https://reddit.com{post_data['permalink']}",
                'post_url': post_data.get('url', ''),
                'created_utc': created_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
            posts_last_hour.append(post_info)

for post in posts_last_hour:
    print(f"Title: {post['title']}")
    print(f"Post: {post['selftext']}")
    print(f"URL: {post['url']}")
    if post.get('post_url'):
        print(f"Content URL: {post['post_url']}")
    print(f"Time: {post['created_utc']}")
    print("-" * 80)
    print()
