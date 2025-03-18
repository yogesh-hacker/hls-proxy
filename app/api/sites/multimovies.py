import requests
from bs4 import BeautifulSoup
import re
from django.http import JsonResponse
import json
import ast
from urllib.parse import quote, unquote
from django.contrib.sites.shortcuts import get_current_site

def get_domain(request):
    current_site = get_current_site(request)
    return f"{request.scheme}://{current_site.domain}"

def is_url_available(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def construct_urls(base_url, request):
    print(base_url)
    # Quality mapping
    quality_mapping = {
        'l': '480p',
        'n': '720p',
        'h': '1080p'
    }

    # Regex to find the quality delimiter and `.urlset` or `/master.m3u8`
    pattern = r'_,[lnh,]+(?:\.urlset)?/master\.m3u8|_[lnh]/master\.m3u8'
    match = re.search(pattern, base_url)

    if not match:
        raise ValueError("Invalid URL pattern for quality replacement.")

    # Extract the part before and after the quality indicators
    prefix = base_url[:match.start()]
    suffix = base_url[match.end()-11:]

    # Store only valid URLs
    available_urls = {}

    for q, resolution in quality_mapping.items():
        new_url = f"{prefix}_{q}/{suffix}"
        if is_url_available(new_url):
            available_urls[resolution] = f"{get_domain(request)}/proxy/?url={quote(new_url, safe='')}"

    return available_urls

default_domain = "https://multimovies.cloud"
initial_headers = {
    'Referer': default_domain,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"',
}

response_data = {
    'status': None,
    'status_code': None,
    'error': None,
    'headers': {},
    'streaming_urls': {},
    'downloading_urls': {}
}

#Create session
session = requests.Session()

qualities= ['144', '240', '360', '480', '720', '1080']

def real_extract(url, request):
    initial_response = session.get(url, headers=initial_headers).text
    
    # Fetch and parse the initial response
    soup = BeautifulSoup(initial_response, 'html.parser')
    js_code = next((script.string for script in soup.find_all('script') if script.string and "eval(function(p,a,c,k,e,d)" in script.string), "")
    
    # Extract and clean the JS code
    encoded_packed = re.sub(r"eval\(function\([^\)]*\)\{[^\}]*\}\(|.split\('\|'\)\)\)", '', js_code)
    data = ast.literal_eval(encoded_packed)

    # Base-36 conversion helper function
    def to_base_36(n):
        return '' if n == 0 else to_base_36(n // 36) + "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36]

    # Extract values from packed data
    p, a, c, k = data[0], int(data[1]), int(data[2]), data[3].split('|')

    # Replace placeholders with corresponding values
    for i in range(c):
        if k[c - i - 1]:
            p = re.sub(r'\b' + to_base_36(c - i - 1) + r'\b', k[c - i - 1], p)

    #Get Video URL
    video_url = re.search(r'file:"([^"]+)', p).group(1)
    
    urls = construct_urls(video_url, request)
    response_data['streaming_urls'] = urls
    
    return response_data