from flask import Flask, Response, request, redirect, url_for, g
import json
import uuid

from RDBResource import BookmarkResource

app = Flask(__name__)

# -------------------- authentication --------------------
import os
import re
import requests
from flask_cors import CORS
from flask_dance.contrib.google import google, make_google_blueprint
from context import get_google_blueprint_info, API_GATEWAY_URL

CORS(app)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
app.secret_key = "e6156"
google_blueprint_info = get_google_blueprint_info()
google_blueprint = make_google_blueprint(
    client_id = google_blueprint_info["client_id"],
    client_secret = google_blueprint_info["client_secret"],
    scope = ["profile", "email"]
)
app.register_blueprint(google_blueprint, url_prefix="/login")
google_blueprint = app.blueprints.get("google")

paths_do_not_require_security = [
    '/login/google/?.*'
]

@app.before_request
def before_request():
    for regex in paths_do_not_require_security:
        if re.match(regex, request.path):
            return

    if not google.authorized:
        return redirect(url_for('google.login'))
    
    try:
        # print(json.dumps(google_blueprint.session.token, indent=2))
        user_data = google.get('/oauth2/v2/userinfo').json()
        email = user_data['email']
        url = f"{API_GATEWAY_URL}/api/users?email={email}"
        cookies = request.cookies
        response = requests.get(url, cookies=cookies)
        result = response.json()

        if len(result) == 0:
            url = f"{API_GATEWAY_URL}/api/users"
            user_id = str(uuid.uuid4())
            template = {
                'user_id': user_id,
                'first_name': user_data['given_name'],
                'last_name': user_data['family_name'],
                'nickname': user_data['email'],
                'email': user_data['email'],
            }
            response = requests.post(url, data=template, cookies=cookies)
        else:
            user_id = result[0]['user_id']
        g.user_id = user_id
        g.email = email
    except:
        # for oauthlib.oauth2.rfc6749.errors.TokenExpiredError
        return redirect(url_for('google.login'))

# -------------------- GET / --------------------

@app.route('/')
def index():
    response = Response(f'Hello\n {g.email}\n {g.user_id}', status=200)
    return response

@app.route('/api/bookmarks', methods = ['POST'])
def create_bookmark():
    template = request.get_json()
    template['user_id'] = g.user_id
    
    if template.get('post_id') is not None:
        BookmarkResource.create(template)
        response = Response("Successfully created bookmark!", status=200)
    else:
        response = Response("Invalid data!", status=400)
    return response

@app.route('/api/bookmarks', methods = ['GET'])
def retrieve_bookmark():
    template = {}
    field_list = []
    for key in request.args:
        vals = request.args.get(key).split(",")
        if key == "fields":
            field_list.extend(vals)
        else:
            if len(vals) == 1:
                template[key] = vals[0]
            else:
                template[key] = vals
    field_list = field_list if len(field_list) else None
    
    result = BookmarkResource.find_by_template(template, field_list)
    response = Response(json.dumps(result), status=200, content_type="application/json")
    return response

@app.route('/api/bookmarks', methods = ['DELETE'])
def delete_bookmark():
    template = {}
    for key in request.args:
        vals = request.args.get(key).split(",")
        if len(vals) == 1:
            template[key] = vals[0]
        else:
            template[key] = vals
    template['user_id'] = g.user_id
    
    if template.get('post_id') is not None:
        BookmarkResource.delete(template)
        response = Response("Successfully deleted bookmark!", status=200)
    else:
        response = Response("Invalid data!", status=400)
    return response

# ------------------- main function -------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
