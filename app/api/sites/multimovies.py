import requests
from bs4 import BeautifulSoup
from django.contrib.sites.shortcuts import get_current_site
from . import streamwish, gdmirrorbot, streamp2p, site_domains
from . import utils as u

# Configuration
default_domain = site_domains.get_domain('multimovies')
headers = {
    'Referer': default_domain,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
}

# Create session
session = requests.Session()


def real_extract(url, request):
    """Extracts streaming URLs from the given video page."""
    response_data = {
        'status': 'error',
        'status_code': 400,
        'error': None,
        'servers': []
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

        response_json = None
        try:
            response_json = post_response.json()
        except ValueError:
            response_data['error'] = 'Invalid JSON returned from POST response'
            return response_data
        if 'type' not in response_json or 'embed_url' not in response_json:
            response_data['error'] = 'Invalid response structure'
            return response_data
        
        embed_url = response_json['embed_url']
        extractor_response = None

        # Handle different types of embeds
        if response_json['type'] == 'iframe':
            embed_data = gdmirrorbot.real_extract(embed_url, request)

            if u.isDict(embed_data) and embed_data.get('error'):
                response_data['error'] = embed_data['error']
                return response_data

            if not u.isDict(embed_data) or 'embed_urls' not in embed_data:
                response_data['error'] = 'Invalid extractor response from gdmirrorbot'
                return response_data
            embed_urls = embed_data['embed_urls']
            streamwish_iframe = embed_urls.get('streamwish')
            streamp2p_iframe = None
            if 'streamp2p' in embed_urls:
                streamp2p_iframe = embed_urls.get('streamp2p')
                
            media_urls = [
                streamwish.real_extract(streamwish_iframe, request)
            ]
            if streamp2p_iframe is not None:
                media_urls.append(streamp2p.real_extract(streamp2p_iframe, request))
            response_data['servers'] = u.proxify(media_urls, request)

        elif response_json['type'] == 'dtshcode':
            soup = BeautifulSoup(embed_url, 'html.parser')
            iframe = soup.select_one('iframe')

            if not iframe or not iframe.get('src'):
                response_data['error'] = 'Iframe src not found'
                return response_data
            media_urls = [
                streamwish.real_extract(iframe['src'], request)
            ]
            response_data['servers'] = u.proxify(media_urls, request)

        # Update response data on success
        response_data['status'] = 'success'
        response_data['status_code'] = 200
        response_data['error'] = None

    except requests.exceptions.RequestException as e:
        response_data['error'] = f'HTTP request failed: {str(e)}'
    except ValueError:
        response_data['error'] = 'Failed to parse JSON response'
    except Exception as e:
        response_data['error'] = f'Unexpected error: {str(e)}'

    return response_data