from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import base64
from werkzeug.utils import secure_filename
import PyPDF2
import io
import logging
from datetime import datetime
import ssl
import ipaddress
import markdown

# Import existing modules
from chat import chat
from medical_docs import medical_docs
from meeting_minutes import meeting_minutes
from generate import generate_response

app = Flask(__name__)

# Fix for Werkzeug connection reset issue with file uploads
# Based on: https://www.cocept.io/blog/development/flask-file-upload-connection-reset/
try:
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
except ImportError:
    pass  # Ignore if not available

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "http://192.168.10.119:5000", 
                   "https://localhost:5000", "https://127.0.0.1:5000", "https://192.168.10.119:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SSL Context for HTTPS
def create_ssl_context():
    """Create SSL context for HTTPS support"""
    try:
        # Create self-signed certificate for development
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Healthcare Platform"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate and key
        cert_path = "cert.pem"
        key_path = "key.pem"
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return cert_path, key_path
        
    except ImportError:
        logger.warning("cryptography not available. Using HTTP only.")
        return None, None
    except Exception as e:
        logger.error(f"Error creating SSL context: {e}")
        return None, None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        return f"Error extracting text: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/meeting-minutes')
def meeting_minutes_page():
    return render_template('meeting_minutes.html')

@app.route('/translate')
def translate_page():
    return render_template('translate.html')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'server': 'Flask Healthcare Platform',
        'protocol': request.scheme
    })

# API Endpoints
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def api_chat():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        logger.info(f"Chat API called at {datetime.now()}")
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        logger.info(f"Processing chat message: {user_message[:50]}...")
        
        response_data = chat(user_message)
        response_markdown = response_data['content']
        token_usage = response_data['token_usage']
        
        # Convert markdown to HTML with table support
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
        response_html = md.convert(response_markdown)
        
        logger.info("Chat response generated successfully")
        return jsonify({
            'response': response_markdown,  # Raw markdown for copying
            'response_html': response_html,  # HTML for display
            'token_usage': token_usage  # Token usage information
        })
    
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/medical-chat', methods=['POST', 'OPTIONS'])
def api_medical_chat():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        logger.info(f"Medical chat API called at {datetime.now()}")
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_message = data.get('message', '')
        medical_history = data.get('medical_history', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        logger.info(f"Processing medical chat message: {user_message[:50]}...")
        
        response_data = medical_docs(user_message, medical_history)
        response_markdown = response_data['content']
        token_usage = response_data['token_usage']
        
        # Convert markdown to HTML with table support
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
        response_html = md.convert(response_markdown)
        
        logger.info("Medical chat response generated successfully")
        return jsonify({
            'response': response_markdown,  # Raw markdown for copying
            'response_html': response_html,  # HTML for display
            'token_usage': token_usage  # Token usage information
        })
    
    except Exception as e:
        logger.error(f"Error in medical chat API: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/upload-medical-record', methods=['POST', 'OPTIONS'])
def upload_medical_record():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        logger.info(f"Medical record upload API called at {datetime.now()}")
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            logger.info(f"File saved: {file_path}")
            
            # Extract text from PDF
            with open(file_path, 'rb') as pdf_file:
                extracted_text = extract_text_from_pdf(pdf_file)
            
            logger.info("Medical record processed successfully")
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'extracted_text': extracted_text
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        logger.error(f"Error in medical record upload: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/generate-meeting-minutes', methods=['POST', 'OPTIONS'])
def api_generate_meeting_minutes():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        logger.info(f"Meeting minutes API called at {datetime.now()}")
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        transcript = data.get('transcript', '')
        
        if not transcript:
            return jsonify({'error': 'No transcript provided'}), 400
        
        logger.info(f"Processing meeting minutes for transcript: {len(transcript)} characters")
        
        response_data = meeting_minutes(transcript)
        minutes_markdown = response_data['content']
        token_usage = response_data['token_usage']
        
        # Convert markdown to HTML with table support
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br'])
        minutes_html = md.convert(minutes_markdown)
        
        logger.info("Meeting minutes generated successfully")
        return jsonify({
            'minutes': minutes_markdown,  # Raw markdown for copying/downloading
            'minutes_html': minutes_html,  # HTML for display
            'token_usage': token_usage  # Token usage information
        })
    
    except Exception as e:
        logger.error(f"Error in meeting minutes API: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/transcribe-audio', methods=['POST', 'OPTIONS'])
def transcribe_audio():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        logger.info(f"Audio transcription API called at {datetime.now()}")
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save audio file temporarily with a safe name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        audio_file.save(file_path)
        logger.info(f"Audio file saved: {file_path}")
        
        # Initialize OpenAI client for Whisper API
        from openai import OpenAI 
        client = OpenAI(api_key="dpais", base_url="http://localhost:8553/v1/openai")

        try:
            # Speech recognition by Whisper
            with open(file_path, "rb") as audio_file_handle:
                transcript = client.audio.transcriptions.create(
                    model="whisper",
                    file=audio_file_handle
                )
            logger.info("Transcription successful with Whisper API")
        except Exception as transcription_error:
            logger.error(f"Transcription failed: {transcription_error}")
            raise Exception(f"Speech recognition failed: {str(transcription_error)}")
        
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
        
        if hasattr(transcript, 'text'):
            transcript_text = transcript.text
        else:
            transcript_text = str(transcript)
            
        if transcript_text:
            logger.info("Audio transcription completed successfully")
            return jsonify({'transcript': transcript_text})
        else:
            raise Exception("Failed to transcribe audio - no transcript generated")
    
    except Exception as e:
        logger.error(f"Error in audio transcription: {str(e)}")
        # Clean up any remaining files
        try:
            import glob
            for file in glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], 'recording_*.wav')):
                os.remove(file)
        except:
            pass
        return jsonify({'error': f'Audio transcription failed: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    logger.info("Starting Flask Healthcare Platform server...")
    logger.info("Access your application at: http://localhost:5000")
    logger.info("For audio recording: Use localhost (HTTP) - it's considered a secure context")
    
    # Run with HTTP by default (localhost is secure for media access)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True) 