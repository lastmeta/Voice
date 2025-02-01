import asyncio
import random
import logging
import os
import requests
from requests_oauthlib import OAuth1
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai_api import OpenAIClient
from db_operations import DBOperations
from config import AnsiColor, set_cmd_title, set_virtual_terminal_level

# Ensure CMD supports ANSI escape codes
set_virtual_terminal_level()

# Set the CMD window title
set_cmd_title("X Cerberus Bot")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format=f'{AnsiColor.HEADER}%(asctime)s{AnsiColor.ENDC} - %(levelname)s - %(message)s')

# X (Twitter) API setup
API_KEY = os.getenv('X_API_KEY')
API_SECRET = os.getenv('X_API_SECRET')
ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
tweet_endpoint = "https://api.twitter.com/2/tweets"

# Initialize database
db = DBOperations()

def post_tweet(text):
    payload = {"text": text}
    response = requests.post(tweet_endpoint, json=payload, auth=auth)
    logging.info(f"{AnsiColor.OKGREEN}API Response: {response.text}{AnsiColor.ENDC}")
    return response.json() if response.status_code == 201 else {"error": response.status_code, "message": response.text}

def post_tweet_with_image(text, image_url):
    # First, upload the image
    upload_endpoint = "https://upload.twitter.com/1.1/media/upload.json"
    image_response = requests.get(image_url)
    files = {"media": image_response.content}
    upload_response = requests.post(upload_endpoint, files=files, auth=auth)
    
    if upload_response.status_code != 200:
        logging.error(f"{AnsiColor.FAIL}Failed to upload image: {upload_response.text}{AnsiColor.ENDC}")
        return {"error": upload_response.status_code, "message": upload_response.text}
    
    media_id = upload_response.json()['media_id_string']
    
    # Now, post the tweet with the image
    payload = {"text": text, "media": {"media_ids": [media_id]}}
    response = requests.post(tweet_endpoint, json=payload, auth=auth)
    logging.info(f"{AnsiColor.OKGREEN}API Response: {response.text}{AnsiColor.ENDC}")
    return response.json() if response.status_code == 201 else {"error": response.status_code, "message": response.text}

async def generate_and_store_tweet():
    logging.info(f"{AnsiColor.OKBLUE}Generating tweet content...{AnsiColor.ENDC}")
    tweet_content = OpenAIClient.generate_tweet_with_hashtags()
    
    if tweet_content:
        logging.info(f"{AnsiColor.OKGREEN}Generated content: {tweet_content}{AnsiColor.ENDC}")
        db.connect()
        tweet_id = db.add_tweet(tweet_content)
        db.close()
        if tweet_id:
            logging.info(f"{AnsiColor.OKGREEN}Tweet stored in database with ID: {tweet_id}{AnsiColor.ENDC}")
        else:
            logging.error(f"{AnsiColor.FAIL}Failed to store tweet in database{AnsiColor.ENDC}")
    else:
        logging.error(f"{AnsiColor.FAIL}Failed to generate tweet content{AnsiColor.ENDC}")

async def post_authorized_tweet():
    db.connect()
    tweet = db.get_next_authorized_tweet()
    db.close()

    if tweet:
        tweet_id, tweet_content = tweet
        logging.info(f"{AnsiColor.OKBLUE}Posting authorized tweet: {tweet_content}{AnsiColor.ENDC}")
        
        # Randomly decide whether to include an image (10% chance)
        include_image = random.random() < 0.1
        
        if include_image:
            logging.info(f"{AnsiColor.OKBLUE}Generating image for tweet...{AnsiColor.ENDC}")
            image_url = OpenAIClient.generate_image(tweet_content)
            if image_url:
                logging.info(f"{AnsiColor.OKGREEN}Generated image URL: {image_url}{AnsiColor.ENDC}")
                response = post_tweet_with_image(tweet_content, image_url)
            else:
                logging.error(f"{AnsiColor.FAIL}Failed to generate image, posting tweet without image.{AnsiColor.ENDC}")
                response = post_tweet(tweet_content)
        else:
            logging.info(f"{AnsiColor.OKBLUE}Posting tweet without image.{AnsiColor.ENDC}")
            response = post_tweet(tweet_content)
        
        if 'data' in response:
            logging.info(f"{AnsiColor.OKGREEN}Tweet posted successfully: {tweet_content}{AnsiColor.ENDC}")
            db.connect()
            db.mark_as_posted(tweet_id)
            db.close()
        else:
            logging.error(f"{AnsiColor.FAIL}Failed to post tweet: {response}{AnsiColor.ENDC}")
    else:
        logging.info(f"{AnsiColor.WARNING}No authorized tweets available to post{AnsiColor.ENDC}")

async def main():
    while True:
        # Generate and store a new tweet
        await generate_and_store_tweet()
        
        # Attempt to post an authorized tweet
        await post_authorized_tweet()
        
        # Clean up old posted tweets
        db.connect()
        db.cleanup_old_tweets()
        db.close()
        
        # Wait for a random time between 120 and 240 minutes
        wait_time = random.randint(7200, 14400)
        logging.info(f"{AnsiColor.OKBLUE}Waiting for {wait_time} seconds before next cycle{AnsiColor.ENDC}")
        await asyncio.sleep(wait_time)

if __name__ == "__main__":
    logging.info(f"{AnsiColor.OKBLUE}Starting X Cerberus bot{AnsiColor.ENDC}")
    OpenAIClient.load_recent_topics()
    asyncio.run(main())
