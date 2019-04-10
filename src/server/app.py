"""server app."""
import json
import datetime
import os

import glob
import concurrent.futures
import urllib.request
from urllib.parse import urlencode

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
def send_static(path):
    return send_from_directory(APP.config['STATIC_DIR'], path)


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
    folderpath = now.strftime('%Y%m%d')

    if not os.path.exists(folderpath):
        os.mkdir(folderpath)

    reqdata = request.json
    itemlist = reqdata['arrlist']

    filename = '{}-page{}.json'.format(folderpath, str(reqdata['page']))

    path = os.path.join(RESOURCE_DIR, filename)
    with open(path, 'w') as filed:
        filed.write(json.dumps(itemlist, indent=4, ensure_ascii=False))

    return response


def combine_json_file(folderpath):
    itemlist = []
    jsonpath = os.path.join(RESOURCE_DIR, '*.json')
    for fhd in glob.glob(jsonpath):
        with open(fhd, 'r') as infile:
            itemlist.extend(json.loads(infile.read()))

    itemlist = list(set(itemlist))
    # results = concurrent_check_urls(itemlist)

    combine_path = os.path.join(RESOURCE_DIR, folderpath + '.json')
    with open(combine_path, 'w') as filed:
        filed.write(json.dumps(itemlist, indent=4, ensure_ascii=False))


def is_active_url(url):
    try:
        urllib.request.urlopen(urlencode(url))
        retdata = {'url': url, 'is_active': True}
    except urllib.error.HTTPError as error:
        retdata = {'url': url, 'is_active': error.code < 500}

    return retdata


def concurrent_check_urls(urls):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        for value, result in zip(urls, executor.map(is_active_url, urls)):
            print(value, result)
            results.append(result)

    return results
