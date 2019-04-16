"""core tools."""
import glob
import concurrent.futures
import urllib.request

from urllib.parse import urlencode, urlparse, quote

import lxml.html

import asyncio

from requests_html import AsyncHTMLSession as AsyncRequestHTMLSession


def combine_json_file(foldername):
    itemlist = []

    jsonpath = os.path.join(RESOURCE_DIR, foldername, '*.json')
    for fhd in glob.glob(jsonpath):
        with open(fhd, 'r') as infile:
            itemlist.extend(json.loads(infile.read()))

    itemlist = list(set(itemlist))
    results = concurrent_get_title(itemlist)

    combine_path = os.path.join(RESOURCE_DIR, 'artslist.json')
    with open(combine_path, 'w') as filed:
        filed.write(json.dumps(results, indent=4, ensure_ascii=False))


def is_active_url(url):
    try:
        urllib.request.urlopen(quote(url))
        retdata = {'url': url, 'is_active': True}
    except urllib.error.HTTPError as error:
        retdata = {'url': url, 'is_active': error.code < 500}

    return retdata


def concurrent_check_urls(urls):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        for value, result in zip(urls, executor.map(is_active_url, urls)):
            results.append(result)

    return results


def concurrent_get_title(urls, max_workers=4):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        for url, result in zip(urls, executor.map(get_url_title, urls)):
            results.append({'link': url, 'title': result})
            print(url, result)

    return results


def get_url_title(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    }
    try:
        req = urllib.request.Request(
            quote(url, safe='/:?='), headers=headers)
    except ValueError:
        print('urlerror', url)
        return url

    try:
        k = urllib.request.urlopen(req, timeout=8)
        data = k.read()
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        return 'error: %s' % error.reason
    except Exception as error:
        print(error)
        return url

    try:
        fe = lxml.html.fromstring(data.decode())
        title = fe.find('.//title').text or urlparse(url).netloc
    except (AttributeError, ValueError, lxml.etree.ParserError):
        title = urlparse(url).netloc

    return title.strip()


class AsyncRequestSession(AsyncRequestHTMLSession):

    def run_with_args(self, coros_list):
        tasks = [
            asyncio.ensure_future(coro(args)) for coro, args in coros_list
        ]
        done, _ = self.loop.run_until_complete(asyncio.wait(tasks))
        return [t.result() for t in done]


asession = AsyncRequestSession()


async def get_url_title(url):
    try:
        r = await asession.get(url)
    except Exception as error:
        return str(error)

    return r


def async_get_url_list_title(url_list):
    coros_list = [
        (get_url_title, url) for url in url_list
    ]
    results = asession.run_with_args(coros_list)

    return results
