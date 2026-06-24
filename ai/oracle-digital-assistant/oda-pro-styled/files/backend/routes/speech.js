// websockets/speechWebSocket.js
const WebSocket = require("ws");
const { RealtimeSpeechClient } = require("@oracle/oci-ai-speech-realtime");
const oci = require("oci-sdk");
const path = require("path");
const fs = require("fs");
const ffmpeg = require("fluent-ffmpeg");

class SpeechWebSocketHandler {
  constructor() {
    this.clients = new Map();
  }

  handleConnection(ws) {
    const clientId = Math.random().toString(36).slice(2, 10);
    console.log(`Client connected: ${clientId}`);

    const client = {
      id: clientId,
      ws: ws,
      oracleClient: null,
    };

    this.clients.set(clientId, client);

    // Iniciar Oracle automáticamente al conectar
    this._startOracle(client);

    ws.on("message", async (data) => {
      // Si es audio, procesarlo
      if (data.length > 100) {
        // Los mensajes JSON son pequeños, el audio es grande
        try {
          const pcm = await this._convertToPCM(data);
          if (client.oracleClient) {
            await client.oracleClient.sendAudioData(pcm);
          }
        } catch (error) {
          console.error("Error procesando audio:", error);
        }
      }
    });

    ws.on("close", () => {
      console.log(`Client disconnected: ${clientId}`);
      if (client.oracleClient) {
        client.oracleClient.close().catch(() => {});
      }
      this.clients.delete(clientId);
    });

    ws.on("error", (error) => {
      console.error(`Error en cliente ${clientId}:`, error);
    });
  }

  async _startOracle(client) {
    try {
      // Leer clave privada
      const privateKeyPath = path.resolve(
        __dirname,
        "..",
        process.env.ORACLE_PRIVATE_KEY
      );
      const privateKey = fs.readFileSync(privateKeyPath, "utf8");

      // Crear proveedor de autenticación
      const provider = new oci.SimpleAuthenticationDetailsProvider(
        process.env.ORACLE_TENANCY_ID,
        process.env.ORACLE_USER_ID,
        process.env.ORACLE_FINGERPRINT,
        privateKey,
        null,
        process.env.ORACLE_REGION
      );

      // Parámetros de Oracle
      const params = {
        encoding: "audio/raw;rate=16000",
        isAckEnabled: false,
        languageCode: "en-US",
        modelDomain: "GENERIC",
        partialSilenceThresholdInMs: 0,
        finalSilenceThresholdInMs: 2000,
      };

      // Crear listener
      const listener = {
        onConnect: () => console.log("Oracle connected"),
        onConnectMessage: (msg) => {
          console.log("Oracle ready");
          client.ws.send(JSON.stringify({ type: "ready" }));
        },
        onResult: (result) => {
          if (result.transcriptions && result.transcriptions[0]) {
            const transcription = result.transcriptions[0];
            client.ws.send(
              JSON.stringify({
                type: "transcription",
                text: transcription.transcription,
                isFinal: transcription.isFinal,
              })
            );
          }
        },
        onError: (error) => console.error("Error Oracle:", error),
        onClose: () => console.log("Oracle closed"),
      };

      // URL del servicio
      const serviceUrl = `wss://realtime.aiservice.${process.env.ORACLE_REGION}.oci.oraclecloud.com`;

      // Crear cliente Oracle
      client.oracleClient = new RealtimeSpeechClient(
        listener,
        provider,
        process.env.ORACLE_REGION,
        process.env.ORACLE_COMPARTMENT_ID,
        serviceUrl,
        params
      );

      // Conectar
      await client.oracleClient.connect();
      console.log("Oracle connected successfully");
    } catch (error) {
      console.error("Error conectando Oracle:", error);
      client.ws.send(JSON.stringify({ type: "error", message: error.message }));
    }
  }

  async _convertToPCM(webmBuffer) {
    return new Promise((resolve, reject) => {
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
        .end(webmBuffer);
    });
  }
}

module.exports = SpeechWebSocketHandler;
