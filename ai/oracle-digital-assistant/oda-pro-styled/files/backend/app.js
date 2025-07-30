var express = require("express");
var path = require("path");
var cookieParser = require("cookie-parser");
var logger = require("morgan");
var cors = require("cors");
var helmet = require("helmet");
var http = require("http");
var WebSocket = require("ws");
require("dotenv").config();

var indexRouter = require("./routes/index");
var SpeechWebSocketHandler = require("./websockets/speechWebSocket");

var app = express();
var server = http.createServer(app);

app.use(helmet());
app.use(cors());
app.use(logger("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, "public")));

app.use("/", indexRouter);

app.get("/api/health", (req, res) => {
  res.status(200).json({
    status: "ok",
    message: "API for ai-speech-backend working correctly",
  });
});

app.use((req, res, next) => {
  res.status(404).json({
    status: "error",
    message: "Route not found",
  });
});

app.use((err, req, res, next) => {
  const statusCode = res.statusCode === 200 ? 500 : res.statusCode;
  res.status(statusCode).json({
    status: "error",
    message: err.message,
    stack: process.env.NODE_ENV === "production" ? null : err.stack,
  });
});

const wss = new WebSocket.Server({
  server,
  path: "/ws/speech",
});

const speechHandler = new SpeechWebSocketHandler();

wss.on("connection", (ws, req) => {
  speechHandler.handleConnection(ws, req);
});

module.exports = { app, server };
