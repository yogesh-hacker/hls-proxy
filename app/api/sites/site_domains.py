# site_domains.py

SITE_DOMAINS = {
    'multimovies': 'https://multimovies.media',
    'gdmirrorbot': 'https://pro.gtxgamer.site/',
    'streamwish': 'https://swiftplayers.com'
}

def get_domain(site_name: str) -> str:
    """
    Returns the domain URL for a given site name.
    
    Args:
        site_name (str): The name of the site to look up.
    
    Returns:
        str: The domain URL if found, else None.
    """
    return SITE_DOMAINS.get(site_name)