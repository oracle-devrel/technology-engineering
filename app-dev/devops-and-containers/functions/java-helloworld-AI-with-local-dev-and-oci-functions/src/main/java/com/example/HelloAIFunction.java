package com.example;

import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.ConfigFileReader;
import com.oracle.bmc.Region;
import com.oracle.bmc.auth.AuthenticationDetailsProvider;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
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

import java.io.*;
import java.util.*;
import java.text.*;

public class HelloAIFunction {

    // FILL IN PROPER VALUES FOR OCI GENAI SERVICE
    private static final String ENDPOINT       = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com";
    private static final Region REGION         = Region.EU_FRANKFURT_1;

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
                    .servingMode(OnDemandServingMode.builder().modelId("ocid1.generativeaimodel.oc1.eu-frankfurt-1.amaaaaaask7dceyazi3cpmptwa52f7dgwyskloughcxtjgrqre3pngwtig4q").build())
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
        return answer;
    }

}