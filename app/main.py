from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me")

oauth = OAuth(app)
oauth.register(
    name='keycloak',
    client_id=os.environ['OIDC_CLIENT_ID'],
    client_secret=os.environ['OIDC_CLIENT_SECRET'],
    server_metadata_url='http://keycloak:8080/realms/flask-realm/.well-known/openid-configuration',
    access_token_url='http://keycloak:8080/realms/flask-realm/protocol/openid-connect/token',
    authorize_url=os.environ['KEYCLOAK_URL'] + '/realms/flask-realm/protocol/openid-connect/auth',
    api_base_url=os.environ['KEYCLOAK_URL'] + '/realms/flask-realm/protocol/openid-connect/userinfo',
    client_kwargs={
        'scope': 'openid profile email'
    }
)

@app.route('/')
def home():
    user = session.get('user')
    if user:
        return f"Hello, {user['name']}!"
    return 'Welcome! <a href="/login">Login</a>'

@app.route('/login')
def login():
    nonce = secrets.token_urlsafe(16)
    session['oidc_nonce'] = nonce
    session.pop('oauth_state', None)
    redirect_uri = url_for('auth_callback', _external=True)
    if oauth.keycloak is None:
        return "Something went wrong with oauth.keycloak"
    return oauth.keycloak.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/auth/callback')
def auth_callback():
    if oauth.keycloak is None:
        return "Something went wrong with oauth.keycloak"

    token = oauth.keycloak.authorize_access_token()
    nonce = session.pop('oidc_nonce', None)
    id_token = token.get('id_token')
    access_token = token['access_token']

    userinfo = oauth.keycloak.parse_id_token(token, nonce=nonce)
    
    session['user'] = {
        'sub': userinfo['sub'],
        'name': userinfo.get('name'),
        'email': userinfo.get('email')
    }
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

