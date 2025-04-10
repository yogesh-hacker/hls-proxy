import requests
from bs4 import BeautifulSoup
from django.contrib.sites.shortcuts import get_current_site
from . import streamwish, gdmirrorbot

# Configuration
default_domain = "https://multimovies.guru"
headers = {
    'Referer': default_domain,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"',
}

# Create session
session = requests.Session()


def real_extract(url, request):
    """Extracts streaming URLs from the given video page."""
    response_data = {
        'status': 'error',
        'status_code': 400,
        'error': None,
        'headers': headers,
        'streaming_urls': {},
        'downloading_urls': {}
    }

    try:
        initial_response = session.get(url, headers=headers)
        initial_response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(initial_response.text, 'html.parser')
        player_element = soup.select_one("#player-option-1")

        if not player_element:
            response_data['error'] = 'Player element not found'
            return response_data

        # Extract POST data attributes
        post_id = player_element.get('data-post')
        data_type = player_element.get('data-type')
        data_nume = player_element.get('data-nume')

        if not all([post_id, data_type, data_nume]):
            response_data['error'] = 'Missing required data attributes'
            return response_data

        # Prepare request data
        data = {
            'action': 'doo_player_ajax',
            'post': post_id,
            'nume': data_nume,
            'type': data_type
        }

        # Send POST request
        post_response = session.post(f"{default_domain}/wp-admin/admin-ajax.php", data=data, headers=headers)
        post_response.raise_for_status()

        response_json = post_response.json()
        
        if 'type' not in response_json or 'embed_url' not in response_json:
            response_data['error'] = 'Invalid response structure'
            return response_data

        embed_url = response_json['embed_url']
        extractor_response = None

        # Handle different types of embeds
        if response_json['type'] == 'iframe':
            embed_url_data = gdmirrorbot.real_extract(embed_url, request)

            if isinstance(embed_url_data, dict) and embed_url_data.get('error'):
                response_data['error'] = embed_url_data['error']
                return response_data

            if not isinstance(embed_url_data, dict) or 'url' not in embed_url_data:
                response_data['error'] = 'Invalid extractor response from gdmirrorbot'
                return response_data

            extractor_response = streamwish.real_extract(embed_url_data['url'], request)

        elif response_json['type'] == 'dtshcode':
            soup = BeautifulSoup(embed_url, 'html.parser')
            iframe = soup.select_one('iframe')

            if not iframe or not iframe.get('src'):
                response_data['error'] = 'Iframe src not found'
                return response_data

            extractor_response = streamwish.real_extract(iframe['src'], request)

        if not isinstance(extractor_response, dict) or 'streaming_url' not in extractor_response:
            response_data['error'] = 'Extraction failed or invalid response structure'
            return response_data

        # Update response data on success
        response_data['status'] = 'success'
        response_data['status_code'] = 200
        response_data['error'] = None
        response_data['streaming_urls'] = extractor_response.get('streaming_url', {})

    except requests.exceptions.RequestException as e:
        response_data['error'] = f'HTTP request failed: {str(e)}'
    except ValueError:
        response_data['error'] = 'Failed to parse JSON response'
    except Exception as e:
        response_data['error'] = f'Unexpected error: {str(e)}'

    return response_data