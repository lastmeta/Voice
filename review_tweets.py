from db_operations import DBOperations
from openai_api import OpenAIClient
import logging
from config import AnsiColor, set_cmd_title, set_virtual_terminal_level

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure CMD supports ANSI escape codes
set_virtual_terminal_level()

# Set the CMD window title
set_cmd_title("Tweet Review System")

def generate_additional_tweet():
    print(f"\n{AnsiColor.OKBLUE}Generating a new tweet...{AnsiColor.ENDC}")
    tweet_content = OpenAIClient.generate_tweet_with_hashtags()
    if tweet_content:
        print(f"{AnsiColor.OKGREEN}Generated tweet: {tweet_content}{AnsiColor.ENDC}")
        confirm = input("Do you want to add this tweet to the queue? (y/n): ").lower()
        if confirm == 'y':
            db.add_tweet(tweet_content)
            print(f"{AnsiColor.OKGREEN}Tweet added to the queue.{AnsiColor.ENDC}")
        else:
            print(f"{AnsiColor.FAIL}Tweet discarded.{AnsiColor.ENDC}")
    else:
        print(f"{AnsiColor.FAIL}Failed to generate a new tweet.{AnsiColor.ENDC}")

def generate_bulk_tweets(count=10):
    print(f"\n{AnsiColor.OKBLUE}Generating {count} tweets...{AnsiColor.ENDC}")
    tweets = []
    for i in range(count):
        tweet_content = OpenAIClient.generate_tweet_with_hashtags()
        if tweet_content:
            print(f"Tweet {i+1}: {tweet_content}")
            tweets.append(tweet_content)
        else:
            print(f"{AnsiColor.FAIL}Failed to generate tweet {i+1}{AnsiColor.ENDC}")
    
    if tweets:
        confirm = input(f"Do you want to add these {len(tweets)} tweets to the queue? (y/n): ").lower()
        if confirm == 'y':
            added_count = db.bulk_add_tweets(tweets)
            print(f"{AnsiColor.OKGREEN}{added_count} tweets added to the queue.{AnsiColor.ENDC}")
        else:
            print(f"{AnsiColor.FAIL}Tweets discarded.{AnsiColor.ENDC}")
    else:
        print(f"{AnsiColor.FAIL}No tweets were generated successfully.{AnsiColor.ENDC}")

def create_new_tweet():
    print(f"\n{AnsiColor.OKBLUE}Creating a new tweet...{AnsiColor.ENDC}")
    tweet_content = input(f"{AnsiColor.BOLD}Enter the tweet content: {AnsiColor.ENDC}")
    if tweet_content:
        db.add_tweet(tweet_content)
        print(f"{AnsiColor.OKGREEN}Tweet added to the queue.{AnsiColor.ENDC}")
    else:
        print(f"{AnsiColor.FAIL}Tweet content cannot be empty.{AnsiColor.ENDC}")

def edit_tweet(tweet_id, content):
    print(f"\n{AnsiColor.HEADER}Editing tweet {tweet_id}{AnsiColor.ENDC}")
    print(f"Current content: {content}")
    new_content = input("Enter the new content (or press Enter to keep current): ")
    if new_content:
        db.cursor.execute("UPDATE tweets SET content = ? WHERE id = ?", (new_content, tweet_id))
        db.conn.commit()
        print(f"{AnsiColor.OKGREEN}Tweet updated successfully.{AnsiColor.ENDC}")
    else:
        print(f"{AnsiColor.WARNING}No changes made.{AnsiColor.ENDC}")

def display_all_tweets():
    db.cursor.execute("SELECT id, content, status FROM tweets ORDER BY id DESC LIMIT 50")
    tweets = db.cursor.fetchall()
    if not tweets:
        print(f"{AnsiColor.FAIL}No tweets found in the database.{AnsiColor.ENDC}")
    else:
        print(f"\n{AnsiColor.HEADER}{'=' * 50}\n--- All Tweets (Last 50) ---\n{'=' * 50}{AnsiColor.ENDC}")
        for tweet in tweets:
            print(f"{AnsiColor.BOLD}ID: {tweet[0]} | Status: {tweet[2]}{AnsiColor.ENDC}")
            print(f"Content: {tweet[1]}")
            print(f"{AnsiColor.OKBLUE}{'-' * 50}{AnsiColor.ENDC}")

def perform_maintenance():
    print(f"\n{AnsiColor.OKBLUE}Performing database maintenance...{AnsiColor.ENDC}")
    try:
        db.perform_maintenance()
        print(f"{AnsiColor.OKGREEN}Maintenance completed successfully.{AnsiColor.ENDC}")
    except Exception as e:
        print(f"{AnsiColor.FAIL}An error occurred during maintenance: {e}{AnsiColor.ENDC}")
    print(f"{AnsiColor.WARNING}You can check the log file for detailed information.{AnsiColor.ENDC}")

