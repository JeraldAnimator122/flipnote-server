#!/usr/bin/env python3
import sys
import os
import cgi

# Importing your custom modules
from hatena import ServerLog, Silent
from DB import Database
from Hatenatools import TMB

def main():
    # 1. Handle the Request Method
    method = os.environ.get("REQUEST_METHOD", "GET")
    client_ip = os.environ.get("REMOTE_ADDR", "0.0.0.0")

    if method == "GET":
        ServerLog.write(f"{client_ip} got 403 when requesting post/flipnote.post with GET", Silent)
        print("Status: 405 Method Not Allowed")
        print("Content-Type: text/plain\n")
        print("405 - Method Not Allowed")
        return

    # 2. Grab the Channel from the URL (Query String)
    # This replaces request.args["channel"][0]
    query_string = os.environ.get("QUERY_STRING", "")
    params = cgi.parse_qs(query_string)
    channel = params.get("channel", [""])[0]

    # 3. Read the Raw Binary Data (The Flipnote)
    # This replaces request.content.read()
    try:
        content_length = int(os.environ.get("CONTENT_LENGTH", 0))
        data = sys.stdin.buffer.read(content_length)
    except (ValueError, TypeError):
        data = b""

    # 4. Database Logic
    add = Database.AddFlipnote(data, channel)

    if add:
        ServerLog.write(f"{client_ip} successfully uploaded \"{add[1]}.ppm\"", Silent)
        print("Status: 200 OK")
        print("Content-Type: text/plain\n")
    else:
        ServerLog.write(f"{client_ip} tried to upload a flipnote, but failed...", Silent)
        print("Status: 500 Internal Server Error")
        print("Content-Type: text/plain\n")

if __name__ == "__main__":
    main()
