import logging
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
import random

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class OpenAIClient:
    recent_topics_file = "recent_topics.json"
    recent_topics = []
    max_recent_topics = 10
    MAX_TWEET_LENGTH = 2000

    @staticmethod
    def load_recent_topics():
        try:
            with open(OpenAIClient.recent_topics_file, 'r') as f:
                OpenAIClient.recent_topics = json.load(f)
        except FileNotFoundError:
            OpenAIClient.recent_topics = []

    @staticmethod
    def save_recent_topics():
        with open(OpenAIClient.recent_topics_file, 'w') as f:
            json.dump(OpenAIClient.recent_topics, f)

    @staticmethod
    def update_recent_topics(topic):
        if topic not in OpenAIClient.recent_topics:
            OpenAIClient.recent_topics.append(topic)
            if len(OpenAIClient.recent_topics) > OpenAIClient.max_recent_topics:
                OpenAIClient.recent_topics.pop(0)
        OpenAIClient.save_recent_topics()

    @staticmethod
    def extract_main_topic(tweet):
        hashtags = re.findall(r'#(\w+)', tweet)
        return hashtags[0] if hashtags else "Unknown"

    @staticmethod
    def generate_tweet():
        try:
            recent_topics_str = ", ".join(OpenAIClient.recent_topics)
            
            # Define a list of content themes
            content_themes = [
                "Decentralization and its potential to disrupt traditional power structures",
                "Blockchain and cryptocurrency innovations for a more equitable future",
                "Cybersecurity and privacy: Safeguarding individual rights in a digital age",
                "Gaming technology: Pioneering new frontiers in immersive experiences",
                "Open-source software as a catalyst for technological and societal change",
                "AI and machine learning: Balancing transformative potential with ethical risks",
                "Cypherpunk philosophy and its ongoing relevance in shaping technology",
                "Technology's impact on the nature of reality and human perception",
                "Leveraging tech innovations to solve global sustainability challenges",
                "Empowering individuals through decentralized tools and platforms",
                "Emerging tech (IoT, edge computing) and its influence on daily life",
                "Fostering community and collaboration in gaming and tech spaces",
                "Reflecting on technology's societal impact through a cypherpunk lens",
                "Imagining alternative futures shaped by decentralized technologies"
            ]
            
            # Randomly select a content theme
            selected_theme = random.choice(content_themes)
            
            systemprompt = f"""You are Cerberus, a cypherpunk technologist with deep expertise in decentralization, blockchain, gaming, and emerging tech. With a background in networking, hardware, and software engineering, you bring a pragmatic yet visionary perspective to your content.

Post Guidelines:
1. Focus on the following tech topic: {selected_theme}
2. Aim for approximately 250-300 characters, including spaces and punctuation.
3. Offer unique insights that challenge conventional thinking and spark discussion
4. Explain complex ideas clearly, balancing depth with accessibility 
5. Make bold, reasoned predictions about future tech developments
6. Write with confidence, reflection, and a cypherpunk point of view
7. Include 1-2 specific, relevant hashtags
8. Aim for concise content, optimized for engagement
9. Use Australian English spelling and grammar. Proofread for typos and clarity.

Writing Style:
- Vary your opening techniques to hook readers; avoid repetitive phrases like "Exploring," "Unveiling," "Unleashing," "Diving into," or starting with an emoji.
- Hook readers with your first line using questions, surprising facts, metaphors, bold statements, brief anecdotes, etc.
- Incorporate vivid language, analogies and metaphors to make complex ideas relatable and memorable.
- Optimize flow and readability. Ensure each sentence builds on the previous one logically. 
- Conclude with a strong final line that provokes further thought or discussion.
- Mix up your sentence structures and lengths to create a dynamic, engaging rhythm.

Engagement Strategies:
- Connect tech to relatable scenarios and cultural touchstones
- Highlight surprising parallels and contrasts across domains
- Challenge conventional wisdom or tech hype with reasoned counterpoints 
- Explore tech's impact on individuals, communities, and society
- Extrapolate current tech trajectories to paint vivid pictures of future possibilities, both positive and negative
- Emphasize the human element in tech by exploring user behaviors, developer motivations, societal reactions, etc.
- Occasionally pose questions or polls to invite interaction

Recent topics to avoid: {recent_topics_str}. Please choose a different topic that hasn't been covered recently. Aim for a balanced mix of your core themes over time."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": systemprompt},
                    {"role": "user", "content": f"Generate a post about {selected_theme}, avoiding recent topics if possible."}
                ],
                max_tokens=100,
                n=1,
                temperature=0.8,
            )
            
            tweet_content = response.choices[0].message.content.strip()
            
            main_topic = OpenAIClient.extract_main_topic(tweet_content)
            OpenAIClient.update_recent_topics(main_topic)
            
            return tweet_content

        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}", exc_info=True)
            return None

    @staticmethod
    def generate_tweet_with_hashtags():
        tweet = OpenAIClient.generate_tweet()
        if tweet:
            # Check if the tweet already has hashtags
            if not re.search(r'#\w+', tweet):
                # If no hashtags, generate and append them
                hashtags = OpenAIClient.generate_hashtags(tweet)
                tweet = tweet.rstrip('.') + ' ' + ' '.join(hashtags)

            # Ensure the tweet is not longer than MAX_TWEET_LENGTH characters
            if len(tweet) > OpenAIClient.MAX_TWEET_LENGTH:
                tweet = tweet[:OpenAIClient.MAX_TWEET_LENGTH - 3] + "..."
            
            return tweet
        return None
    
    @staticmethod
    def generate_hashtags(tweet_content, num_hashtags=3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate relevant hashtags for the given tweet content."},
                    {"role": "user", "content": f"Generate {num_hashtags} relevant hashtags for this tweet:\n\n{tweet_content}"}
                ],
                max_tokens=30,
                n=1,
                temperature=0.7,
            )
            hashtags = response.choices[0].message.content.strip().split()
            return [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags]
        except Exception as e:
            logging.error(f"Error generating hashtags: {e}", exc_info=True)
            return ['#tech', '#innovation', '#future']  # Fallback hashtags
    
    @staticmethod
    def generate_image(prompt):
        if not prompt.strip():
            logging.warning("Empty prompt provided for image generation")
            return None
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"Create an image representing the following tech concept: {prompt}",
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            return image_url
        except Exception as e:
            logging.error(f"Error in OpenAI image generation: {e}", exc_info=True)
            return None

# Load recent topics when the module is imported
OpenAIClient.load_recent_topics()

if __name__ == "__main__":
    # Test the tweet and image generation
    tweet = OpenAIClient.generate_tweet_with_hashtags()
    print("Generated Tweet:", tweet)
    if tweet:
        image_url = OpenAIClient.generate_image(tweet)
        print("Generated Image URL:", image_url)