def remove_specific_tweet():
    display_all_tweets()
    tweet_id = input("Enter the ID of the tweet you want to remove (or 'c' to cancel): ")
    if tweet_id.lower() == 'c':
        return
    db.cursor.execute("SELECT content FROM tweets WHERE id = ?", (tweet_id,))
    result = db.cursor.fetchone()
    if result:
        print(f"\n{AnsiColor.HEADER}{'=' * 50}\nTweet ID: {tweet_id}\n{'=' * 50}{AnsiColor.ENDC}")
        print(f"Content: {result[0]}")
        confirm = input("Are you sure you want to remove this tweet? (y/n): ").lower()
        if confirm == 'y':
            db.remove_tweet(tweet_id)
            print(f"{AnsiColor.OKGREEN}Tweet removed successfully.{AnsiColor.ENDC}")
        else:
            print(f"{AnsiColor.WARNING}Tweet removal cancelled.{AnsiColor.ENDC}")
    else:
        print(f"{AnsiColor.FAIL}Tweet not found.{AnsiColor.ENDC}")

def review_tweets():
    global db
    db = DBOperations()
    db.connect()

    while True:
        print(f"\n{AnsiColor.HEADER}{'=' * 50}\n--- Tweet Review Menu ---\n{'=' * 50}{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}1. Review pending tweets{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}2. Generate additional tweet{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}3. Generate 10 tweets in bulk{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}4. Create a new tweet{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}5. Edit a specific tweet{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}6. Remove a specific tweet{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}7. Display all tweets{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}8. Perform database maintenance{AnsiColor.ENDC}")
        print(f"{AnsiColor.BOLD}{AnsiColor.OKCYAN}9. Exit{AnsiColor.ENDC}")
        
        choice = input(f"{AnsiColor.HEADER}Enter your choice (1-9): {AnsiColor.ENDC}")

        if choice == '1':
            pending_tweets = db.get_pending_tweets()
            if not pending_tweets:
                print(f"{AnsiColor.FAIL}No pending tweets to review.{AnsiColor.ENDC}")
            else:
                for tweet_id, content in pending_tweets:
                    print(f"\n{AnsiColor.HEADER}{'=' * 50}\nTweet ID: {tweet_id}\n{'=' * 50}{AnsiColor.ENDC}")
                    print(f"Content: {content}")
                    action = input("Enter 'a' to authorize, 'r' to remove, 'e' to edit, or 's' to skip: ").lower()
                    
                    if action == 'a':
                        db.authorize_tweet(tweet_id)
                        print(f"{AnsiColor.OKGREEN}Tweet authorized.{AnsiColor.ENDC}")
                    elif action == 'r':
                        db.remove_tweet(tweet_id)
                        print(f"{AnsiColor.OKGREEN}Tweet removed.{AnsiColor.ENDC}")
                    elif action == 'e':
                        edit_tweet(tweet_id, content)
                    elif action == 's':
                        print(f"{AnsiColor.WARNING}Tweet skipped.{AnsiColor.ENDC}")
                    else:
                        print(f"{AnsiColor.FAIL}Invalid action. Tweet skipped.{AnsiColor.ENDC}")

        elif choice == '2':
            generate_additional_tweet()

        elif choice == '3':
            generate_bulk_tweets()

        elif choice == '4':
            create_new_tweet()

        elif choice == '5':
            display_all_tweets()
            tweet_id = input("Enter the ID of the tweet you want to edit (or 'c' to cancel): ")
            if tweet_id.lower() == 'c':
                continue
            db.cursor.execute("SELECT content FROM tweets WHERE id = ?", (tweet_id,))
            result = db.cursor.fetchone()
            if result:
                edit_tweet(tweet_id, result[0])
            else:
                print(f"{AnsiColor.FAIL}Tweet not found.{AnsiColor.ENDC}")

        elif choice == '6':
            remove_specific_tweet()

        elif choice == '7':
            display_all_tweets()

        elif choice == '8':
            perform_maintenance()

        elif choice == '9':
            print(f"{AnsiColor.OKBLUE}Exiting tweet review.{AnsiColor.ENDC}")
            break

        else:
            print(f"{AnsiColor.FAIL}Invalid choice. Please try again.{AnsiColor.ENDC}")

    db.close()
    print(f"{AnsiColor.OKBLUE}Review session ended.{AnsiColor.ENDC}")

if __name__ == "__main__":
    OpenAIClient.load_recent_topics()
    review_tweets()
