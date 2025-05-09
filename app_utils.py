# your-youtube-summarizer/app_utils.py
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import re
import logging # Using standard logging

# Configure a simple logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Cloudflare Functions will print this to logs


def extract_video_id(url):
    if not url:
        return None
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript_text(video_id):
    """Fetches and concatenates transcript text."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        
        # Try to find a manually created transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except NoTranscriptFound:
            logger.info(f"No manual English transcript for {video_id}. Trying generated.")
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except NoTranscriptFound:
                logger.warning(f"No generated English transcript for {video_id}. Trying any available.")
                available_langs = transcript_list.available_languages
                if available_langs:
                    for lang_code in [lang['language_code'] for lang in available_langs]:
                        try:
                            transcript = transcript_list.find_generated_transcript([lang_code])
                            logger.info(f"Using transcript in language: {lang_code} for {video_id}")
                            break
                        except NoTranscriptFound:
                            continue
                if not transcript:
                    return None, "No transcripts found for this video in any language."

        fetched_transcript_segments = transcript.fetch()
        full_text = " ".join([segment['text'] for segment in fetched_transcript_segments]) # Original code used dict access. If it's obj, it's segment.text
        # Re-checking your original code:
        # It says: "# The error indicates 'segment' is an object, so we use attribute access '.text'"
        # So it should be:
        # full_text = " ".join([segment.text for segment in fetched_transcript_segments])
        # However, the youtube_transcript_api.fetch() usually returns a list of dicts.
        # Let's stick to dict access as it's more common with the library.
        # If you indeed get objects, change segment['text'] to segment.text.
        # For safety, let's try to be robust:
        processed_segments = []
        for segment in fetched_transcript_segments:
            if isinstance(segment, dict) and 'text' in segment:
                processed_segments.append(segment['text'])
            elif hasattr(segment, 'text'):
                processed_segments.append(segment.text)
            else:
                logger.warning(f"Unexpected segment format: {segment}")
        full_text = " ".join(processed_segments)

        return full_text, None
        
    except TranscriptsDisabled:
        logger.warning(f"Transcripts disabled for video {video_id}")
        return None, "Transcripts are disabled for this video."
    except NoTranscriptFound:
        logger.warning(f"No transcript found for video {video_id} after all attempts.")
        return None, "No transcript found for this video."
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        return None, f"An unexpected error occurred: {str(e)}"

def basic_summarizer(text):
    if not text:
        return ""
    # Your original summarizer returns the full text.
    # If you want a "summary", you might take the first N words/sentences.
    # For now, keeping it as is:
    return text
