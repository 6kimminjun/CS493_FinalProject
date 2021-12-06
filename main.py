from google.cloud import datastore
from flask import Flask, request, render_template, redirect
import json
import constants
import loads
import boats
import string
import random
import requests

app = Flask(__name__)
client = datastore.Client()
app.register_blueprint(loads.bp)
app.register_blueprint(boats.bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/redirect')
def redirect_oauth():
    letters = string.ascii_lowercase
    client_state = ''.join(random.choice(letters) for i in range(12))
    new_states = datastore.entity.Entity(key=client.key(constants.states))
    new_states.update(
        {
            "states": client_state
        }
    )
    client.put(new_states)
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=25602732107-jm2o8s3k2ccr1gvdqh6hn8c6j3uhsp9p.apps.googleusercontent.com&redirect_uri=https://kimassignment6.ue.r.appspot.com/oauth&scope=https://www.googleapis.com/auth/userinfo.profile&state={}".format(client_state))

@app.route('/oauth')
def oauth_page():
    query = client.query(kind=constants.states)
    results = list(query.fetch())
    state = request.args.get('state')
    states_list = []
    for result in results:
        if "states" in result:
            states_list.append(result["states"])
    if state not in states_list:
        return ("The state was not verified!")
    server_data = {
        "code" : request.args.get('code'),
        "client_id" : "25602732107-jm2o8s3k2ccr1gvdqh6hn8c6j3uhsp9p.apps.googleusercontent.com",
        "client_secret" : "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",
        "redirect_uri" : "https://kimassignment6.ue.r.appspot.com/oauth",
        "grant_type" : "authorization_code"
    }
    post_response = requests.post('https://oauth2.googleapis.com/token', data=server_data)
    post_response_in_json = post_response.json()
    access_token = post_response_in_json['access_token']
    get_response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=" + access_token)
    get_response_in_json = get_response.json()
    userInfo = {
        "First name": get_response_in_json["given_name"],
        "Last name": get_response_in_json["family_name"],
        "The client's state": state
    }
    return render_template("userInfo.html", userInfo=userInfo)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)