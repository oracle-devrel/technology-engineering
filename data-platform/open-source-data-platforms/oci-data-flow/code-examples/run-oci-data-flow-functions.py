# Copyright (c) 2023 Oracle and/or its affiliates.
# 
# The Universal Permissive License (UPL), Version 1.0
# 
# Subject to the condition set forth below, permission is hereby granted to any
# person obtaining a copy of this software, associated documentation and/or data
# (collectively the "Software"), free of charge and under any and all copyright
# rights in the Software, and any and all patent rights owned or freely
# licensable by each licensor hereunder covering either (i) the unmodified
# Software as contributed to or provided by such licensor, or (ii) the Larger
# Works (as defined below), to deal in both
# 
# (a) the Software, and
# (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
# one is included with the Software (each a "Larger Work" to which the Software
# is contributed by such licensors),
# without restriction, including without limitation the rights to copy, create
# derivative works of, display, perform, and distribute the Software and make,
# use, sell, offer for sale, import, export, have made, and have sold the
# Software and the Larger Work(s), and to sublicense the foregoing rights on
# either these or other terms.
# 
# This license is subject to the following condition:
# The above copyright notice and either this complete permission notice or at
# a minimum a reference to the UPL must be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import io
import json
import logging
import oci
import os
import requests
import sys

from fdk import response
from oci.signer import Signer

def handler(ctx, data: io.BytesIO=None):
    # Really doesn't belong here, unsure how to enable logging remotely otherwise.
    logging.basicConfig(level=logging.INFO)

    retval = dict()
    # For extra debugging, uncomment this. Populate the initial return value.
    # retval = dict(os.environ)

    # Get an appropriate signer, automatically.
    logging.info('Using resource principal for private key')
    signer = oci.auth.signers.get_resource_principals_signer()

    # Ensure we got valid JSON input and all fields accounted for.
    try:
        body = json.loads(data.getvalue())
        body = body['data']
        for item in ['resourceName']:
            if item not in body:
                retval['error'] = 'Missing mandatory field ' + item
                return response.Response(
                        ctx,
                        response_data=json.dumps(retval),
                        headers={"Content-Type": "application/json"})

        applicationId = body.get('applicationId','<OCI ID application data flow>')
        compartmentId = body.get('compartmentId','<Compartment ID>')
        displayName = body.get('displayName','MaterialInventory')
        #driverShape = body.get('driverShape','VM.Standard2.1')
        #executorShape = body.get('executorShape','VM.Standard2.1')
        numExecutors = body.get('numExecutors',1)
        pool_id = '<Pool ID>'
        region = body.get('region', '<Regios>')

        resourceName = body.get('resourceName')

        if 'parameters' not in body:
            parameters = dict()
        else:
            parameters = body.get('parameters')
        parameters['input-path'] = 'oci://<bucket name>@<namespace bucket>/{}'.format(resourceName)
        logging.info(parameters['input-path'])

    except (Exception, ValueError) as ex:
        retval['error'] = str(ex)
        return response.Response(
                ctx,
                response_data=json.dumps(retval),
                headers={"Content-Type": "application/json"})

    # Call Data Flow.
    dataflow_root = 'https://dataflow.{}.oci.oraclecloud.com/20200129'.format(region)
    dataflow_runs_endpoint = dataflow_root + '/runs'
    run_payload = dict(
        compartmentId=compartmentId,
        applicationId=applicationId,
        displayName=displayName,
        applicationSettings=dict(
            #driverShape=driverShape,
            #executorShape=executorShape,
            numExecutors=numExecutors,
            pool_id=pool_id,
            arguments=[
                dict(name=key, value=value) for key, value in parameters.items()
            ]
        ),
    )
    retval['run_payload'] = run_payload
    try:
        result = requests.post(
                dataflow_runs_endpoint,
                json=run_payload,
                auth=signer)
        result_obj = json.loads(result.text)
        if 'id' not in result_obj:
            retval['error'] = result.text
        else:
            runid = result_obj['id']
            retval['runid'] = result_obj['id']
    except Exception as ex:
        retval['error'] = str(ex)
    return response.Response(ctx,
            response_data=json.dumps(retval),
            headers={"Content-Type": "application/json"})

if __name__ == '__main__':
    from fdk import context
    ctx = context.InvokeContext(None, None, None)

    # Read stdin and turn it into BytesIO
    input = io.BytesIO(sys.stdin.read().encode())
    retval = handler(ctx, input)
    print(retval.body())