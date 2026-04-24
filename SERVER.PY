from flask import Flask, request, send_from_directory, Response
import os
import logging

app = Flask(__name__)
ASSET_FOLDER = os.path.abspath('ASSET')

# Logging set to mimic old-school server consoles
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

@app.before_request
def validate_dsi():
    """
    Strong Resolver Logic: 
    Checks if the request is actually coming from a Nintendo console.
    """
    ua = request.headers.get('User-Agent', '')
    if 'Nintendo DSi' in ua:
        logger.info(f'[CON] Verified DSi Connection: {request.remote_addr}')

# 1. NINTENDO CONNECTION TEST (conntest.nintendowifi.net)
@app.route('/testconn.html')
@app.route('/ok.html')
def conntest():
    # This header is the 'secret sauce' for 3rd party servers.
    # It tells the DSi firmware the internet is active.
    resp = Response("<html><body>ok</body></html>")
    resp.headers['X-Organization'] = 'Nintendo'
    return resp

# 2. NAS AUTHENTICATION (nas.nintendowifi.net)
# This mimics the login server that shut down in 2014.
@app.route('/ac', methods=['POST'])
@app.route('/pr', methods=['POST'])
def nas_login():
    logger.info('[NAS] Handling Authentication Handshake')
    # Returns a dummy challenge/token so the DSi thinks it's logged in.
    return "challenge=abcdefg12345&token=hijklmn67890"

# 3. HATENA / ASSET RESOLVER
@app.route('/<path:path>')
def resolve_assets(path):
    # Regional fix (Map all regions to EU assets)
    path = path.replace('ds/v2-us/', 'ds/v2-eu/').replace('ds/v2-jp/', 'ds/v2-eu/')
    
    # Handle the specific user-ID folder structure
    if 'ds/v2-eu/' in path and len(path.split('/')) > 3:
        # Re-route to the user folder logic used in 2014 hacks
        parts = path.split('/')
        filename = parts[-1]
        path = os.path.join('ds/v2-eu/user/', filename)

    file_path = os.path.join(ASSET_FOLDER, path)
    
    if os.path.isfile(file_path):
        logger.info(f'[GET] Serving: {path}')
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    
    logger.warning(f'[404] Missing Asset: {path}')
    return Response("Not Found", status=404)

if __name__ == '__main__':
    # Running on Port 80 is non-negotiable for the 'Strong' setup
    # because the DSi doesn't support custom ports for system domains.
    print("Sudomemo-style Proxy Server Active")
    print("Direct your DSi Primary DNS to this machine's IP.")
    app.run(host='0.0.0.0', port=80)
