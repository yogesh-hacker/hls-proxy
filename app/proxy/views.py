import requests
from django.http import StreamingHttpResponse, JsonResponse
from urllib.parse import urlparse, urljoin, quote, unquote
import time
import m3u8
from django.contrib.sites.shortcuts import get_current_site
from base64 import b64decode
from ..api.sites import utils

HEADERS = None

HOP_BY_HOP_HEADERS = {
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailer', 'transfer-encoding', 'upgrade'
}

# Helper Functions
def safe_b64decode(value):
    try:
        return b64decode(unquote(value)).decode()
    except Exception:
        return unquote(value) 


def remove_hop_by_hop_headers(response):
    """Remove hop-by-hop headers from the response."""
    for header in HOP_BY_HOP_HEADERS:
        if header in response.headers:
            del response.headers[header]
    return response

def get_domain(request):
    current_site = get_current_site(request)
    return f"{request.scheme}://{current_site.domain}"

def generate_m3u8(playlist_items, is_master=False):
    m3u8_content = "#EXTM3U\n"

    if is_master:
        m3u8_content += "#EXT-X-VERSION:3\n"
        for item in playlist_items:
            if item.get("type") == "audio":
                m3u8_content += f"#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"audio\",NAME=\"Audio\",URI=\"{item['uri']}\"\n"
            else:
                m3u8_content += (
                    f"#EXT-X-STREAM-INF:BANDWIDTH={item['bandwidth']},RESOLUTION={item.get('resolution', (0, 0))[0]}x{item.get('resolution', (0, 0))[1]},AUDIO=\"audio\"\n"
                    f"{item['uri']}\n"
                )
    else:
        m3u8_content += "#EXT-X-TARGETDURATION:10\n#EXT-X-ALLOW-CACHE:YES\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:1\n"
        for item in playlist_items:
            if "#EXT-X-MAP" in item['info']:
                m3u8_content += f"{item['info']}\n"
            else:
                m3u8_content += f"{item['info']}\n{item['uri']}\n"
        
        m3u8_content += "#EXT-X-ENDLIST\n"

    return m3u8_content

def proxy_view(request):
    """Entry point for master and media playlists (video & audio)."""
    start_time = time.time()
    encoded_url = request.GET.get('url', '')
    server = request.GET.get('server', '')
    HEADERS = utils.get_headers(server)
    hls_url = safe_b64decode(encoded_url)

    # Fetch the M3U8 playlist
    playlist_response = requests.get(hls_url, headers=HEADERS)
    m3u8_playlist = m3u8.loads(playlist_response.text)
    
    playlist_items = []
    is_master = m3u8_playlist.is_variant  

    if is_master:
        # Handling master playlist with multiple resolutions and audio
        for variant in m3u8_playlist.playlists:
            uri = variant.uri
            complete_url = uri if bool(urlparse(uri).netloc) else urljoin(hls_url, uri)
            proxied_url = f"{get_domain(request)}/proxy/?server={server}&url={quote(complete_url)}"
            playlist_items.append({
                'uri': proxied_url,
                'resolution': variant.stream_info.resolution,
                'bandwidth': variant.stream_info.bandwidth
            })

        # Handling audio-only streams
        for media in m3u8_playlist.media:
            if media.type == "AUDIO":
                complete_url = media.uri if bool(urlparse(media.uri).netloc) else urljoin(hls_url, media.uri)
                proxied_url = f"{get_domain(request)}/proxy/?server={server}&url={quote(complete_url)}"
                playlist_items.append({
                    'uri': proxied_url,
                    'type': 'audio'
                })

    else:
    # Handle init segment if present
        if m3u8_playlist.segments and m3u8_playlist.segment_map:
            init_segment_uri = m3u8_playlist.segment_map[0].uri
            complete_init_url = init_segment_uri if bool(urlparse(init_segment_uri).netloc) else urljoin(hls_url, init_segment_uri)
            proxied_init_url = f"{get_domain(request)}/proxy/stream/?server={server}&ts_url={quote(complete_init_url)}"
            playlist_items.append({
                'info': f"#EXT-X-MAP:URI=\"{proxied_init_url}\"",
                'uri': ''
            })

        for segment in m3u8_playlist.segments:
            complete_url = segment.uri if bool(urlparse(segment.uri).netloc) else urljoin(hls_url, segment.uri)
            proxied_url = f"{get_domain(request)}/proxy/stream/?server={server}&ts_url={quote(complete_url)}"
            playlist_items.append({
                'info': f"#EXTINF:{segment.duration},",
                'uri': proxied_url
            })

    # Generate playlist with updated URLs
    m3u8_content = generate_m3u8(playlist_items, is_master=is_master)

    response = StreamingHttpResponse(m3u8_content, content_type="application/vnd.apple.mpegurl")
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Content-Security-Policy'] = "default-src * data: blob: 'unsafe-inline' 'unsafe-eval'"
    
    return remove_hop_by_hop_headers(response)


# Entry point for TS segments
def stream_ts(request):
    ts_url = request.GET.get('ts_url')
    server = request.GET.get('server', '')
    HEADERS = utils.get_headers(server)

    if not ts_url:
        return JsonResponse({"error": "Missing ts_url parameter"}, status=400)

    decoded_url = unquote(ts_url)

    # Add Range support from client
    range_header = request.META.get('HTTP_RANGE')
    if range_header:
        HEADERS['Range'] = range_header

    try:
        response = requests.get(decoded_url, stream=True, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Determine correct Content-Type
        if decoded_url.endswith('.m4s'):
            content_type = 'video/iso.segment'
        elif decoded_url.endswith('.mp4') or 'init' in decoded_url:
            content_type = 'video/mp4'
        else:
            content_type = response.headers.get('Content-Type', 'video/mp2t')

        # Build headers
        excluded_headers = {'content-encoding', 'transfer-encoding', 'content-type'}
        response_headers = {
            k: v for k, v in response.headers.items() if k.lower() not in excluded_headers
        }

        # Required streaming headers
        if 'Content-Length' in response.headers:
            response_headers['Content-Length'] = response.headers['Content-Length']
        if 'Content-Range' in response.headers:
            response_headers['Content-Range'] = response.headers['Content-Range']

        # CORS + streaming headers
        response_headers['Access-Control-Allow-Origin'] = '*'
        response_headers['Access-Control-Allow-Headers'] = 'Range'
        response_headers['Accept-Ranges'] = 'bytes'

        # Prepare the response
        streaming_response = StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=4096),
            content_type=content_type,
            status=206 if 'Content-Range' in response.headers else 200,
            headers=response_headers
        )

        return remove_hop_by_hop_headers(streaming_response)

    except requests.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"HTTP error: {e}"}, status=response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)