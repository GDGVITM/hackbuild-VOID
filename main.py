from auto_mod import initialize_reddit, process_existing_posts, monitor_new_posts
from database import create_database

def main():
    create_database()
    
    reddit = initialize_reddit()
    if not reddit:
        print("Failed to initialize Reddit connection")
        return
    
    subreddit_name = 'disasterhazards'
    
    process_existing_posts(reddit, subreddit_name)
    
    monitor_new_posts(reddit, subreddit_name)

if __name__ == "__main__":
    main()
