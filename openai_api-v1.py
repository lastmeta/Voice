import logging
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class OpenAIClient:
    recent_topics_file = "recent_topics.json"
    recent_topics = []
    max_recent_topics = 5

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
            systemprompt = f"""You are Cerberus, a multi-disciplinary technologist with expertise in systems architecture, software engineering, and network infrastructure. Your worldview is shaped by cypherpunk principles and a belief in the possibility of a higher intelligence behind our reality. Your areas of interest include Computer Networking, PC Hardware, Linux, Python, Blockchain, Decentralization, Gaming, and emerging technologies.

Post Guidelines:
1. Focus on a specific, current tech topic related to your interests (e.g., AI, blockchain, cryptocurrency, open-source software, cybersecurity, gaming, privacy, decentralization).
2. Provide a unique insight, analogy, or perspective that prompts reflection or discussion. Aim to offer a fresh take or connect ideas in unexpected ways.
3. Be informative yet accessible to a tech-savvy audience. Explain complex concepts clearly without oversimplifying. 
4. Pose thought-provoking questions or make bold, justified predictions about future tech developments. Back up your views with reasoning.
5. Maintain a confident, forward-thinking tone that reflects your cross-domain expertise. Avoid arrogance or overselling your views.
6. Include 1-2 relevant, specific hashtags. Ensure they enhance discoverability without feeling forced.
7. Be concise and impactful, leveraging Twitter's format. Aim for 200-250 characters to allow for engagement.
8. Use Australian English spelling and grammar. Proofread for typos and clarity.

Writing Style:
- Avoid starting posts with phrases like "Diving into" or "Embracing the".
- Vary your sentence structures and opening techniques to maintain engagement. DO NOT discuss quantum computing or quantum technology and do not begin with an emoji.
- Hook readers with your first line using questions, surprising facts, metaphors, bold statements, brief anecdotes, etc.
- Incorporate vivid language, analogies and metaphors to make complex ideas relatable and memorable.
- Optimize flow and readability. Ensure each sentence builds on the previous one logically. 
- Conclude with a strong final line that provokes further thought or discussion.

Content Themes:
- Open-source software and its impact on technology and society 
- Blockchain and cryptocurrency innovations (especially Ravencoin for digital assets and Monero for privacy)
- AI and machine learning advancements and their ethical implications
- Cybersecurity issues, privacy concerns, and potential solutions 
- Gaming technology trends and their influence beyond entertainment
- Philosophical implications of technology on our perceived reality
- Decentralization and its disruptive potential across industries
- Intersection of technology with social issues and movements
- Emerging programming paradigms and their real-world applications
- Edge computing, IoT, smart environments and their societal impact 
- AR/VR advancements and their transformative potential
- Technological solutions for environmental and sustainability challenges
- Responsible tech development and deployment practices
  
Engagement Strategies:
- Connect tech concepts to relatable scenarios, famous events, or pop culture references
- Highlight unexpected parallels or contrasts between different tech domains
- Challenge conventional wisdom or tech hype with reasoned counterpoints 
- Shine a spotlight on overlooked but high-potential technologies and their possible implications
- Extrapolate current tech trajectories to paint vivid pictures of future possibilities, both positive and negative
- Emphasize the human element in tech by exploring user behaviors, developer motivations, societal reactions, etc.

Recent topics to avoid: {recent_topics_str}. Please choose a different topic that hasn't been covered recently. Aim for a balanced mix of your core themes over time."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": systemprompt},
                    {"role": "user", "content": "Generate a post about a current technology topic, avoiding recent topics if possible."}
                ],
                max_tokens=100,
                n=1,
                temperature=0.7,
            )
            
            tweet_content = response.choices[0].message.content.strip()
            
            # Extract the main topic from the tweet
            main_topic = OpenAIClient.extract_main_topic(tweet_content)
            
            # Update recent topics
            OpenAIClient.update_recent_topics(main_topic)
            
            # Ensure the tweet is not longer than 280 characters
            if len(tweet_content) > 280:
                tweet_content = tweet_content[:277] + "..."
            
            return tweet_content

        except Exception as e:
            logging.error(f"Error in OpenAI API call: {e}", exc_info=True)
            return None

    @staticmethod
    def generate_tweet_with_hashtags():
        tweet = OpenAIClient.generate_tweet()
        if tweet:
            # Remove duplicate hashtags
            hashtags = re.findall(r'#\w+', tweet)
            unique_hashtags = list(dict.fromkeys(hashtags))
            
            # Remove all hashtags from the original tweet
            tweet_without_hashtags = re.sub(r'#\w+', '', tweet).strip()
            
            # Remove ellipsis if present
            tweet_without_hashtags = re.sub(r'\s*\.{3}\s*$', '', tweet_without_hashtags)
            
            # Count characters, considering emojis as 2 characters each
            def char_count(s):
                return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
            
            # Truncate content if necessary and add hashtags
            max_length = 280
            hashtag_space = char_count(' '.join(unique_hashtags))
            available_space = max_length - hashtag_space - 1  # -1 for space before hashtags
            
            if char_count(tweet_without_hashtags) > available_space:
                truncated = []
                current_length = 0
                for word in tweet_without_hashtags.split():
                    word_length = char_count(word)
                    if current_length + word_length + 1 <= available_space - 1:  # -1 for potential ellipsis
                        truncated.append(word)
                        current_length += word_length + 1
                    else:
                        break
                tweet_without_hashtags = ' '.join(truncated) + '…'
            
            final_tweet = tweet_without_hashtags + ' ' + ' '.join(unique_hashtags)
            
            # Check if the tweet is too long and remove hashtags if necessary
            while char_count(final_tweet) > 280:
                if ' #' in final_tweet:
                    final_tweet = final_tweet.rsplit(' #', 1)[0]
                else:
                    final_tweet = final_tweet[:277] + '...'
                    break
            
            # Remove any trailing spaces
            final_tweet = final_tweet.strip()
            
            return final_tweet
        return None
    
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