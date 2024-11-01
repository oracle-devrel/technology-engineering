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

const fdk=require('@fnproject/fdk');
const core = require("oci-core");
const common = require("oci-common");
const os = require("oci-objectstorage");

fdk.handle(async function(event){
  //console.log(event);
  var res = "ok";
  const provider = common.ResourcePrincipalAuthenticationDetailsProvider.builder();
  const client = new os.ObjectStorageClient({
    authenticationDetailsProvider: provider
  });
  try {
    console.log("Running os replication .. ");
    if(event.data && event.data.resourceName)
    {
        var file = event.data.resourceName;
        console.log(file);
        var ns = process.env.NAMESPACE;
        var sourceBucketName = process.env.SOURCE_BUCKET;
        var targetBucketNames = process.env.TARGET_BUCKETS;
        console.log("Reading " + file + " from " + sourceBucketName);
        var getObjectRequest = {
            namespaceName: ns,
            bucketName: sourceBucketName,
            objectName: file
        };
        var getObjectResponse = await client.getObject(getObjectRequest).catch(error => {
            console.log(error);
            res = error;
        });
        if(res == "ok") {
            console.log(getObjectResponse.value._readableState.buffer.head.data);
            var chunks = [];
            for await (let chunk of getObjectResponse.value) {
                chunks.push(chunk);
            }
            var buffer = Buffer.concat(chunks);
            //console.log(buffer);
            var targetbucketName = targetBucketNames.split(",");
            for (var i = 0; i < targetbucketName.length; i++) 
            {
                console.log("Writing " + file + " to " + targetbucketName[i]);
                var putObjectRequest = {
                    namespaceName: ns,
                    bucketName: targetbucketName[i],
                    putObjectBody: buffer,
                    objectName: file,
                    contentLength: buffer.length
                };
                var putObjectResponse = await client.putObject(putObjectRequest).catch(error => {
                    console.log(error);
                    res = error;
                    i = targetbucketName[i].length;
                });
            }
        }
    } 
  } catch (error) {
        console.log("Error: " + error);
        res = "Replication error " + error;
  } finally {
        return res;
  }
})
