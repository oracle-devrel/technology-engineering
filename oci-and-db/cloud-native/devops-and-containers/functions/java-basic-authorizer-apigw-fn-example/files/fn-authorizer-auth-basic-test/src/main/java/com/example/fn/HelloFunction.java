package com.example.fn;

import com.fnproject.fn.api.RuntimeContext;
import com.fnproject.fn.api.httpgateway.HTTPGatewayContext;
import com.fnproject.fn.api.InputEvent;

public class HelloFunction {

    public String handleRequest(final HTTPGatewayContext hctx, final InputEvent input) {
        
        // Use header transformation in APIGW Route to get username in headers from authorizer
        // Overwrite	username     ${request.auth[username]}
        String username = hctx.getHeaders().get("username").orElse("");
        return "Username: " + username;
    }
}