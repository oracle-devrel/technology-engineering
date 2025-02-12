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

package com.example;

import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.ConfigFileReader;
import com.oracle.bmc.Region;
import com.oracle.bmc.auth.AuthenticationDetailsProvider;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.auth.ConfigFileAuthenticationDetailsProvider;
import com.oracle.bmc.auth.StringPrivateKeySupplier;
import com.oracle.bmc.auth.SimpleAuthenticationDetailsProvider;
import com.oracle.bmc.generativeaiinference.GenerativeAiInferenceClient;
import com.oracle.bmc.generativeaiinference.model.ChatDetails;
import com.oracle.bmc.generativeaiinference.model.CohereChatRequest;
import com.oracle.bmc.generativeaiinference.model.CohereMessage;
import com.oracle.bmc.generativeaiinference.model.DedicatedServingMode;
import com.oracle.bmc.generativeaiinference.requests.ChatRequest;
import com.oracle.bmc.generativeaiinference.responses.ChatResponse;
import com.oracle.bmc.generativeaiinference.model.BaseChatRequest.ApiFormat;
import com.oracle.bmc.generativeaiinference.model.ChatChoice;
import com.oracle.bmc.generativeaiinference.model.ChatContent;
import com.oracle.bmc.generativeaiinference.model.ChatContent.Type;
import com.oracle.bmc.generativeaiinference.model.ChatResult;
import com.oracle.bmc.generativeaiinference.model.Message;
import com.oracle.bmc.generativeaiinference.model.OnDemandServingMode;
import com.oracle.bmc.generativeaiinference.model.ServingMode;
import com.oracle.bmc.generativeaiinference.model.TextContent;
import com.oracle.bmc.retrier.RetryConfiguration;

import java.time.LocalDate;
import java.io.*;
import java.util.*;
import java.text.*;

public class HelloAIFunction {

    // FILL IN PROPER VALUES FOR OCI GENAI SERVICE
    private static final String ENDPOINT       = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com";
    private static final Region REGION         = Region.EU_FRANKFURT_1;
    private static final String COMPARTMENT_ID = "ocid1.compartment.oc1..";
    private static final String GENAI_OCID     = "ocid1.generativeaimodel.oc1.eu-frankfurt-1.amaaaaaa....wtig4q";

    // FILL IN PROPER VALUES FOR IAM USER WHEN RUNNING LOCALLY WITH Fn. RUNNING AS OCI FUNCTION DO NOT NEED TO SET THESE.
    private static final String TENANCY_ID     = "ocid1.tenancy.oc1..";
    private static final String USER_ID        = "ocid1.user.oc1..";
    private static final String FINGERPRINT    = "ef:4d:..";
    private static final String PRIVATEKEY     = "-----BEGIN PRIVATE KEY-----\n .. \n-----END PRIVATE KEY-----";
    private static final String PASSPHRASE     = "";

    public String handleRequest(String input) {
        GenerativeAiInferenceClient generativeAiInferenceClient = null;
        String answer = "";

        LocalDate date = LocalDate.now().minusYears(100);
        String questionToAI = (input == null || input.isEmpty()) ? "What happened at " + date + " ?": input;

        try {
                ResourcePrincipalAuthenticationDetailsProvider resourcePrincipalAuthenticationDetailsProvider =
                        ResourcePrincipalAuthenticationDetailsProvider.builder().build();
                generativeAiInferenceClient =
                        GenerativeAiInferenceClient.builder()
                                .region(REGION)
                                .endpoint(ENDPOINT)
                                .build(resourcePrincipalAuthenticationDetailsProvider);

        } catch (Exception e) {
                try {
                        ConfigFileAuthenticationDetailsProvider configFileAuthenticationDetailsProvider =
                                new ConfigFileAuthenticationDetailsProvider("/config", "DEFAULT");
                        generativeAiInferenceClient =
                                GenerativeAiInferenceClient.builder()
                                        .region(REGION)
                                        .endpoint(ENDPOINT)
                                        .build(configFileAuthenticationDetailsProvider);
                } catch (Exception ee) {
                        try {
                                AuthenticationDetailsProvider authenticationDetailsProvider =
                                        SimpleAuthenticationDetailsProvider.builder()
                                                .tenantId(TENANCY_ID)
                                                .userId(USER_ID)
                                                .fingerprint(FINGERPRINT)
                                                .privateKeySupplier(new StringPrivateKeySupplier(PRIVATEKEY))
                                                .passPhrase(PASSPHRASE)
                                                .build();
                                generativeAiInferenceClient =
                                        GenerativeAiInferenceClient.builder()
                                                .region(REGION)
                                                .endpoint(ENDPOINT)
                                                .build(authenticationDetailsProvider);
                        } catch (Exception eee) {
                                answer = answer + "\n" + eee.getMessage();
                        }
                }
        }

        if(answer.length() == 0)
        {
                try {
                        CohereChatRequest chatRequest = CohereChatRequest.builder()
                                .message(questionToAI)
                                .maxTokens(600)
                                .temperature((double)0)
                                .frequencyPenalty((double)1)
                                .topP((double)0.75)
                                .topK((int)0)
                                .isStream(false)
                                .build();

                        ChatDetails chatDetails = ChatDetails.builder()
                                .servingMode(OnDemandServingMode.builder().modelId(GENAI_OCID).build())
                                .compartmentId(COMPARTMENT_ID)
                                .chatRequest(chatRequest)
                                .build();

                        ChatRequest request = ChatRequest.builder()
                                .chatDetails(chatDetails)
                                .build();

                        ChatResponse chatResponse = generativeAiInferenceClient.chat(request);
                        String answerAI = chatResponse.toString();
                        answerAI = answerAI.substring(answerAI.indexOf("text=") + 5);
                        if(answerAI.indexOf(", chatHistory=") > 0) {
                                answerAI = answerAI.substring(0, answerAI.indexOf(", chatHistory="));
                        }
                        answer = questionToAI + "\n\n" + answerAI;

                } catch (Exception e) {
                        answer = answer + "\n" + e.getMessage();
                }
        }
        return answer;
    }
}