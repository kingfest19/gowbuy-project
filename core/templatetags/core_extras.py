from django import template
import re

register = template.Library()

@register.filter(name='get_embed_url')
def get_embed_url(video_url):
    if not video_url:
        return ""

    # Try to extract YouTube video ID
    # Handles URLs like:
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    # - https://www.youtube.com/embed/VIDEO_ID (already an embed link)
    youtube_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)",
        r"(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]+)",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)"
    ]
    for pattern in youtube_patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

    # Try to extract Vimeo video ID
    # Handles URLs like:
    # - https://vimeo.com/VIDEO_ID
    # - https://player.vimeo.com/video/VIDEO_ID (already an embed link)
    vimeo_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/([0-9]+)",
        r"(?:https?:\/\/)?player\.vimeo\.com\/video\/([0-9]+)"
    ]
    for pattern in vimeo_patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            return f"https://player.vimeo.com/video/{video_id}"

    return "" # Return empty if no known pattern matches, or original URL if preferred
