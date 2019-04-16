"""server app."""
import json
import datetime
import os

from urllib.parse import urlparse


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


@APP.route('/card/')
def card_view():
    context = {}
    return render_template('card.html', **context)


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
