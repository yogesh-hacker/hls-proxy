import requests
import re
import base64
import json

# Configuration
default_domain = "https://gdmirrorbot.nl"
headers = {
    'Referer': default_domain,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"',
}

# Create session
session = requests.Session()

def real_extract(url, request):
    """Extracts the streaming URL from the given URL."""
    response_data = {
        'status': 'error',
        'status_code': 400,
        'error': None,
        'url': None
    }

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        page_content = response.text

        # Extract SID
        sid_match = re.search(r'sid\s*=\s*"([^"]+)"', page_content)
        if not sid_match:
            response_data['error'] = 'SID not found in response'
            return response_data

        sid = sid_match.group(1)
        data = {'sid': sid}

        # Fetch streaming data
        post_response = requests.post("https://pro.gtxgamer.site/embedhelper.php", headers=headers, data=data)
        post_response.raise_for_status()

        post_json = post_response.json()
        if 'mresult' not in post_json:
            response_data['error'] = 'Invalid response structure'
            return response_data

        # Decode the base64 data
        decoded_data = base64.b64decode(post_json['mresult']).decode("utf-8")
        json_data = json.loads(decoded_data)

        if 'smwh' not in json_data:
            response_data['error'] = 'Missing streaming URL in response'
            return response_data

        # Success
        response_data['status'] = 'success'
        response_data['status_code'] = 200
        response_data['error'] = None
        response_data['url'] = f"https://multimovies.cloud/{json_data['smwh']}"

    except requests.exceptions.RequestException as e:
        response_data['error'] = f'HTTP request failed: {str(e)}'
    except json.JSONDecodeError:
        response_data['error'] = 'Failed to parse JSON response'
    except base64.binascii.Error:
        response_data['error'] = 'Failed to decode base64 response'
    except Exception as e:
        response_data['error'] = f'Unexpected error: {str(e)}'

    return response_data  # Return a dictionary instead of JsonResponse