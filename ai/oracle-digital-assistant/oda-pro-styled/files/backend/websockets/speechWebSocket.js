// websockets/speechWebSocket.js
const WebSocket = require("ws");
const { RealtimeSpeechClient } = require("@oracle/oci-ai-speech-realtime");
const oci = require("oci-sdk");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

class SpeechWebSocketHandler {
  constructor() {
    this.clients = new Map();
  }

  handleConnection(ws) {
    const clientId = Math.random().toString(36).slice(2, 10);
    console.log(`[Server] 🆕 Client connected: ${clientId}`);

    const client = { id: clientId, ws, oracleClient: null, ffmpeg: null };
    this.clients.set(clientId, client);

    this._startOracle(client)
      .then(() => this._startFfmpegPipeline(client))
      .catch((err) => {
        console.error(
          `[Server][${clientId}] Could not start Oracle:`,
          err
        );
        ws.send(JSON.stringify({ type: "error", message: err.message }));
        ws.close();
      });

    ws.on("message", (data) => {
      // Simplemente alimentamos FFmpeg
      if (client.ffmpeg && client.ffmpeg.stdin.writable) {
        client.ffmpeg.stdin.write(data);
      }
    });

    ws.on("close", async (code, reason) => {
      console.log(`[Server][${clientId}] 🔒 WS closed:`, code, reason);
      // Le decimos a Oracle que flushee lo que tiene pendiente
      try {
        if (client.oracleClient && client.oracleClient.requestFinalResult) {
          console.log(
            `[Server][${clientId}] → Request final result from Oracle`
          );
          await client.oracleClient.requestFinalResult();
        }
      } catch (err) {
        console.error(
          `[Server][${clientId}] Error in requestFinalResult:`,
          err
        );
      }
      // Cerramos la tubería de FFmpeg
      if (client.ffmpeg) {
        client.ffmpeg.stdin.end();
        client.ffmpeg.kill();
        console.log(`[Server][${clientId}] FFmpeg terminated`);
      }
      // Cerramos el cliente Oracle
      if (client.oracleClient) {
        try {
          await client.oracleClient.close();
          console.log(`[Server][${clientId}] OracleClient closed`);
        } catch (err) {
          console.error(
            `[Server][${clientId}] Error closing OracleClient:`,
            err
          );
        }
      }
      this.clients.delete(clientId);
    });

    ws.on("error", (err) => {
      console.error(`[Server][${clientId}] WS error:`, err);
    });
  }

  async _startOracle(client) {
    const privateKeyPath = path.resolve(
      __dirname,
      "..",
      process.env.ORACLE_PRIVATE_KEY
    );
    const privateKey = fs.readFileSync(privateKeyPath, "utf8");

    const provider = new oci.SimpleAuthenticationDetailsProvider(
      process.env.ORACLE_TENANCY_ID,
      process.env.ORACLE_USER_ID,
      process.env.ORACLE_FINGERPRINT,
      privateKey,
      null,
      process.env.ORACLE_REGION
    );

    const params = {
      encoding: "audio/raw;rate=16000",
      isAckEnabled: false,
      languageCode: "en-US",
      modelDomain: "GENERIC",
      partialSilenceThresholdInMs: 500,
      finalSilenceThresholdInMs: 1000,
    };
    const serviceUrl = `wss://realtime.aiservice.${process.env.ORACLE_REGION}.oci.oraclecloud.com`;

    const listener = {
      onConnect: () => console.log(`[Oracle][${client.id}] connected`),
      onConnectMessage: (msg) => {
        console.log(`[Oracle][${client.id}] ready message:`, msg);
        client.ws.send(JSON.stringify({ type: "ready" }));
      },
      onResult: (result) => {
        console.log(
          `[Oracle][${client.id}] Resultado:`,
          JSON.stringify(result)
        );
        if (result.transcriptions?.length) {
          const { transcription, isFinal } = result.transcriptions[0];
          client.ws.send(
            JSON.stringify({
              type: "transcription",
              text: transcription,
              isFinal,
            })
          );
        }
      },
      onError: (err) => console.error(`[Oracle][${client.id}] onError:`, err),
      onClose: () => console.log(`[Oracle][${client.id}] onClose`),
    };

    client.oracleClient = new RealtimeSpeechClient(
      listener,
      provider,
      process.env.ORACLE_REGION,
      process.env.ORACLE_COMPARTMENT_ID,
      serviceUrl,
      params
    );

    await client.oracleClient.connect();
    console.log(`[Server][${client.id}] Oracle connected successfully`);
  }

  _startFfmpegPipeline(client) {
    // Creamos un solo proceso FFmpeg por cliente
    const ffmpeg = spawn("ffmpeg", [
      "-f",
      "webm",
      "-i",
      "pipe:0",
      "-acodec",
      "pcm_s16le",
      "-ac",
      "1",
      "-ar",
      "16000",
      "-f",
      "s16le",
      "pipe:1",
    ]);

    ffmpeg.stderr.on("data", (msg) => {
      // Podemos ignorar o loguear si queremos debug
      // console.error(`[FFmpeg][${client.id}] `, msg.toString());
    });

    ffmpeg.stdout.on("data", async (pcm) => {
      try {
        await client.oracleClient.sendAudioData(pcm);
      } catch (err) {
        console.error(
          `[Server][${client.id}] Error sending PCM to Oracle:`,
          err
        );
      }
    });

    ffmpeg.on("exit", (code) => {
      console.log(`[FFmpeg][${client.id}] exited with code ${code}`);
    });

    client.ffmpeg = ffmpeg;
    console.log(`[Server][${client.id}] FFmpeg pipeline started`);
  }
}

module.exports = SpeechWebSocketHandler;
