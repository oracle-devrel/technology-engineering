const TailFile = require('@logdna/tail-file')
const identity = require("oci-identity");
const common = require("oci-common");
const loggingingestion = require("oci-loggingingestion");
const objectstorage = require("oci-objectstorage");
const fs = require("fs");

async function start() {

const log_ocid = process.env.log_ocid;
console.log("OCI LOG:" + log_ocid);

const log_file = process.env.log_file;
console.log("ACCESS LOG:" + log_file);

const www_path = process.env.www_path;
console.log("WWW DATA:" + www_path);

const bucket = process.env.os_bucket;
console.log("OS BUCKET:" + bucket);

const provider = new common.ConfigFileAuthenticationDetailsProvider("config");
//const provider = common.ResourcePrincipalAuthenticationDetailsProvider.builder();
const logClient = new loggingingestion.LoggingClient({ authenticationDetailsProvider: provider });
const osClient = new objectstorage.ObjectStorageClient({ authenticationDetailsProvider: provider });

// Get OS namespace
const nsRequest = {};
const nsResponse = await osClient.getNamespace(nsRequest);
const namespace = nsResponse.value;

// Mount "filesystem" from OS
mount(osClient, namespace, bucket, www_path);

// Start tailing to OCI Logging
const tail = new TailFile(log_file, {encoding: 'utf8'})
  .on('data', (chunk) => {
    console.log(`${chunk}`)
    writeLog(logClient, log_ocid, 'nginx', 'nginx', `${chunk}`)
  })
  .on('tail_error', (err) => {
    console.error('TailFile had an error!', err)
  })
  .on('error', (err) => {
    console.error('A TailFile stream error was likely encountered', err)
  })
  .start()
  .catch((err) => {
    console.error('Cannot start.  Does " + log_file + " exist?', err)
  })
}

async function mount(osClient, namespace, bucket, www_path)
{
 const listObjectsRequest = {
      namespaceName: namespace,
      bucketName:  bucket
 };
 const listObjectsResponse = await osClient.listObjects(listObjectsRequest);
 //console.log(listObjectsResponse.listObjects.objects);
 files = listObjectsResponse.listObjects.objects;
 for(i=0; i < files.length; i++) {
    console.log(files[i].name);
    await downloadFile(osClient, namespace, bucket, files[i], www_path);
 }
 
  setTimeout(function() {
    mount(osClient, namespace, bucket, www_path);
  }, 5000);
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
      //console.log(path + "/" + file.name);
      fs.mkdir(path + "/" + file.name, (err) => {
        if (err) console.log(err);
      });
    } else {
     var chunks = [];
     for await (let chunk of getObjectResponse.value) {
         chunks.push(chunk);
     }
     var buffer = Buffer.concat(chunks);
     //console.log(buffer.toString());
     console.log(path + "/" + file.name);
     await fs.writeFile(path + "/" + file.name, buffer.toString(), 'utf8', (err) => {
      if (err) {
        console.log('Error writing file:', err);
        return;
      }
      console.log('File written to' + path + "/" + file.name);
     });
    }
}

async function writeLog(logClient, log_ocid, subject, type, data)
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
              source: "nginx-logging-sidecar",
              type: type,
              subject: subject
            }
          ]
        };
        var putLogsRequest = loggingingestion.requests.PutLogsRequest = {
          logId: log_ocid,
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