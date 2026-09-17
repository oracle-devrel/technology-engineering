# AIQ RAG Document Analyzer - Frontend

A modern React application for AI-powered parameter extraction from PDF documents. This application features a split-screen interface with a PDF viewer on the left and extracted parameters displayed on the right.

## EnterpriseAI backend

This project is configured to use the deployed OCI EnterpriseAI service for
documents, chat, research, and other `/api/*` capabilities. In development,
Vite proxies those calls to the service set by `ENTERPRISE_AI_API_URL` (see
`.env.example`). Production NGINX provides the equivalent same-origin proxy.

`/api/auth/*` remains on this application's FastAPI backend, so the browser
never receives a service password. Set the local backend's `ADMIN_USERNAME`
and `ADMIN_PASSWORD` through its local environment or deployment secret.

## Features

- **Split-Screen Layout**: View PDF documents alongside extracted parameters
- **Real-time Processing**: Live status updates during document upload and extraction
- **Modern UI**: Clean, professional design built with Tailwind CSS
- **PDF Viewing**: Full-featured PDF viewer with zoom, scroll, and navigation
- **Confidence Scores**: Visual indicators for parameter extraction confidence
- **Responsive Design**: Optimized for desktop and tablet devices
- **TypeScript**: Full type safety throughout the application

## Tech Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **@react-pdf-viewer/core** - PDF viewing functionality
- **Axios** - HTTP client for API communication
- **Create React App** - Build tooling and development server

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (or configure different URL)

## Installation

1. Navigate to the frontend directory:
```bash
cd /Users/slv/Projects/ai-coe/AIQ/aiq-rag/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment configuration (optional):
```bash
cp .env.example .env
```

Edit `.env` to configure your API URL if different from default:
```
REACT_APP_API_URL=http://localhost:8000
```

## Development

Start the development server:
```bash
npm start
```

The application will open automatically at [http://localhost:3000](http://localhost:3000).

The page will reload automatically when you make changes. Lint errors will appear in the console.

## Building for Production

Create an optimized production build:
```bash
npm run build
```

This creates a `build/` directory with optimized production files ready for deployment.

## Project Structure

```
frontend/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/
│   │   ├── Header/
│   │   │   └── Header.tsx      # App header with title and controls
│   │   ├── PdfViewer/
│   │   │   └── PdfViewer.tsx   # PDF document viewer
│   │   ├── ExtractionPanel/
│   │   │   └── ExtractionPanel.tsx  # Extracted parameters display
│   │   ├── UploadButton/
│   │   │   └── UploadButton.tsx     # File upload button
│   │   └── StatusIndicator/
│   │       └── StatusIndicator.tsx  # Processing status indicator
│   ├── services/
│   │   └── api.ts              # API client and HTTP calls
│   ├── types/
│   │   └── index.ts            # TypeScript type definitions
│   ├── styles/
│   │   └── globals.css         # Global styles and Tailwind imports
│   ├── App.tsx                 # Main application component
│   └── index.tsx               # Application entry point
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── README.md
```

## API Integration

The frontend expects the following backend API endpoints:

### Upload Document
```
POST /api/upload
Content-Type: multipart/form-data
Body: { file: <PDF file> }
Response: { document_id: string, filename: string, message: string }
```

### Extract Parameters
```
POST /api/extract/{document_id}
Response: { document_id: string, status: string, parameters: Array }
```

### Get Document Status
```
GET /api/document/{document_id}
Response: {
  document_id: string,
  filename: string,
  status: string,
  extracted_parameters?: Array,
  error?: string
}
```

### Get PDF File
```
GET /api/document/{document_id}/pdf
Response: PDF file binary
```

## User Flow

1. **Upload**: Click "Upload PDF" button and select a PDF file
2. **View**: PDF displays in the left panel
3. **Process**: Extraction automatically starts with live status updates
4. **Review**: Extracted parameters appear in the right panel with confidence scores
5. **Analyze**: Scroll through PDF while viewing categorized parameters

## Component Details

### Header
- Application branding and title
- Upload button
- Processing status indicator

### PdfViewer
- Full-featured PDF viewer
- Zoom controls
- Page navigation
- Error handling for invalid PDFs

### ExtractionPanel
- Categorized parameter display
- Confidence score visualization
- Color-coded confidence levels (High/Medium/Low)
- Progress bars for each parameter
- Loading skeletons during processing

### UploadButton
- File selection dialog
- PDF validation
- Disabled state during processing

### StatusIndicator
- Real-time status updates
- Visual indicators (idle, uploading, processing, completed, error)
- Current filename display
- Animated loading states

## Styling

The application uses Tailwind CSS for styling with a custom color scheme:

- **Primary Color**: Blue (sky-500 to sky-700)
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red
- **Neutral**: Gray scale

Custom scrollbar styling and smooth transitions are included for a polished user experience.

## Environment Variables

- `REACT_APP_API_URL`: Backend API base URL (default: `http://localhost:8000`)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### PDF not loading
- Ensure the backend API is running
- Check browser console for CORS errors
- Verify the document ID is valid

### API connection errors
- Confirm backend is running on the configured port
- Check `REACT_APP_API_URL` in `.env` file
- Verify network connectivity

### Build errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear build cache: `rm -rf build`
- Check Node.js version (18+ required)

## Development Tips

1. **Hot Reload**: Changes to source files trigger automatic reloads
2. **Type Checking**: Run `npx tsc --noEmit` to check types without building
3. **Linting**: Use ESLint configuration from Create React App
4. **Console Logs**: Check browser console for detailed API responses and errors

## Future Enhancements

- Multi-document comparison
- Export extracted parameters (JSON, CSV)
- Search within PDF
- Parameter editing and validation
- Document history and management
- Dark mode support
- Mobile responsive layout

## License

Proprietary - AIQ Project

## Support

For issues or questions, contact the AIQ development team.
