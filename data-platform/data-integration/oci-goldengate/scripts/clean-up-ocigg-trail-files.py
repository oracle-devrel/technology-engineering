/*
Copyright (c) 2021 Oracle and/or its affiliates.

The Universal Permissive License (UPL), Version 1.0

Subject to the condition set forth below, permission is hereby granted to any
person obtaining a copy of this software, associated documentation and/or data
(collectively the "Software"), free of charge and under any and all copyright
rights in the Software, and any and all patent rights owned or freely
licensable by each licensor hereunder covering either (i) the unmodified
Software as contributed to or provided by such licensor, or (ii) the Larger
Works (as defined below), to deal in both

(a) the Software, and
(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
one is included with the Software (each a "Larger Work" to which the Software
is contributed by such licensors),

without restriction, including without limitation the rights to copy, create
derivative works of, display, perform, and distribute the Software and make,
use, sell, offer for sale, import, export, have made, and have sold the
Software and the Larger Work(s), and to sublicense the foregoing rights on
either these or other terms.

This license is subject to the following condition:
The above copyright notice and either this complete permission notice or at
a minimum a reference to the UPL must be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

### Import Packages
import oci
import requests
import json
from base64 import b64encode
import base64

# Auth Config
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

#OCI GoldenGate API
version ="v2"
username = '<gg username>'
password = '<password>'
issueCommand=f'/services/{version}/commands/execute'

#OCI GoldenGate deployment name
sourceUrl = "https://<OCI GG URL>"

encoded_credentials = b64encode(bytes(f'{username}:{password}',
                                encoding='ascii')).decode('ascii') 

auth_header = f'Basic {encoded_credentials}' 
payload=""
header = f'{auth_header}' 
headers = {
'Authorization':  header,
'Cookie': ''
}

#initilize service client
golden_gate_client = oci.golden_gate.GoldenGateClient(config)

#function to delete trail
def deleteTrail(inputHearders, inputBody,url):
    responsePost = requests.post(url+issueCommand, headers=inputHearders, json=inputBody)
    print (responsePost.json())

list_trail_files_response = golden_gate_client.list_trail_files(
    deployment_id="<OCI ID for OCI GG deployment>")

#data dictionary for trail files
data_dict = json.loads(str(list_trail_files_response.data.items))

#iterate through trail files
for i in data_dict:
#Only for trails that are not currently in use by any extract or replicat.
    if i['consumers'] == None and i['producer'] == None:
       #print(i['consumers'], i['producer'], i['trail_file_id'])
        trailsDict={
         "name": "purge", 
         "purgeType": "trails", 
         "trails": [ { "name": i['trail_file_id'] } ], 
         "useCheckpoints": False, 
         "keep": [ { 
         "type": "min", 
         "units": "files", 
         "value": 0}]
        }
        #delete trail
        deleteTrail(headers,trailsDict,sourceUrl)