#!/usr/bin/python

import getopt
import requests
import socket
import getpass
import sys
import base64
import urllib
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def api_call (url, op_type, user, password, token):
    if not token:
        resp = requests.post(url, verify=False, auth=(user, password)).json()
    else:
        auth = "Bearer " + token
        headers = { 'Authorization': auth, }
        if op_type == "GET":
            resp = requests.get (url, headers=headers, verify=False).json()
        elif op_type == "DELETE":
            resp = requests.delete(url,  headers=headers, verify=False)
    try: resp['errors']
    except KeyError: return (resp)
    except TypeError: return (resp)
    sys.stderr.write("ERROR: " + resp['errors'][0]['message'] + "\n")
    exit (1)

DEBUG = False
# Get Session Token / Validates connection
addr = socket.gethostbyname(sys.argv[1])
url_head = "https://" + addr + "/api/"
user = raw_input("User: ")
password = getpass.getpass ("Password: ")
url = url_head + "v1/session"
resp = api_call (url, 'POST', user, password, '')
try: resp['token']
except KeyError:
    sys.stderr.write("No token found, re-check credentials.\n")
    exit (5)
token = resp['token']
print "Connection Validated"
#
# Get Additional Data
#
nas_host = raw_input ("NAS Host: ")
share = raw_input("Share Name/Export Path: ")
fileset = raw_input("Fileset: ")
delete_snaps = raw_input("Delete the snaps? (y/n): ")
preserve_snaps = "true"
if delete_snaps == "Y" or delete_snaps == "y":
    preserve_snaps = "false"
share_type = "SMB"
if share.startswith("/"):
    share_type = "NFS"
done = False
first = True
ShareID = ""
while not done:
    if first:
        url = url_head + "internal/host/share"
    else:
        url = "https://" + url_next
    resp = api_call (url, 'GET', '', '', token)
    first = False
    for x, y in enumerate(resp['data']):
        if y['hostname'] == nas_host and y['shareType'] == share_type and y['exportPoint'] == share:
            done = True
            ShareID = urllib.quote_plus(y['id'])
            ShareID_s = y['id']
            break
    if resp['hasMore'] == 'true':
        url_next = resp['links']['next']['href']
    else:
        done = True
if not ShareID:
    sys.stderr.write ("Can't find Share\n")
    exit (2)
if DEBUG:
    print ShareID
done = False
first = True
filesetID = ""
while not done:
    if first:
        url = url_head + "v1/fileset?share_id=" + ShareID
    else:
        if DEBUG:
            print "Calling next"
        url = "https://" + url_next
    resp = api_call (url, 'GET', '', '', token)
    first = False
    for x, y in enumerate(resp['data']):
        if y['shareId'] == ShareID_s and y['name'] == fileset:
            done = True
            filesetID = urllib.quote_plus(y['id'])
            break
    if resp['hasMore'] == True:
        url_next = resp['links']['next']['href']
    else:
        done = True
if not filesetID:
    sys.stderr.write ("Can't find Fileset\n")
    exit (3)
if DEBUG:
    print filesetID
url = url_head + "v1/fileset/" + filesetID + "?preserve_snapshots=" + preserve_snaps
if DEBUG:
    print url
resp = api_call (url, 'DELETE', '', '', token)
print "Done"

