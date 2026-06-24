import fs from "fs";
import {
  NoRetryConfigurationDetails,
  SimpleAuthenticationDetailsProvider,
} from "oci-common";
import { GenerativeAiInferenceClient } from "oci-generativeaiinference";

export async function POST(req) {
  try {
    const { input } = await req.json();

    const privateKey = fs.readFileSync(
      process.env.ORACLE_PRIVATE_KEY_PATH,
      "utf8"
    );

    const provider = new SimpleAuthenticationDetailsProvider(
      process.env.ORACLE_TENANCY_ID,
      process.env.ORACLE_USER_ID,
      process.env.ORACLE_FINGERPRINT,
      privateKey,
      null, // passphrase, normalmente null
      null
    );

    const client = new GenerativeAiInferenceClient({
      authenticationDetailsProvider: provider,
    });

    client.endpoint = process.env.ORACLE_ENDPOINT;

    const servingMode = {
      modelId: process.env.ORACLE_MODEL_ID,
      servingType: "ON_DEMAND",
    };

    const chatRequest = {
      chatDetails: {
        compartmentId: process.env.ORACLE_COMPARTMENT_ID,
        servingMode: servingMode,
        chatRequest: {
          messages: [
            {
              role: "USER",
              content: [
                {
                  type: "TEXT",
                  text: input,
                },
              ],
            },
          ],
          apiFormat: "GENERIC",
          maxTokens: 600,
          temperature: 1,
          frequencyPenalty: 0,
          presencePenalty: 0,
          topP: 0.75,
        },
      },
      retryConfiguration: NoRetryConfigurationDetails,
    };

    const chatResponse = await client.chat(chatRequest);

    return Response.json({
      success: true,
      data: chatResponse,
    });
  } catch (error) {
    console.error("Error calling Oracle AI:", error);
    return Response.json(
      {
        success: false,
        error: error.message || "Failed to get response from Oracle AI",
      },
      { status: 500 }
    );
  }
}
