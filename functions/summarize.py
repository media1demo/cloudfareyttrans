# your-youtube-summarizer/functions/summarize.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
# from cloudflare.workers.types import Response # For explicit Response object

# Import your utility functions
# Since app_utils.py is in the parent directory of 'functions/',
# we need to adjust the Python path or use relative imports if structured as a package.
# For Cloudflare Functions, they often run with the project root in sys.path.
# So a direct import might work:
import app_utils # This assumes app_utils.py is discoverable (e.g. project root is in sys.path)
                 # If not, you might need to adjust sys.path (less ideal) or structure differently.
                 # Let's try direct import first, common for CF Pages Functions.


# Determine the correct path to the 'templates' directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
# If the above doesn't work try:
# TEMPLATES_DIR = 'templates' # If functions CWD is project root

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name, **context):
    template = env.get_template(template_name)
    return template.render(**context)

# This function will be called for POST requests to the path matching the file name (i.e., /summarize)
async def onRequestPost(context):
    request = context.request
    form_data = await request.formData() #formData() is async
    video_url = form_data.get('video_url', '').strip()

    summary_text = None
    error_msg = None
    fetched_text_content = None

    if not video_url:
        error_msg = "Please enter a YouTube video URL."
    else:
        video_id = app_utils.extract_video_id(video_url)
        if not video_id:
            error_msg = "Invalid YouTube URL or could not extract Video ID. Please use a valid format (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)."
        else:
            app_utils.logger.info(f"Processing video ID: {video_id}") # Use the logger from app_utils
            fetched_text_content, error_msg_from_fetch = app_utils.get_transcript_text(video_id)

            if error_msg_from_fetch:
                error_msg = error_msg_from_fetch
            elif fetched_text_content:
                summary_text = app_utils.basic_summarizer(fetched_text_content)
                # Since basic_summarizer returns the full text, summary_text is the transcript.
                # The template uses 'summary' for the main text display.
                if not summary_text and not error_msg:
                    error_msg = "Could not generate summary from the transcript."
            elif not error_msg:
                 error_msg = "Could not retrieve transcript for the video (no text content)."

    html_content = render_template('index.html',
                                   summary=summary_text, # This will be the full transcript
                                   error_message=error_msg,
                                   video_url_input=video_url,
                                   full_transcript=fetched_text_content if error_msg and fetched_text_content else None) # This condition might be redundant
    
    return Response(html_content, headers={'Content-Type': 'text/html'})


# Fallback for any method if you only want one handler for this path
async def onRequest(context):
    if context.request.method == "POST":
        return await onRequestPost(context)
    else:
        # Method Not Allowed
        return Response("Method Not Allowed", status=405)
