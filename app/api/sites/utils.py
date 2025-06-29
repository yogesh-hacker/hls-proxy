from base64 import b64encode
from urllib.parse import quote, urlparse
import json
from . import site_domains as s

def isDict(value):
    return isinstance(value, dict)

def proxify(value, request):
    media_urls = value
    current_domain = request.build_absolute_uri('/')[:-1]

    for media in media_urls:
        tag = media.get('tag', '')
        encoded_url = None
        if media.get('streaming_url') and media.get('streaming_url') != 'null':
            encoded_url = quote(b64encode(str(media.get('streaming_url', '')).encode()).decode())
            proxied_url = f"{current_domain}/proxy/?url={encoded_url}&server={tag}"
            media['streaming_url'] = proxied_url
        else:
            media['streaming_url'] = None 

    return media_urls

def get_headers(server_name):
    return {
        'Referer': s.get_domain(server_name)
    }

def get_domain(url):
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    domain = parsed.netloc

    return f"{scheme}://{domain}/"