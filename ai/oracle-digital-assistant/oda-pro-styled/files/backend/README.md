# ODA Pro Style - Backend API

WebSocket-based backend service that provides Oracle AI Speech Service integration for enhanced speech recognition capabilities.

## What's This All About?

This Node.js backend serves as a bridge between the ODA Pro Style frontend and Oracle's AI Speech Service. It provides real-time speech-to-text conversion with enterprise-grade accuracy, replacing basic browser speech recognition with Oracle's powerful AI models.

Perfect for production environments where speech recognition accuracy and reliability are critical.

## Key Features

**🎤 Oracle AI Speech Integration**

- Real-time speech-to-text using Oracle Cloud Infrastructure AI Speech Service
- WebSocket-based streaming for low-latency audio processing
- Automatic audio format conversion (WebM to PCM 16kHz)
- Multilingual support: Broaden your audience reach with Whisper's multilingual support voice-to-text transcription for over 50 languages, including Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Māori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh

**🔧 Enterprise-Ready Architecture**

- Built with Express.js for robust API handling
- FFmpeg integration for seamless audio processing
- Secure Oracle Cloud authentication with API keys
- Health check endpoints for monitoring

**⚡ Performance Optimized**

- Streaming audio processing with minimal latency
- Efficient memory usage with chunked audio handling
- Automatic connection management and cleanup

## Technology Stack

- **Node.js** with Express.js framework
- **WebSocket (ws)** for real-time communication
- **Oracle AI Speech Realtime SDK v2.1.0** for speech recognition
- **Oracle Cloud Infrastructure SDK** for authentication
- **FFmpeg** for audio format conversion
- **Helmet & CORS** for security

## Prerequisites

- Node.js 16+ and npm
- FFmpeg installed on your system
- Oracle Cloud Infrastructure account
- Oracle AI Speech Service enabled in your tenancy

## Installation

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your Oracle Cloud credentials:

   ```bash
   PORT=3001
   ORACLE_TENANCY_ID=ocid1.tenancy.oc1..your_tenancy_id_here
   ORACLE_USER_ID=ocid1.user.oc1..your_user_id_here
   ORACLE_FINGERPRINT=your_fingerprint_here
   ORACLE_PRIVATE_KEY=.secrets/your-private-key.pem
   ORACLE_REGION=your_region_here
   ORACLE_COMPARTMENT_ID=ocid1.compartment.oc1..your_compartment_id_here
   ```

4. Add your Oracle Cloud private key:

   ```bash
   mkdir .secrets
   # Copy your Oracle Cloud private key file to .secrets/
   ```

5. Start the server:
   ```bash
   npm run dev    # Development with nodemon
   npm start      # Production
   ```

## Project Structure

```
├── app.js                      # Main Express application
├── routes/
│   └── index.js               # Basic API routes
├── services/
│   └── oracleRealtimeService.js # Oracle AI Speech service wrapper
├── websockets/
│   └── speechWebSocket.js     # WebSocket handler for speech processing
└── .secrets/                  # Oracle Cloud private keys (not in repo)
```

## API Endpoints

### Health Check

```
GET /api/health
```

Returns API status for monitoring and load balancing.

### WebSocket Speech Service

```
WebSocket: ws://localhost:3001/ws/speech
```

Real-time speech-to-text conversion endpoint.

**Connection Flow:**

1. Client connects to WebSocket
2. Server automatically establishes Oracle AI Speech connection
3. Client sends audio chunks (WebM format)
4. Server converts to PCM and forwards to Oracle
5. Oracle returns transcription results in real-time

## Oracle Cloud Setup

You'll need an Oracle Cloud Infrastructure account with AI Speech Service enabled and proper API credentials configured in your `.env` file. Refer to Oracle Cloud documentation for detailed setup instructions.

## Audio Processing Pipeline

1. **Client Audio**: Browser captures audio in WebM format
2. **WebSocket Transport**: Audio chunks sent via WebSocket
3. **FFmpeg Conversion**: WebM converted to PCM 16kHz mono
4. **Oracle Processing**: PCM audio sent to Oracle AI Speech Service
5. **Real-time Results**: Transcription results streamed back to client

## Security Features

- **Helmet.js**: Security headers and protection
- **CORS**: Configurable cross-origin resource sharing
- **Private Key Management**: Secure Oracle Cloud authentication
- **Connection Isolation**: Each client gets isolated processing pipeline

## Available Scripts

```bash
npm start      # Start production server
npm run dev    # Start development server with auto-reload
```

## Integration with Frontend

The frontend automatically detects this backend service and enables Oracle AI Speech features when available. No additional configuration needed on the frontend side.

**Frontend Detection:**

```javascript
// Frontend automatically uses Oracle AI Speech when backend is running
NEXT_PUBLIC_SPEECH_SERVICE_URL=ws://localhost:3001/ws/speech
```

## Monitoring and Debugging

### Health Check

```bash
curl http://localhost:3001/api/health
```

The service includes comprehensive logging for debugging connection status, audio processing pipeline, and WebSocket lifecycle.

## Performance Considerations

- **Memory Usage**: Streaming audio processing keeps memory usage low
- **Latency**: Direct Oracle integration minimizes processing delays
- **Concurrency**: Each client gets isolated processing pipeline
- **Cleanup**: Automatic resource cleanup on client disconnect

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License v1.0.
