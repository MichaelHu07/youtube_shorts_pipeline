"""
Reddit client for fetching posts from subreddits
"""
import praw
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import Config
from config.pipeline_config import PipelineConfig
from config.logging_config import get_logger
from src.utils import save_json_file, generate_timestamped_filename, ensure_directory

logger = get_logger('reddit_fetcher')

class RedditClient:
    def __init__(self):
        """Initialize Reddit client"""
        try:
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise
    
    def fetch_top_post(self, subreddit_name: Optional[str] = None, time_filter: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch top post from specified subreddit or randomly selected subreddit
        
        Args:
            subreddit_name: Name of subreddit (if None, randomly selects from TARGET_SUBREDDITS)
            time_filter: Time filter for top posts (uses config default if None)
        
        Returns:
            Dictionary containing post data or None if failed
        """
        if time_filter is None:
            time_filter = PipelineConfig.TIME_FILTER
        
        # If no subreddit specified, randomly select from configured list
        if subreddit_name is None:
            subreddit_name = random.choice(PipelineConfig.TARGET_SUBREDDITS)
            logger.info(f"Randomly selected subreddit: r/{subreddit_name}")
            
        try:
            logger.info(f"Fetching top post from r/{subreddit_name} (filter: {time_filter})")
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get top posts using config limit
            top_posts = list(subreddit.top(time_filter=time_filter, limit=PipelineConfig.FETCH_POST_LIMIT))
            
            # Filter for text posts that are suitable for narration
            suitable_posts = [post for post in top_posts if self._is_suitable_post(post)]
            
            if not suitable_posts:
                logger.warning(f"No suitable posts found in r/{subreddit_name}")
                return None
            
            # Sort by score to get highest quality posts first
            suitable_posts.sort(key=lambda p: p.score, reverse=True)
            
            # Randomly select from top N highest scoring posts using config
            top_sample_size = min(PipelineConfig.TOP_SAMPLE_SIZE, len(suitable_posts))
            top_posts_sample = suitable_posts[:top_sample_size]
            selected_post = random.choice(top_posts_sample)
            
            if PipelineConfig.REPORT_SELECTION_STATS:
                logger.info(f"Randomly selected post with score {selected_post.score} from top {top_sample_size} posts (out of {len(suitable_posts)} suitable)")
            
            post_data = self._extract_post_data(selected_post)
            
            # Save post data using utility function
            self._save_post_data(post_data)
            
            logger.info(f"Successfully fetched post: {post_data['title'][:50]}...")
            return post_data
            
        except Exception as e:
            logger.error(f"Failed to fetch post from r/{subreddit_name}: {e}")
            return None
    
    def _is_suitable_post(self, post) -> bool:
        """Check if post is suitable for narration using config settings"""
        # Check if post has substantial text content
        if not post.selftext or len(post.selftext.strip()) < PipelineConfig.MIN_POST_LENGTH:
            return False
        
        # Check maximum length if configured
        if PipelineConfig.MAX_POST_LENGTH and len(post.selftext.strip()) > PipelineConfig.MAX_POST_LENGTH:
            return False
        
        # Check estimated video duration
        word_count = len(post.selftext.split())
        estimated_duration = PipelineConfig.get_duration_estimate(word_count)
        
        if estimated_duration < PipelineConfig.MIN_VIDEO_DURATION:
            return False
        
        # Check maximum duration if configured
        if PipelineConfig.MAX_VIDEO_DURATION is not None and estimated_duration > PipelineConfig.MAX_VIDEO_DURATION:
            return False
        
        # Check upvote threshold
        if post.score < PipelineConfig.MIN_UPVOTES:
            return False
        
        # Check NSFW filter
        if not PipelineConfig.ALLOW_NSFW and post.over_18:
            return False
            
        # Check deleted authors
        if PipelineConfig.EXCLUDE_DELETED_AUTHORS and (not post.author or str(post.author) == '[deleted]'):
            return False
        
        return True
    
    def _extract_post_data(self, post) -> Dict:
        """Extract relevant data from Reddit post"""
        return {
            'id': post.id,
            'title': post.title,
            'selftext': post.selftext,
            'author': str(post.author) if post.author else '[deleted]',
            'subreddit': str(post.subreddit),
            'score': post.score,
            'num_comments': post.num_comments,
            'created_utc': post.created_utc,
            'url': post.url,
            'permalink': f"https://reddit.com{post.permalink}",
            'fetched_at': datetime.now().isoformat(),
            'estimated_duration': PipelineConfig.get_duration_estimate(len(post.selftext.split()))
        }
    
    def _save_post_data(self, post_data: Dict) -> str:
        """Save post data using utility function"""
        ensure_directory(Config.REDDIT_POSTS_DIR)
        
        if PipelineConfig.INCLUDE_POST_ID_IN_FILENAMES:
            filename = generate_timestamped_filename('reddit_post', 'json', post_data['id'])
        else:
            filename = generate_timestamped_filename('reddit_post', 'json')
            
        filepath = os.path.join(Config.REDDIT_POSTS_DIR, filename)
        
        save_json_file(post_data, filepath)
        return filepath
    
    def create_narration_script(self, post_data: Dict) -> str:
        """Create a narration script from post data using config settings"""
        title = post_data['title']
        content = post_data['selftext']
        
        # Clean up the content if configured
        if PipelineConfig.CLEAN_REDDIT_FORMATTING:
            content = self._clean_text_for_narration(content)
        
        # Build script parts based on config
        script_parts = []
        
        # Add title if configured
        if PipelineConfig.ADD_INTRO_PHRASE and PipelineConfig.INCLUDE_TITLE_IN_SCRIPT:
            script_parts.append(f"{title}")
            script_parts.append("")  # Pause
        elif PipelineConfig.INCLUDE_TITLE_IN_SCRIPT:
            script_parts.append(title)
            script_parts.append("")  # Pause
        
        # Add content
        script_parts.append(content)
        
        # Add outro if configured
        if PipelineConfig.ADD_OUTRO_PHRASE:
            script_parts.append("")  # Pause
            script_parts.append(PipelineConfig.OUTRO_TEXT)
        
        script = " ".join(script_parts)
        
        # Save script if using timestamped filenames
        if PipelineConfig.USE_TIMESTAMPED_FILENAMES:
            if PipelineConfig.INCLUDE_POST_ID_IN_FILENAMES:
                script_filename = generate_timestamped_filename('script', 'txt', post_data['id'])
            else:
                script_filename = generate_timestamped_filename('script', 'txt')
                
            script_filepath = os.path.join(Config.REDDIT_POSTS_DIR, script_filename)
            
            try:
                with open(script_filepath, 'w', encoding='utf-8') as f:
                    f.write(script)
                logger.info(f"Narration script saved to: {script_filepath}")
            except Exception as e:
                logger.error(f"Failed to save script: {e}")
        
        return script
    
    def _clean_text_for_narration(self, text: str) -> str:
        """Clean text for better narration using config settings"""
        if not PipelineConfig.CLEAN_REDDIT_FORMATTING:
            return text
            
        # Remove Reddit formatting
        text = text.replace('&amp;', 'and')
        text = text.replace('&lt;', 'less than')
        text = text.replace('&gt;', 'greater than')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Replace common abbreviations if configured
        if PipelineConfig.EXPAND_ABBREVIATIONS:
            replacements = {
                'AITA': 'Am I the asshole',
                'NTA': 'Not the asshole',
                'YTA': 'You are the asshole',
                'ESH': 'Everyone sucks here',
                'NAH': 'No assholes here',
                'INFO': 'I need more information',
                'SO': 'significant other',
                'BF': 'boyfriend',
                'GF': 'girlfriend',
                'DH': 'dear husband',
                'DW': 'dear wife',
                'MIL': 'mother in law',
                'FIL': 'father in law',
                'SIL': 'sister in law',
                'BIL': 'brother in law'
            }
            
            for abbrev, full_form in replacements.items():
                text = text.replace(abbrev, full_form)
        
        return text
    
    def fetch_post_by_url(self, reddit_url: str) -> Optional[Dict]:
        """
        Fetch a specific Reddit post by URL
        
        Args:
            reddit_url: Full Reddit post URL (e.g., https://www.reddit.com/r/nosleep/comments/abc123/title/)
        
        Returns:
            Dictionary containing post data or None if failed
        """
        try:
            # Extract post ID from URL
            post_id_match = re.search(r'/comments/([a-zA-Z0-9]+)/', reddit_url)
            if not post_id_match:
                logger.error(f"Could not extract post ID from URL: {reddit_url}")
                return None
            
            post_id = post_id_match.group(1)
            logger.info(f"Fetching specific post by ID: {post_id}")
            
            # Get the post directly
            post = self.reddit.submission(id=post_id)
            
            # Validate it's suitable for narration
            if not self._is_suitable_post(post):
                logger.warning(f"Post {post_id} is not suitable for narration")
                return None
            
            post_data = self._extract_post_data(post)
            self._save_post_data(post_data)
            
            logger.info(f"Successfully fetched manual post: {post_data['title'][:50]}...")
            return post_data
            
        except Exception as e:
            logger.error(f"Failed to fetch post from URL {reddit_url}: {e}")
            return None 