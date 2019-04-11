"""server app."""
import json
import datetime
import os

import glob
import concurrent.futures
import urllib.request

from urllib.parse import urlencode, urlparse, quote

import lxml.html

from flask import (Flask, render_template, send_from_directory,
                   request, make_response, jsonify)

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_DIR = os.path.join(PROJECT_DIR, 'templates')

STATIC_DIR = os.path.join(PROJECT_DIR, 'templates/static')
RESOURCE_DIR = os.path.join(PROJECT_DIR, 'resource')


APP = Flask(__name__, template_folder=TEMPLATE_DIR, static_url_path=STATIC_DIR)

APP.config['STATIC_DIR'] = STATIC_DIR


@APP.route('/static/<path:path>')
def handler_static(path):
    return send_from_directory(APP.config['STATIC_DIR'], path)


@APP.route('/artslist/')
def get_artslist():
    combine_path = os.path.join(RESOURCE_DIR, 'artslist.json')

    with open(combine_path, 'r') as filed:
        itemlist = json.loads(filed.read())

    itemlist = [
        {'title': item['title'], 'link': item['link'],
         'domain': urlparse(item['link']).netloc}
        for item in itemlist
    ]
    context = {'itemlist': itemlist}
    return render_template('artslist.html', **context)


@APP.route('/')
def index_view():
    context = {
        'total_answers': 460,
        'total_links': 1000
    }
    return render_template('index.html', **context)


@APP.route('/post/', methods=['POST', 'OPTIONS'])
def collect_items():
    response = make_response(jsonify({'hello': 'ok'}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'content-type'

    if request.method == 'OPTIONS':
        return response

    now = datetime.datetime.today()
    foldername = now.strftime('%Y%m%d')

    folderpath = os.path.join(RESOURCE_DIR, foldername)
    if not os.path.exists(folderpath):
        os.mkdir(folderpath)

    reqdata = request.json
    itemlist = reqdata['arrlist']

    filename = '{}-page{}.json'.format(foldername, str(reqdata['page']))

    path = os.path.join(RESOURCE_DIR, foldername, filename)
    with open(path, 'w') as filed:
        filed.write(json.dumps(itemlist, indent=4, ensure_ascii=False))

    return response


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
