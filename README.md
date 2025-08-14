# Healthcare AI Assistant

A comprehensive healthcare platform with AI-powered chat, medical document processing, audio transcription, and meeting minutes generation.

## Features

- 🤖 AI Chat Assistant (general & medical)
- 📄 Medical Document Processing
- 🎤 Audio Transcription with Whisper
- 📝 Meeting Minutes Generator
- 🔧 Flask REST API with CORS support

## Installation

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure local AI server running on port 8553
3. Run: `python app.py`
4. Access: `http://localhost:5000`

## API Endpoints

- `POST /api/chat` - General chat
- `POST /api/medical-chat` - Medical chat
- `POST /api/transcribe-audio` - Audio transcription
- `POST /api/generate-meeting-minutes` - Meeting minutes
- `POST /api/upload-medical-record` - Document processing

## Usage

1. **Audio Recording**: Use Meeting Minutes page for recording and transcription
2. **Document Processing**: Upload PDFs for text extraction
3. **AI Chat**: General or medical-specific conversations
4. **Meeting Minutes**: Automatic generation from transcripts

## Requirements

- Python 3.8+
- Local AI server (port 8553)
- Modern browser with microphone support
- Use `localhost` for audio recording (secure context) 