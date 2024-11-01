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

const queue = require("oci-queue");
const core = require("oci-core");
const identity = require("oci-identity");
const common = require("oci-common");
const os = require("oci-objectstorage");

// Use this locally instead of env vars and region:
//const provider = new common.ConfigFileAuthenticationDetailsProvider();

const region = common.Region.EU_FRANKFURT_1;
const provider = new common.SimpleAuthenticationDetailsProvider(
  process.env.OCI_TENANCY,
  process.env.OCI_USER,
  process.env.OCI_FINGERPRINT,
  process.env.OCI_KEY,
  process.env.OCI_PASSPHRASE ? process.env.OCI_PASSPHRASE : '',
  region
);

// Q settings
const queueId = process.env.Q_ID;
const endpoint = process.env.Q_ENDPOINT;

(async () => {
    var res = "";
    try {
        
        const statsReq = {
          queueId: queueId
        };

        const getReq = {
          queueId: queueId,
          timeoutInSeconds: 2
        };

        const client = new queue.QueueClient({
          authenticationDetailsProvider: provider
        });
        
        client.endpoint = endpoint;
        
        console.log("Getting Queue stats .. ");
        var statsRes = await client.getStats(statsReq).catch(error => {
            console.log(error);
        });
        console.log(statsRes);
        
        console.log("Polling .. ");
        var getRes = await client.getMessages(getReq).catch(error => {
            console.log(error);
        });
        while(getRes && getRes.getMessages && getRes.getMessages.messages.length)
        {
            getRes.getMessages.messages.forEach(function(msg) {
                console.log(msg);
                var delReq = {
                  queueId: queueId,
                  messageReceipt: msg.receipt
                };
                client.deleteMessage(delReq);
            });
            console.log("Polling .. ");
            getRes = await client.getMessages(getReq).catch(error => {
                console.log(error);
            });
        }

        const d = new Date();
        console.log("Writing .. ");
        const putReq = {
          queueId: queueId,
          putMessagesDetails: { messages : [ { content: 'hello @ ' + d } ] }
        };
        
        const putRes = await client.putMessages(putReq);
        console.log(putRes);
        
    } catch (error) {
        console.log("Error: " + error);
        res = "error";
    } finally {
        return res;
    }
}) ();