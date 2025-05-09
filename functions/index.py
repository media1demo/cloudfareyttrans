# your-youtube-summarizer/functions/index.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os # To construct paths reliably

# Cloudflare Pages Functions can return a Response object or just HTML string
# For explicit control, use Response.
# from cloudflare.workers.types import Response # Not strictly needed if just returning string

# Determine the correct path to the 'templates' directory.
# When deployed, functions run from the project root.
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

# This function will be called for GET requests to the path matching the file name (i.e., /)
# Cloudflare provides context, from which we can get the request.
async def onRequestGet(context):
    # context.request contains the Request object
    # context.env contains bindings (secrets, KV stores, etc.)
    # context.next() calls the next function in the chain (for middleware)
    # context.data can be used to pass data between middleware functions
    
    html_content = render_template('index.html', 
                                   summary=None, 
                                   error_message=None, 
                                   video_url_input='',
                                   full_transcript=None)
    return Response(html_content, headers={'Content-Type': 'text/html'})

# Fallback for any method if you only want one handler for this path
async def onRequest(context):
    if context.request.method == "GET":
        return await onRequestGet(context)
    else:
        # Method Not Allowed
        return Response("Method Not Allowed", status=405)
