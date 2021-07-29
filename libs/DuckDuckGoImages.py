#
# Direction modification of the original code by https://github.com/JorgePoblete/DuckDuckGoImages
# - Added use_name and target_resolution
#

import re
import io
import os
import json
import uuid
import shutil
import random
import requests
from PIL import Image
from joblib import Parallel, delayed

def download(query, folder='.', max_urls=None, thumbnails=False,
             parallel=False, shuffle=False, remove_folder=False, use_name=None,
             target_resolution=None):

    if thumbnails:
        urls = get_image_thumbnails_urls(query)
    else:
        urls = get_image_urls(query)

    if shuffle:
        random.shuffle(urls)

    if max_urls is not None and len(urls) > max_urls:
        urls = urls[:max_urls]

    if remove_folder:
        _remove_folder(folder)

    _create_folder(folder)
    if parallel:
        return _parallel_download_urls(urls, folder, use_name, target_resolution)
    else:
        return _download_urls(urls, folder, use_name, target_resolution)

def _download(url, folder, use_name, target_resolution):
        try:
            filename = str(uuid.uuid4().hex)
            if use_name:
                filename = use_name

            while os.path.exists("{}/{}.jpg".format(folder, filename)):
                filename = str(uuid.uuid4().hex)

            response = requests.get(url, stream=True, timeout=1.0, allow_redirects=True)
            with Image.open(io.BytesIO(response.content)) as im:
                with open("{}/{}.jpg".format(folder, filename), 'wb') as out_file:
                    if target_resolution:
                        im = im.resize(target_resolution)

                    im.save(out_file)
                    return True
        except:
            return False

def _download_urls(urls, folder, use_name, target_resolution):
    downloaded = 0
    for index, url in enumerate(urls):
        filename = use_name[index] if isinstance(use_name, list) == 1 else use_name
        if _download(url, folder, filename, target_resolution):
            downloaded += 1
    return downloaded

def _parallel_download_urls(urls, folder, use_name, target_resolution):
    downloaded = 0
    with Parallel(n_jobs=os.cpu_count()) as parallel:
        results = parallel(delayed(_download)(url, folder, None, target_resolution) for url in urls)
        for result in results:
            if result:
                downloaded += 1
    return downloaded

def get_image_urls(query):
    token = _fetch_token(query)
    return _fetch_search_urls(query, token)

def get_image_thumbnails_urls(query):
    token = _fetch_token(query)
    return _fetch_search_urls(query, token, what="thumbnail")

def _fetch_token(query, URL="https://duckduckgo.com/"):
    res = requests.post(URL, data={'q': query})
    if res.status_code != 200:
        return ""
    match = re.search(r"vqd='([\d-]+)'", res.text, re.M|re.I)
    if match is None:
        return ""
    return match.group(1)

def _fetch_search_urls(query, token, URL="https://duckduckgo.com/", what="image"):
    query = {
        "vqd": token,
        "q": query,
        "l": "wt-wt",
        "o": "json",
        "f": ",,,",
        "p": "2"
    }
    urls = []

    res = requests.get(URL+"i.js", params=query)
    if res.status_code != 200:
        return urls

    data = json.loads(res.text)
    for result in data["results"]:
        urls.append(result[what])

    while "next" in data:
        res = requests.get(URL+data["next"], params=query)
        if res.status_code != 200:
            return urls
        data = json.loads(res.text)
        for result in data["results"]:
            urls.append(result[what])
    return urls

def _remove_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder, ignore_errors=True)

def _create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
