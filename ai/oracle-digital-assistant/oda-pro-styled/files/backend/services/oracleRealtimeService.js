const ffmpeg = require("fluent-ffmpeg");
const SpeechClient = require("@oracle/oci-ai-speech-realtime");
const oci = require("oci-sdk");
const path = require("path");
const fs = require("fs");

const oracleRealtimeService = {
  client: null,
  listener: null,

  createListener() {
    console.log("🔧 Creating listener...");
    this.listener = {
      onError: function (error) {
        console.error("❌ Listener Error:", error);
      },
      onClose: function (closeEvent) {
        console.log("🔒 Listener Close:", closeEvent);
      },
      onConnect: function (event) {
        console.log("✅ Listener Connect:", event);
      },
      onConnectMessage: function (message) {
        console.log("📨 Listener ConnectMessage:", message);
      },
      onResult: function (result) {
        console.log("📝 Listener Result:", result);
      },
      onAckAudio: function (ack) {
        console.log("🎵 Listener AckAudio:", ack);
      },
    };

    console.log("🔧 Listener created:", Object.keys(this.listener));
    return this.listener;
  },

  getAuthenticationDetails() {
    console.log("🔐 Creating authentication provider...");

    const privateKeyPath = path.resolve(
      __dirname,
      "..",
      process.env.ORACLE_PRIVATE_KEY
    );
    const privateKeyContent = fs.readFileSync(privateKeyPath, "utf8");

    const provider = new oci.SimpleAuthenticationDetailsProvider(
      process.env.ORACLE_TENANCY_ID,
      process.env.ORACLE_USER_ID,
      process.env.ORACLE_FINGERPRINT,
      privateKeyContent,
      null,
      process.env.ORACLE_REGION
    );

    console.log("🔐 Provider created correctly");
    return provider;
  },

  createClientParams() {
    const params = {
      encoding: "audio/raw;rate=16000",
      isAckEnabled: false,
      partialSilenceThresholdInMs: 100,
      finalSilenceThresholdInMs: 500,
      stabilizePartialResults: "NONE",
      modelDomain: "GENERIC",
      languageCode: "en-US",
      punctuation: true,
      compartmentId: process.env.ORACLE_COMPARTMENT_ID,
    };

    console.log("⚙️ Client params:", params);
    return params;
  },

  async getConnectionDetails() {
    console.log("🚀 === STARTING getConnectionDetails ===");

    try {
      console.log("📍 Verifying environment variables...");
      console.log("- ORACLE_REGION:", process.env.ORACLE_REGION);
      console.log(
        "- ORACLE_TENANCY_ID:",
        process.env.ORACLE_TENANCY_ID ? "✓" : "✗"
      );
      console.log("- ORACLE_USER_ID:", process.env.ORACLE_USER_ID ? "✓" : "✗");
      console.log(
        "- ORACLE_COMPARTMENT_ID:",
        process.env.ORACLE_COMPARTMENT_ID ? "✓" : "✗"
      );
      console.log(
        "- ORACLE_FINGERPRINT:",
        process.env.ORACLE_FINGERPRINT ? "✓" : "✗"
      );
      console.log(
        "- ORACLE_PRIVATE_KEY:",
        process.env.ORACLE_PRIVATE_KEY ? "✓" : "✗"
      );

      const provider = this.getAuthenticationDetails();
      const serviceUrl = `wss://realtime.aiservice.${process.env.ORACLE_REGION}.oci.oraclecloud.com`;

      console.log("🌐 Service URL built:", serviceUrl);

      const listener = this.createListener();
      const params = this.createClientParams();

      console.log(
        "🔨 Creating RealtimeSpeechClient with correct constructor..."
      );
      console.log("- Listener:", typeof listener);
      console.log("- Provider:", typeof provider);
      console.log("- Region:", process.env.ORACLE_REGION);
      console.log("- CompartmentId:", process.env.ORACLE_COMPARTMENT_ID);
      console.log("- ServiceUrl:", serviceUrl);
      console.log("- Params:", JSON.stringify(params));

      // Usar el constructor correcto según el ejemplo de Oracle
      this.client = new SpeechClient.RealtimeSpeechClient(
        listener, // 1. listener
        provider, // 2. provider
        process.env.ORACLE_REGION, // 3. region
        process.env.ORACLE_COMPARTMENT_ID, // 4. compartmentId
        serviceUrl, // 5. serviceUrl
        params // 6. parameters
      );

      console.log("✅ Client created successfully with correct constructor");
      console.log(
        "🔍 Client methods:",
        Object.getOwnPropertyNames(this.client)
      );

      return {
        success: true,
        connectionId: "oracle-realtime-stt",
        streamUrl: serviceUrl,
      };
    } catch (error) {
      console.error("💥 Error in getConnectionDetails:", error);
      console.error("💥 Error stack:", error.stack);
      return {
        success: false,
        error: error.message || "Error creating streaming connection",
      };
    }
  },

  async startConnection() {
    console.log("🚀 === STARTING startConnection ===");

    if (!this.client) {
      console.error("❌ Client not initialized");
      return { success: false, error: "Client not initialized" };
    }

    console.log("🔍 Client available:", !!this.client);
    console.log("🔍 Client methods:", Object.getOwnPropertyNames(this.client));
    console.log("🔍 Client.connect exists:", typeof this.client.connect);

    try {
      console.log("🔌 Attempting to connect...");
      const result = await this.client.connect();
      console.log("✅ Connection successful:", result);
      return { success: true, message: "Connection started" };
    } catch (error) {
      console.error("💥 Error connecting:", error);
      console.error("💥 Error stack:", error.stack);
      return { success: false, error: error.message };
    }
  },

  sendAudio: async function (audioChunk) {
    console.log("🎵 === SENDING AUDIO ===");
    console.log("🎵 Audio chunk size:", audioChunk?.length || 0);

    if (!this.client) {
      console.error("❌ Client not initialized para sendAudio");
      return { success: false, error: "Client not initialized" };
    }

    try {
      console.log("🔄 Converting WebM to WAV...");

      // Convertir WebM a WAV PCM
      const wavBuffer = await new Promise((resolve, reject) => {
        const chunks = [];

        ffmpeg()
          .input("pipe:0")
          .inputFormat("webm")
          .audioCodec("pcm_s16le")
          .audioChannels(1)
          .audioFrequency(16000)
          .format("s16le")
          .pipe()
          .on("data", (chunk) => chunks.push(chunk))
          .on("end", () => resolve(Buffer.concat(chunks)))
          .on("error", reject)
          .end(audioChunk);
      });

      console.log("✅ Audio converted, sending to Oracle...");
      const result = await this.client.sendAudioData(wavBuffer);
      console.log("✅ Audio sent:", result);
      await this.client.requestFinalResult();

      return { success: true };
    } catch (error) {
      console.error("💥 Error processing audio:", error);
      return { success: false, error: error.message };
    }
  },

  async closeConnection() {
    console.log("🔌 === CLOSING CONNECTION ===");

    if (!this.client) {
      console.error("❌ Client not initialized para cerrar");
      return { success: false, error: "Client not initialized" };
    }

    console.log("🔍 Client.close exists:", typeof this.client.close);

    try {
      console.log("🔌 Disconnecting...");
      // Usar close en lugar de disconnect (según el ejemplo)
      const result = await this.client.close();
      console.log("✅ Disconnection successful:", result);
      this.client = null;
      this.listener = null;
      return { success: true, message: "Connection closed" };
    } catch (error) {
      console.error("💥 Error closing:", error);
      console.error("💥 Error stack:", error.stack);
      return { success: false, error: error.message };
    }
  },
};

module.exports = oracleRealtimeService;
