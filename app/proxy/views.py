import requests
from django.http import StreamingHttpResponse, JsonResponse
from urllib.parse import urlparse, urljoin, quote, unquote
import time

HEADERS = {
    "Referer": "https://spedostream.com/",
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

def proxy_view(request, hls_url):
    start_time = time.time()
    hls_url = unquote(hls_url)
    
    # Fetch the M3U8 playlist
    playlist_response = requests.get(hls_url, headers=HEADERS)

    if playlist_response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch HLS playlist"}, status=404)
    
    # Parse the playlist and rewrite URLs
    playlist_content = playlist_response.text.splitlines()
    updated_playlist = []

    # Get the base URL for relative paths
    parsed_url = urlparse(hls_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    for line in playlist_content:
        if line.startswith("#EXT-X-KEY"):  
            key_url = extract_key_url(line)
            if key_url:
                proxied_key_url = request.build_absolute_uri(f'/proxy/key/?key_url={quote(key_url)}')
                line = line.replace(key_url, proxied_key_url)
            updated_playlist.append(line)
        elif line.startswith("#"):  
            updated_playlist.append(line)
        elif line:  
            absolute_url = urljoin(base_url, line) if not line.startswith("http") else line
            proxy_ts_url = request.build_absolute_uri(f'/proxy/stream/?ts_url={quote(absolute_url)}')
            updated_playlist.append(proxy_ts_url)
    
    end_time = time.time()
    print(f"Response Time: {end_time - start_time:.4f} seconds")
    
    # Return the updated M3U8 playlist
    response = StreamingHttpResponse("\n".join(updated_playlist), content_type="application/vnd.apple.mpegurl")
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