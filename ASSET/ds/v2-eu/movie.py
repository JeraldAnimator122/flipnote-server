#!/usr/bin/env python3
import os
import sys
import cgi

# Importing your custom modules
from hatena import Log, ServerLog, Silent, NotFound
from DB import Database
from Hatenatools import TMB

# --- HTML TEMPLATES ---
DetailsPageTemplate = """<html>
	<head>
		<title>Flipnote</title>
		<meta name="upperlink" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.ppm">
		<meta name="starbutton" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star">
		<meta name="starbutton1" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=green">
		<meta name="starbutton2" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=red">
		<meta name="starbutton3" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=blue">
		<meta name="starbutton4" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=purple">
		<meta name="savebutton" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.ppm">
		<meta name="playcontrolbutton" content="">
		<link rel="stylesheet" href="http://flipnote.hatena.com/css/ds/basic.css">
	</head>
	<body>
		<table width="240" border="0" cellspacing="0" cellpadding="0" class="tab">
			<tr>
				<td class="border" width="5" align="center"><div class="border"></div></td>
				<td class="border" width="70" align="center"><div class="border"></div></td>
				<td class="border" width="95" align="center"><div class="border"></div></td>
			</tr>
			<tr>
				<td class="space"> </td>
				<td class="tabon" align="center"><div class="on" align="center">Description</div></td>
				<td class="taboff" align="center">
					<a class="taboff" href="%%Filename%%.htm?mode=commentshalfsize">Comments(%%CommentCount%%)</a>
				</td>
			</tr>
		</table>
		<div class="pad5b"></div>%%Spinoff%%
		<table width="226" border="0" cellspacing="0" cellpadding="0" class="detail">%%PageEntries%%</table>
	</body>
</html>"""

SpinoffTemplate1 = """
		<div class="notice2" align="center">
			This Flipnote is a spin-off.<br>
			<a href="%%Filename%%.htm">Original Flipnote</a>
		</div>"""

SpinoffTemplate2 = """
		<div class="notice2" align="center">
			This Flipnote is a spin-off.
		</div>"""

PageEntryTemplate = """
			<tr>
				<th width="90">
					<div class="item-term" align="left">%%Name%%</div>
				</th>
				<td width="136">
					<div class="item-value" align="right">%%Content%%</div>
				</td>
			</tr>"""

PageEntrySeparator = """
			<tr> </tr>
			<tr>
				<td colspan="2">
					<div class="hr"></div>
				</td>
			</tr>"""

def generate_details_page(creator_id, filename):
    flipnote = Database.GetFlipnote(creator_id, filename)
    if not flipnote:
        return "This flipnote doesn't exist!"
    
    tmb_data = Database.GetFlipnoteTMB(creator_id, filename)
    tmb = TMB().Read(tmb_data)
    if not tmb:
        return "This flipnote is corrupt!"
    
    # Spinoff Logic
    spinoff = ""
    if tmb.OriginalAuthorID != tmb.EditorAuthorID or tmb.OriginalFilename != tmb.CurrentFilename:
        if Database.FlipnoteExists(tmb.OriginalAuthorID, tmb.OriginalFilename[:-4]):
            spinoff = SpinoffTemplate1.replace("%%Filename%%", tmb.OriginalFilename[:-4])
        elif tmb.OriginalAuthorID != tmb.EditorAuthorID:
            spinoff = SpinoffTemplate2
    
    # Build Table Entries
    entries = []
    
    # Creator
    creator_link = f'<a href="http://flipnote.hatena.com/ds/v2-xx/{creator_id}/profile.htm?t=260&pm=80">{tmb.Username}</a>'
    entries.append(PageEntryTemplate.replace("%%Name%%", "Creator").replace("%%Content%%", creator_link))
    
    # Stars (0=Yellow, 1=Green, 2=Red, 3=Blue, 4=Purple)
    star_html = ""
    for i in range(5):
        count = flipnote[i+2]
        star_html += f'<br/><a href="#"><span class="star{i}c">\u2605</span> <span class="star{i}">{count}</span></a>'
    entries.append(PageEntryTemplate.replace("%%Name%%", "Stars").replace("%%Content%%", star_html))
    
    # Views & Downloads
    entries.append(PageEntryTemplate.replace("%%Name%%", "Views").replace("%%Content%%", str(flipnote[1])))
    entries.append(PageEntryTemplate.replace("%%Name%%", "Downloads").replace("%%Content%%", str(flipnote[8])))

    return DetailsPageTemplate.replace("%%CreatorID%%", creator_id) \
                              .replace("%%Filename%%", filename) \
                              .replace("%%CommentCount%%", "0") \
                              .replace("%%Spinoff%%", spinoff) \
                              .replace("%%PageEntries%%", PageEntrySeparator.join(entries))

def send_response(body, status="200 OK", content_type="text/plain"):
    sys.stdout.write(f"Status: {status}\r\n")
    sys.stdout.write(f"Content-Type: {content_type}\r\n")
    sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n")
    if isinstance(body, str):
        sys.stdout.write(body)
    else:
        sys.stdout.buffer.write(body)

def main():
    path = os.environ.get("PATH_INFO", "")
    client_ip = os.environ.get("REMOTE_ADDR", "0.0.0.0")
    
    # Expected path format: /movie/[CreatorID]/[Filename].[ext]
    parts = path.strip("/").split("/")
    if len(parts) < 3:
        send_response("403 Forbidden", "403 Forbidden")
        return

    creator_id = parts[1]
    filename_ext = parts[2]
    filename = ".".join(filename_ext.split(".")[:-1])
    filetype = filename_ext.split(".")[-1].lower()

    # Access checks
    if not Database.CreatorExists(creator_id) or not Database.FlipnoteExists(creator_id, filename):
        send_response("404 Not Found", "404 Not Found")
        return

    # Handle file types
    if filetype == "ppm":
        Log(None, path)
        Database.AddView(creator_id, filename)
        data = Database.GetFlipnotePPM(creator_id, filename)
        send_response(data, content_type="application/octet-stream")

    elif filetype == "info":
        Log(None, path, True)
        send_response("0\n0\n")

    elif filetype == "htm":
        html = generate_details_page(creator_id, filename)
        send_response(html, content_type="text/html; charset=UTF-8")

    elif filetype == "star":
        star_count = os.environ.get("HTTP_X_HATENA_STAR_COUNT")
        query = cgi.parse_qs(os.environ.get("QUERY_STRING", ""))
        color = query.get('starcolor', ['yellow'])[0]

        if not star_count or not (1 <= int(star_count) <= 65535):
            ServerLog.write(f"{client_ip} invalid star header on {path}", Silent)
            send_response("Invalid Star Header", "403 Forbidden")
            return

        if Database.AddStar(creator_id, filename, int(star_count), color):
            ServerLog.write(f"{client_ip} added {star_count} {color} stars to {creator_id}/{filename}", Silent)
            send_response("Success")
        else:
            send_response("Database Error", "500 Internal Server Error")

    elif filetype == "dl":
        Log(None, path, True)
        Database.AddDownload(creator_id, filename)
        send_response("Noted ;)")

    else:
        send_response("403 Forbidden", "403 Forbidden")

if __name__ == "__main__":
    main()
