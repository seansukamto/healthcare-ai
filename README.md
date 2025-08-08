# Healthcare AI Platform

A comprehensive healthcare platform with AI-powered features including medical consultations, document analysis, meeting minutes generation, and more.

## Features

### 🏥 Dashboard
- Professional healthcare dashboard with key metrics
- Quick access to all platform features
- Real-time activity tracking

### 💬 AI Chat Assistant
- **General Health Chat**: Get instant medical advice and health consultations
- **Medical Records Analysis**: Upload PDF medical documents and get AI-powered insights
- Side menu with quick action buttons for common health queries

### 🎤 Meeting Minutes Generator
- Record meetings with browser-based audio recording
- Automatic speech-to-text transcription
- AI-generated meeting minutes with structured summaries
- Download and copy functionality

### 🌐 Translation Service
- Medical document translation (Coming Soon)
- Multi-language support for healthcare communications

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python Flask
- **AI**: OpenAI GPT-4
- **Audio Processing**: SpeechRecognition, PyAudio
- **Document Processing**: PyPDF2
- **Styling**: Custom CSS with professional healthcare theme

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd healthcare-platform
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Audio Recording Setup
The audio recording feature works with HTTP on localhost (which is considered a secure context). This is the recommended approach for development with confidential data.

```bash
python app.py
```
Then access your application at `http://localhost:5000`

**Why localhost HTTP is secure:**
- localhost is considered a secure context by browsers
- No data leaves your local machine
- Perfect for confidential healthcare data
- No certificate setup required

### 5. Run the Application
```bash
python app.py
```

The application will be available at:
- **HTTP**: `http://localhost:5000` - Full functionality, secure for localhost

## Troubleshooting

### Audio Recording Issues

If you encounter `getUserMedia` errors:

1. **Use localhost**: Access via `http://localhost:5000` (not IP address)
2. **Check Browser Support**: Use Chrome, Firefox, Safari, or Edge (latest versions)
3. **Grant Permissions**: Allow microphone access when prompted
4. **Check Microphone**: Ensure your microphone is connected and working

### Common Error Messages

- **"Cannot read properties of undefined (reading 'getUserMedia')"**: Browser doesn't support the API or not using localhost
- **"NotAllowedError"**: Microphone permission denied
- **"NotFoundError"**: No microphone detected
- **"NotSupportedError"**: Audio recording is not supported in your browser
- **"SecurityError"**: Not using localhost or HTTPS

## Usage Guide

### Dashboard
- View key healthcare metrics and statistics
- Access quick actions for common tasks
- Monitor recent activity and system status

### AI Chat
1. **General Health Chat**:
   - Click on the "Chat" tab in the sidebar
   - Type your health questions or use quick action buttons
   - Get instant AI-powered medical advice

2. **Medical Records Analysis**:
   - Click on the "Medical Records" tab in the sidebar
   - Upload PDF medical documents
   - Ask questions about the uploaded documents
   - Receive AI analysis and insights

### Meeting Minutes
1. Click the red microphone button to start recording
2. Speak clearly during your meeting
3. Click the green stop button when finished
4. Wait for automatic transcription
5. Click "Generate Meeting Minutes" for AI-powered summaries
6. Download or copy the generated minutes

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - General health chat
- `POST /api/medical-chat` - Medical records chat
- `POST /api/upload-medical-record` - Upload medical documents

### Meeting Minutes Endpoints
- `POST /api/transcribe-audio` - Transcribe audio recordings
- `POST /api/generate-meeting-minutes` - Generate meeting minutes

## File Structure

```
healthcare-platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Landing page
│   ├── dashboard.html    # Dashboard page
│   ├── chat.html         # Chat interface
│   ├── meeting_minutes.html # Meeting minutes page
│   └── translate.html    # Translation page (placeholder)
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # Main JavaScript file
├── uploads/              # File upload directory
├── chat.py              # Chat functionality
├── medical_docs.py      # Medical document processing
├── meeting_minutes.py   # Meeting minutes generation
├── generate.py          # AI response generation
├── pdf.py               # PDF processing utilities
└── audio.py             # Audio processing utilities
```

## Security & Privacy

- All medical data is processed securely
- No data is stored permanently on the server
- Audio recordings are processed and deleted immediately
- Localhost HTTP provides secure context for development

## Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure your browser has permission to access the microphone
   - Check browser settings for microphone permissions

2. **OpenAI API Errors**
   - Verify your API key is correct and has sufficient credits
   - Check your internet connection

3. **File Upload Issues**
   - Ensure files are in supported formats (PDF, TXT, DOC, DOCX)
   - Check file size limits

4. **Audio Recording Problems**
   - Use a modern browser with WebRTC support
   - Ensure microphone is properly connected and working

### Error Logs
Check the console for detailed error messages and logs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Note**: This platform is designed for educational and demonstration purposes. For actual medical use, ensure compliance with healthcare regulations and obtain necessary certifications. 