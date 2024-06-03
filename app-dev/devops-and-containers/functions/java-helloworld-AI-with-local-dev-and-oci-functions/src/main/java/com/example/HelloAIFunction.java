package com.example;


import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.ConfigFileReader;
import com.oracle.bmc.Region;
import com.oracle.bmc.auth.AuthenticationDetailsProvider;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.auth.StringPrivateKeySupplier;
import com.oracle.bmc.auth.SimpleAuthenticationDetailsProvider;
import com.oracle.bmc.generativeaiinference.GenerativeAiInferenceClient;
import com.oracle.bmc.generativeaiinference.model.CohereLlmInferenceRequest;
import com.oracle.bmc.generativeaiinference.model.DedicatedServingMode;
import com.oracle.bmc.generativeaiinference.model.GenerateTextDetails;
import com.oracle.bmc.generativeaiinference.model.LlamaLlmInferenceRequest;
import com.oracle.bmc.generativeaiinference.model.OnDemandServingMode;
import com.oracle.bmc.generativeaiinference.model.SummarizeTextDetails;
import com.oracle.bmc.generativeaiinference.requests.GenerateTextRequest;
import com.oracle.bmc.generativeaiinference.requests.SummarizeTextRequest;
import com.oracle.bmc.generativeaiinference.responses.GenerateTextResponse;
import com.oracle.bmc.retrier.RetryConfiguration;

import java.io.*;
import java.util.*;
import java.text.*;

public class HelloAIFunction {

    // FILL IN PROPER VALUES FOR OCI GENAI SERVICE
    private static final String ENDPOINT       = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com";
    private static final Region REGION         = Region.US_CHICAGO_1;

    // FILL IN PROPER VALUES FOR IAM USER WHEN NOT USING INSTANCE_PRINCIPAL IN OCI FUNCTION
    private static final String COMPARTMENT_ID = "ocid1.compartment.oc1..";
    private static final String TENANCY_ID     = "ocid1.tenancy.oc1..";
    private static final String USER_ID        = "ocid1.user.oc1..";
    private static final String FINGERPRINT    = "ef:4d:..";
    private static final String PRIVATEKEY     = "-----BEGIN PRIVATE KEY-----\n .. \n-----END PRIVATE KEY-----";
    private static final String PASSPHRASE     = "";

    public String handleRequest(String input) {
        GenerativeAiInferenceClient generativeAiInferenceClient;
        String answer = "";
        try {
            Date date = new Date();
            SimpleDateFormat dateFormat = new SimpleDateFormat("MM/dd/yyyy");
            String currentDate = dateFormat. format(date);
            String questionToAI = (input == null || input.isEmpty()) ? "What happened today " + currentDate + " 100 years ago ?": input;

            // OCI FUNCTION CONFIG VAR "AUTH_INSTANCE_PRINCIPAL" FOR INSTANCE_PRINCIPAL AUTH (ANY VALUE)
            if(System.getenv("AUTH_INSTANCE_PRINCIPAL") != null) {
                System.out.println("AUTH_INSTANCE_PRINCIPAL");
                ResourcePrincipalAuthenticationDetailsProvider resourcePrincipalAuthenticationDetailsProvider =
                        ResourcePrincipalAuthenticationDetailsProvider.builder().build();
                generativeAiInferenceClient =
                        GenerativeAiInferenceClient.builder()
                                .region(REGION)
                                .endpoint(ENDPOINT)
                                .build(resourcePrincipalAuthenticationDetailsProvider);

            } else {
                System.out.println("AUTH_USER");
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
            }

            CohereLlmInferenceRequest llmInferenceRequest =
                    CohereLlmInferenceRequest.builder()
                            .prompt(questionToAI)
                            .maxTokens(600)
                            .temperature((double)1)
                            .frequencyPenalty((double)0)
                            .topP((double)0.99)
                            .isStream(false)
                            .isEcho(false)
                            .build();

            GenerateTextDetails generateTextDetails = GenerateTextDetails.builder()
                    .servingMode(OnDemandServingMode.builder()
                            .modelId("ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyafhwal37hxwylnpbcncidimbwteff4xha77n5xz4m7p6a").build())
                    .compartmentId(COMPARTMENT_ID)
                    .inferenceRequest(llmInferenceRequest)
                    .build();

            GenerateTextRequest generateTextRequest = GenerateTextRequest.builder()
                    .generateTextDetails(generateTextDetails)
                    .build();

            GenerateTextResponse generateTextResponse = generativeAiInferenceClient.generateText(generateTextRequest);
            String answerAI = generateTextResponse.toString();
            answerAI = answerAI.substring(answerAI.indexOf("text= ") + 6);
            if(answerAI.indexOf(", likelihood") > 0) {
                answerAI = answerAI.substring(0, answerAI.indexOf(", likelihood"));
            }
            answer = questionToAI + "\n\n" + answerAI;

        } catch (Exception e) {
            answer = answer + "\n" + e.getMessage();
        }
        return answer;
    }

}