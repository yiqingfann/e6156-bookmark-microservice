from flask import Flask, Response, request, redirect, url_for, g
import json
import uuid

from RDBResource import BookmarkResource

app = Flask(__name__)

# -------------------- authentication --------------------
import requests
from flask_cors import CORS
from context import API_GATEWAY_URL
CORS(app)

@app.before_request
def before_request():

    # verify id_token
    id_token = request.headers.get('id_token')
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    response = requests.get(url)
    user_data = response.json()
    email = user_data.get('email')

    # if not verified, return message
    if not email:
        response = Response("Please provide a valid google id_token!", status=200)
        return response

    # if verified
    url = f"{API_GATEWAY_URL}/api/users?email={email}"
    headers = {'id_token': id_token}
    response = requests.get(url, headers=headers)
    result = response.json()

    # check if user exist
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
        response = requests.post(url, data=template, headers=headers)
    else:
        user_id = result[0]['user_id']

    g.user_id = user_id
    g.email = email

# -------------------- GET / --------------------

@app.route('/')
def index():
    response = Response(f'Hello\n {g.email}\n {g.user_id}', status=200)
    return response

@app.route('/api/bookmarks', methods = ['POST'])
def create_bookmark():
    template = request.get_json()
    if template.get('user_id') is None:
        template['user_id'] = g.user_id
    
    if template.get('post_id') is not None:
        BookmarkResource.create(template)
        response = Response("Successfully created bookmark!", status=200)
    else:
        response = Response("Invalid data: must provide post_id in request body!", status=400)
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
    if template.get('user_id') is None:
        template['user_id'] = g.user_id
    
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
    if template.get('user_id') is None:
        template['user_id'] = g.user_id
    
    if template.get('post_id') is not None:
        BookmarkResource.delete(template)
        response = Response("Successfully deleted bookmark!", status=200)
    else:
        response = Response("Invalid data: must provide post_id in query param!", status=400)
    return response

# ------------------- main function -------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
