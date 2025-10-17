# ODA Pro Styled

Review date: 17-10-2025

Author: Ras Alungei

🎥 **[View Demo Video](files/oda-pro-styled-demo.mp4)**

A complete solution for creating professional, customizable chat interfaces for Oracle Digital Assistant with enterprise-grade speech recognition capabilities.

## Overview

ODA Pro Styled provides everything you need to deploy branded chat experiences that integrate seamlessly with Oracle Digital Assistant. Perfect for solution architects, sales teams, and developers who need to quickly showcase Oracle Digital Assistant across multiple client scenarios.

**What's Included:**

- **Frontend**: Modern React chat interface with multi-project theming
- **Backend**: Oracle AI Speech Service integration for enhanced speech recognition

## Key Features

**🎨 Professional Showcase Capabilities**

- Multi-project management (up to 8 branded configurations)
- Instant theme switching for client demonstrations
- Custom branding with logos, colors, and backgrounds
- Lightning-fast project setup (under 30 seconds)

**🎤 Enterprise Speech Integration**

- Dual speech options: Browser native or Oracle AI Speech Service
- **Multilingual Support**: 50+ languages including Spanish, French, German, Chinese, Japanese, Arabic, and more
- Real-time speech-to-text with enterprise-grade accuracy
- Automatic text-to-speech using Oracle Digital Assistant's TTS
- Seamless voice conversation flow

**💬 Rich Chat Experience**

- Full markdown support for formatted responses
- File attachment support (images and PDFs)
- Real-time WebSocket communication
- Responsive design across all devices

**🔒 Privacy & Security**

- Client data stored locally (localStorage)
- No server dependencies for configuration data
- Secure Oracle Cloud authentication
- Complete client data isolation

## Architecture

The solution consists of two complementary components:

### Frontend (React/Next.js)

- Multi-tenant chat interface
- Dynamic theming system
- Oracle Digital Assistant WebSDK integration
- Speech recognition interface

### Backend (Node.js/Express)

- Oracle AI Speech Service WebSocket proxy
- **Multilingual speech recognition** (50+ languages via Whisper technology)
- Real-time audio processing pipeline
- FFmpeg audio format conversion
- Secure Oracle Cloud authentication

## Quick Start

### Option 1: Frontend Only

Basic setup with browser speech recognition:

```bash
cd files/frontend/
npm install
cp .env.example .env.local
# Configure your Oracle Digital Assistant credentials
npm run dev
```

### Option 2: Full Stack (Recommended)

Complete setup with Oracle AI Speech Service:

```bash
# Start backend
cd files/backend/
npm install
cp .env.example .env
# Configure Oracle Cloud credentials
npm start

# Start frontend (in new terminal)
cd files/frontend/
npm install
cp .env.example .env.local
# Configure Oracle Digital Assistant + Speech Service URL
npm run dev
```

## Configuration

### Oracle Digital Assistant Setup

1. Create a Web channel in your Oracle Digital Assistant
2. Note the Channel ID and URI
3. Configure in frontend `.env.local`

### Oracle AI Speech Service Setup (Optional)

1. Enable AI Speech Service in Oracle Cloud Infrastructure
2. Generate API credentials
3. Configure in backend `.env`

Detailed setup instructions are available in each component's README.

## Use Cases

**Sales Demonstrations**

- Quickly switch between different client brand themes
- Showcase Oracle Digital Assistant capabilities
- Professional presentation-ready interface

**Development & Testing**

- Rapid prototyping with multiple configurations
- A/B testing different chat experiences
- Integration testing with Oracle services

**Production Deployments**

- Enterprise-ready speech recognition
- Scalable WebSocket architecture
- Secure credential management

## Components

- **Frontend**: [`files/frontend/`](files/frontend/) - Complete React chat interface
- **Backend**: [`files/backend/`](files/backend/) - Oracle AI Speech Service integration

## Technology Stack

**Frontend**: Next.js 15, React 19, Material-UI, Framer Motion, Oracle WebSDK  
**Backend**: Node.js, Express, WebSocket, Oracle AI Speech SDK, FFmpeg

## Browser Requirements

- Modern browser with WebSocket support
- Web Speech API (for browser speech mode)
- LocalStorage for project persistence

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License v1.0.
