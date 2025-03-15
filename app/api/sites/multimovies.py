import requests
from bs4 import BeautifulSoup
import re
from django.http import JsonResponse
import json
import ast
from urllib.parse import quote
from django.contrib.sites.shortcuts import get_current_site

def get_domain(request):
    current_site = get_current_site(request)
    return f"{request.scheme}://{current_site.domain}"
    
from urllib.parse import quote

def construct_urls(base_url, request):
    # Mapping of quality indicators to resolutions
    quality_mapping = {
        'l': '480p',
        'n': '720p',
        'h': '1080p'
    }

    # Corresponding indexes
    indexes = ['f1', 'f2', 'f3']

    # Extract the part before ",l,n,h,.urlset" and after it
    prefix, suffix = base_url.split(",l,n,h,.urlset")
    
    # Remove "/master.m3u8" from the suffix if present
    suffix = suffix.replace("/master.m3u8", "")

    # Construct URLs
    urls = {}
    for q, index in zip(quality_mapping, indexes):
        url = f"{prefix}{q}/index-{index}-v1-a1.m3u8{suffix}"
        urls[quality_mapping[q]] = f"{get_domain(request)}/proxy?url={quote(url, safe='')}"

    return urls


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