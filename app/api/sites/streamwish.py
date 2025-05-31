import requests
from bs4 import BeautifulSoup
import re
from django.http import JsonResponse
import json
import ast
from urllib.parse import quote, unquote
from django.contrib.sites.shortcuts import get_current_site
from . import site_domains

# Configuration
TAG = 'streamwish'
default_domain = site_domains.get_domain('streamwish')
multimovies_domain = site_domains.get_domain('multimovies')
initial_headers = {
    'Referer': default_domain,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"',
}

# Helper Functions
def get_domain(request):
    """Returns the base domain of the request."""
    current_site = get_current_site(request)
    return f"{request.scheme}://{current_site.domain}"

def to_base_36(n):
    """Converts a number to base-36 using an iterative approach for efficiency."""
    return '' if n == 0 else to_base_36(n // 36) + "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36]

response_data = {
    'status': None,
    'status_code': None,
    'error': None,
    'tag': TAG,
    'headers': None,
    'streaming_url': None
}

#Create session
session = requests.Session()

qualities= ['144', '240', '360', '480', '720', '1080']

def real_extract(url, request):
    """Extracts streaming URLs from the given video page."""
    initial_response = session.get(url, headers=initial_headers).text
    if "File is no longer" in initial_response:
        response_data['status'] = 'failed'
        response_data['status_code'] = 200
        response_data['error'] = 'Link Expired!'
        response_data['streaming_url'] = None
        return response_data
    
    # Fetch and parse the initial response
    soup = BeautifulSoup(initial_response, 'html.parser')
    js_code = next((script.string for script in soup.find_all('script') if script.string and "eval(function(p,a,c,k,e,d)" in script.string), "")
    
    # Extract and clean the JS code
    encoded_packed = re.sub(r"eval\(function\([^\)]*\)\{[^\}]*\}\(|.split\('\|'\)\)\)", '', js_code)
    data = ast.literal_eval(encoded_packed)
    
    # Extract values from packed data
    p, a, c, k = data[0], int(data[1]), int(data[2]), data[3].split('|')

    # Replace placeholders with corresponding values
    for i in range(c):
        if k[c - i - 1]:
            p = re.sub(r'\b' + to_base_36(c - i - 1) + r'\b', k[c - i - 1], p)
    #Get Video URL
    video_url = re.search(r'"hls2":"([^"]+)', p).group(1)
    
    
    # Prepare response
    response_data['status']= 'success'
    response_data['status_code']= 200
    response_data['headers'] = initial_headers
    response_data['streaming_url'] = video_url
    
    return response_data