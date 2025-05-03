import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from . import site_domains


# Configuration
TAG = 'streamp2p'
default_domain = site_domains.get_domain(TAG)
user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36"
headers = {
    'Referer': default_domain,
    'User-Agent': user_agent
}
response_data = {
    'status': None,
    'status_code': None,
    'error': None,
    'tag': TAG,
    'headers': None,
    'streaming_url': None
}

def real_extract(url, request):
    # Fetch response
    response = requests.get(url, headers=headers).text
    video_id = url.split("#")[-1]
    
    # Get encrypted video info from API
    api = f'{default_domain}/api/v1/video?id={video_id}'
    encrypted_data = requests.get(api, headers=headers).text
    # Decrypt Data using AES-CBC
    password = "kiemtienmua911ca"
    iv = "1234567890oiuytr"

    # Ensure key and IV are 16 bytes
    key = password.encode('utf-8')
    iv = iv.encode('utf-8')

    # Convert hex to bytes
    encrypted_bytes = bytes.fromhex(encrypted_data)

    # Decrypt using AES CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = cipher.decrypt(encrypted_bytes)

    # Remove padding (PKCS7)
    decrypted_json = unpad(decrypted_bytes, AES.block_size).decode('utf-8')
    decrypted_data = json.loads(decrypted_json)

    # Extract video URL
    video_url = decrypted_data['source']
    
    response_data['status']= 'success'
    response_data['status_code']= 200
    response_data['headers'] = headers
    response_data['streaming_url'] = video_url
    
    return response_data