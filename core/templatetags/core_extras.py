from django import template
import re

register = template.Library()

@register.filter
def get_embed_url(url):
    """
    Converts a YouTube or Vimeo URL to an embeddable URL.
    Returns None if the URL is not recognized or cannot be embedded.
    """
    if not url:
        return None

    # YouTube regex
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    match = re.match(youtube_regex, url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(6)}"

    # Vimeo regex
    vimeo_regex = r'(https?://)?(www\.)?(player\.)?vimeo\.com/(video/)?(\d+)(/?.*)'
    match = re.match(vimeo_regex, url)
    if match:
        return f"https://player.vimeo.com/video/{match.group(5)}"

    return None # Not a recognized embeddable video URL