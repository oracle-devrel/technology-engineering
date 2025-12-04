/*
Copyright (c) 2025 Oracle and/or its affiliates.

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

const identity = require("oci-identity");
const common = require("oci-common");
const objectstorage = require("oci-objectstorage");
const tailfile = require('@logdna/tail-file')
const loggingingestion = require("oci-loggingingestion");

const fs = require("fs");

async function start() {
    const configPath = process.env.config_path;
    console.log("PATH:" + configPath);
    const bucket = process.env.config_bucket;
    console.log("BUCKET:" + bucket);
    const logOcid = process.env.log_ocid;
    console.log("OCI LOG:" + logOcid);
    const logFile = process.env.log_file;
    console.log("LOG FILE:" + logFile);
    const reloadDelay = process.env.reload_delay;
    console.log("OS BUCKET CONFIG RELOAD (ms):" + reloadDelay);

    //const provider = new common.ConfigFileAuthenticationDetailsProvider("~/.oci/config");
    const provider = common.ResourcePrincipalAuthenticationDetailsProvider.builder();

    const osClient = new objectstorage.ObjectStorageClient({ authenticationDetailsProvider: provider });
    const logClient = new loggingingestion.LoggingClient({ authenticationDetailsProvider: provider });

    const nsRequest = {};
    const nsResponse = await osClient.getNamespace(nsRequest);
    const namespace = nsResponse.value;

    mount(osClient, namespace, bucket, configPath, reloadDelay);
    startTail(logClient, logOcid, logFile);
}

async function mount(osClient, namespace, bucket, path, reloadDelay)
{
 const listObjectsRequest = {
      namespaceName: namespace,
      bucketName:  bucket
 };
 const listObjectsResponse = await osClient.listObjects(listObjectsRequest);
 //console.log(listObjectsResponse.listObjects.objects);
 files = listObjectsResponse.listObjects.objects;
 for(i=0; i < files.length; i++) {
    //console.log(files[i].name);
    await downloadFile(osClient, namespace, bucket, files[i], path);
 }
 if(parseInt(reloadDelay) > 0) {
  setTimeout(function() {
    mount(osClient, namespace, bucket, path, reloadDelay);
  }, parseInt(reloadDelay));   
 } else {
    console.log("No reloading of bucket " + bucket + " since reload delay was " + reloadDelay);
 }
}

async function downloadFile(osClient, namespace, bucket, file, path)
{
   const getObjectRequest = {
            namespaceName: namespace,
            bucketName: bucket,
            objectName: file.name
    };
    const getObjectResponse = await osClient.getObject(getObjectRequest);
    //console.log(getObjectResponse);
    if(getObjectResponse.contentType.indexOf("directory") > 0) {
      console.log(file.name + " is a directory, creating .. ");
      fs.mkdir(path + "/" + file.name, (err) => {
        //if (err) console.log(err);
      });
    } else {
     var chunks = [];
     for await (let chunk of getObjectResponse.value) {
         chunks.push(chunk);
     }
     var buffer = Buffer.concat(chunks);
     await fs.writeFile(path + "/" + file.name, buffer, null, (err) => {
       if (err) {
         //console.log('Error writing file:', err);
         return;
       }
       console.log('File written successfully to' + path + "/" + file.name);
     });
  } 
}

async function startTail(logClient, logOcid, logFile)
{
  const tail = new tailfile(logFile, {encoding: 'utf8'})
  .on('data', (chunk) => {
    //console.log(`${chunk}`)
  //writeLog(logClient, logOcid, source,   subject,  type,      data)
    writeLog(logClient, logOcid, logFile,  logFile,  logFile,   `${chunk}`)
  })
  .on('tail_error', (err) => {
    console.error('TailFile had an error!', err)
  })
  .on('error', (err) => {
    console.error('A TailFile stream error was likely encountered', err)
  })
  .start()
  .catch((err) => {
    console.log("Cannot start.  Does " + logFile + "  exist?")
    setTimeout(function() {
        console.log("Trying again to open " + logFile + " ..");
        startTail(logClient, logOcid, logFile);
    }, 5000);
  });
}

async function writeLog(logClient, logOcid, source, subject, type, data)
{
  try {
        const putLogsDetails = {
          specversion: "1.0",
          logEntryBatches: [
            {
              entries: [
                {
                  id: subject,
                  data: data
                }
              ],
              source: source,
              type: type,
              subject: subject
            }
          ]
        };
        var putLogsRequest = loggingingestion.requests.PutLogsRequest = {
          logId: logOcid,
          putLogsDetails: putLogsDetails,
          timestampOpcAgentProcessing: new Date()
        };
        const putLogsResponse = await logClient.putLogs(putLogsRequest);
        //console.log("Wrote to log succesfully");
  } catch (err) {
    console.error('Log error: ' + err.message);
  }
}

start();