import requests
from django.http import StreamingHttpResponse, JsonResponse
from urllib.parse import urlparse, urljoin, quote, unquote
import time
import m3u8
from django.contrib.sites.shortcuts import get_current_site

HEADERS = {
    "Referer": "https://multimovies.cloud",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

HOP_BY_HOP_HEADERS = {
    'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
    'te', 'trailer', 'transfer-encoding', 'upgrade'
}

def remove_hop_by_hop_headers(response):
    """Remove hop-by-hop headers from the response."""
    for header in HOP_BY_HOP_HEADERS:
        if header in response.headers:
            del response.headers[header]
    return response

def generate_m3u8(playlist_items, is_master=False):
    m3u8_content = "#EXTM3U\n"
    
    if is_master:
        # Master playlist with multiple resolutions
        m3u8_content += "#EXT-X-VERSION:3\n"
        for item in playlist_items:
            m3u8_content += (
                f"#EXT-X-STREAM-INF:BANDWIDTH={item['bandwidth']},RESOLUTION={item['resolution'][0]}x{item['resolution'][1]}\n"
                f"{item['uri']}\n"
            )
    else:
        # Media playlist with TS segments
        m3u8_content += "#EXT-X-TARGETDURATION:10\n#EXT-X-ALLOW-CACHE:YES\n#EXT-X-PLAYLIST-TYPE:VOD\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:1\n"
        for item in playlist_items:
            m3u8_content += f"{item['info']}\n{item['uri']}\n"
        m3u8_content += "#EXT-X-ENDLIST"

    return m3u8_content

def get_domain(request):
    current_site = get_current_site(request)
    return f"{request.scheme}://{current_site.domain}"

def proxy_view(request):
    start_time = time.time()
    encoded_url = request.GET.get('url', '')
    hls_url = unquote(encoded_url)
    
    # Fetch the M3U8 playlist
    playlist_response = requests.get(hls_url, headers=HEADERS)
    m3u8_playlist = m3u8.loads(playlist_response.text)
    
    playlist_items = []

    is_master = m3u8_playlist.is_variant  # Determine if it's a master playlist

    if is_master:
        # Handling master playlist with multiple resolutions
        for variant in m3u8_playlist.playlists:
            uri = variant.uri
            complete_url = uri if bool(urlparse(uri).netloc) else urljoin(hls_url, uri)
            proxied_url = f"{get_domain(request)}/proxy/?url={quote(complete_url)}"
            playlist_items.append({
                'uri': proxied_url,
                'resolution': variant.stream_info.resolution,
                'bandwidth': variant.stream_info.bandwidth
            })
    else:
        # Handling media playlist with TS segments
        for segment in m3u8_playlist.segments:
            complete_url = segment.uri if bool(urlparse(segment.uri).netloc) else urljoin(hls_url, segment.uri)
            proxied_url = f"{get_domain(request)}/proxy/stream/?ts_url={quote(complete_url)}"
            playlist_items.append({
                'info': f"#EXTINF:{segment.duration},",
                'uri': proxied_url
            })

    # Pass the is_master flag while generating the playlist
    m3u8_content = generate_m3u8(playlist_items, is_master=is_master)
    print("\n\n"*5+m3u8_content[-500:]+"\n"*7)

    # Return the updated M3U8 playlist
    response = StreamingHttpResponse(m3u8_content, content_type="application/vnd.apple.mpegurl")
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Content-Security-Policy'] = "default-src * data: blob: 'unsafe-inline' 'unsafe-eval'"
    
    return remove_hop_by_hop_headers(response)


def extract_key_url(line):
    """ Extract the key URI from the #EXT-X-KEY line """
    if 'URI=' in line:
        start = line.find('URI="') + 5
        end = line.find('"', start)
        return line[start:end]
    return None


def stream_ts(request):
    ts_url = request.GET.get('ts_url')
    if not ts_url:
        return JsonResponse({"error": "Missing ts_url parameter"}, status=400)

    decoded_url = unquote(ts_url)

    try:
        response = requests.get(decoded_url, stream=True, headers=HEADERS, timeout=10)
        response.raise_for_status()

        excluded_headers = {'content-encoding', 'transfer-encoding', 'content-length', 'content-type'}
        response_headers = {
            k: v for k, v in response.headers.items() if k.lower() not in excluded_headers
        }

        streaming_response = StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=4096),
            content_type=response.headers.get('Content-Type', 'video/mp2t'),
            headers=response_headers
        )

        return remove_hop_by_hop_headers(streaming_response)

    except requests.Timeout:
        return JsonResponse({"error": "Request timed out"}, status=504)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"HTTP error: {e}"}, status=response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)


def proxy_key(request):
    key_url = request.GET.get('key_url')
    if not key_url:
        return JsonResponse({"error": "Missing key_url parameter"}, status=400)

    decoded_key_url = unquote(key_url)

    try:
        key_response = requests.get(decoded_key_url, headers=HEADERS, timeout=10)
        key_response.raise_for_status()

        streaming_response = StreamingHttpResponse(key_response.content, content_type='application/octet-stream')

        return remove_hop_by_hop_headers(streaming_response)

    except requests.Timeout:
        return JsonResponse({"error": "Key request timed out"}, status=504)
    except requests.HTTPError as e:
        return JsonResponse({"error": f"HTTP error: {e}"}, status=key_response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)