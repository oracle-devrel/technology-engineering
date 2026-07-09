# -----------------------------------------------------------------------------
# Copyright (c) 2026 Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/
#
# You may use, copy, modify, and distribute this software and its documentation
# under the terms of the UPL. This software is provided "AS IS" without warranty
# of any kind.
#
# Oracle does not provide support for this script; community support only.
# This software is provided as it is and need to be considered an example
# of a possible implementation rather than for general use. 
#
# Script provided by: Cristiano Ghirardi, Oracle employee
# -----------------------------------------------------------------------------

import io
import json
import logging

from fdk import response


def handler(ctx, data: io.BytesIO = None):
    name = "World"
    try:
        body = json.loads(data.getvalue())
        name = body.get("name")
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))

    logging.getLogger().info("Inside Python Hello World function")
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "Hello {0}".format(name)}),
        headers={"Content-Type": "application/json"}
    )
