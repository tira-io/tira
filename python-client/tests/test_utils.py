import requests
from hashlib import md5
from tira.tira_redirects import redirects, mirror_url

def md5_of_first_kilobyte_of_http_resource(url):
    #if not url.startswith('https://files.webis.de'):
    #    raise ValueError(f'URL {url} is not from webis.de respectively zenodo')
    print(url, flush=True)
    return md5(requests.get(url, headers={'Range': f'bytes=0-1024'}).content).hexdigest()


def digest_of_resource(resource):
    from tira.tira_redirects import RESOURCE_REDIRECTS

    if resource not in RESOURCE_REDIRECTS:
        raise ValueError('Could not find resource {resource}.')
    
    url = RESOURCE_REDIRECTS[resource]
    
    return {
        'url': url,
        'redirect_url': redirects(url=url),
        'md5_of_first_kilobyte': md5_of_first_kilobyte_of_http_resource(url)
    }