# 🤖 Assaf Azran - Personal AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> An AI agent that serves as Assaf Azran's personal representative - a close friend who knows Assaf extremely well and can answer questions about him naturally and warmly to others.

## 🎯 Purpose

This agent is designed to be **Assaf Azran's personal ambassador** that other people can interact with to learn about Assaf. The agent speaks like a close friend would - naturally, warmly, and with genuine knowledge of who Assaf is.

## ✨ Features

- **🧠 Personal Knowledge Base**: Learns deeply about Assaf through uploaded files
- **💬 Natural Conversation**: Speaks like a real friend, not an AI assistant
- **🌐 Multilingual Support**: Converses in both Hebrew and English (English UI)
- **🎯 Context-Aware Responses**: Uses personal knowledge to provide authentic answers
- **🤝 Friend-like Persona**: Warm, genuine, and proud representation of Assaf
- **📁 Multi-format File Upload**: PDF, TXT, DOCX, images (OCR), audio transcription
- **🔍 Knowledge Extraction**: Automatically understands Assaf's personality, skills, and experiences
- **🎨 Modern UI**: Beautiful React frontend with animations and responsive design

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **OpenAI GPT-4** - Chat, knowledge extraction, and understanding Assaf
- **Qdrant** - Vector database for semantic search about Assaf
- **Python** - Core language with extensive AI/ML libraries

### Frontend
- **Next.js 16** - React framework with server-side rendering
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Beautiful animations
- **Lucide React** - Modern icon library

### Infrastructure
- **Docker** - Containerized deployment
- **Docker Compose** - Multi-container orchestration

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/AssafsAgent.git
   cd AssafsAgent
   ```

2. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Start with Docker**
   ```bash
   # On Windows
   start-docker.bat
   
   # On Linux/Mac
   chmod +x start-docker.sh
   ./start-docker.sh
   ```

4. **Access Applications**
   - 🌐 Frontend: http://localhost:3000
   - 🔧 Backend API: http://localhost:8000
   - 📚 API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

1. **Install Backend Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Start Qdrant**
   ```bash
   docker run -p 6334:6334 qdrant/qdrant
   ```

5. **Run Backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Run Frontend** (in another terminal)
   ```bash
   cd frontend
   npm run dev
   ```

## 📡 API Endpoints

### Chat with Assaf's Agent
- `POST /api/chat/` - Ask questions about Assaf
- `GET /api/chat/sessions` - List conversation sessions
- `POST /api/chat/sessions/{session_id}/reset` - Reset conversation

### Upload Information About Assaf
- `POST /api/upload/` - Upload files about Assaf
- `GET /api/upload/status/{upload_id}` - Check processing status
- `GET /api/upload/uploads` - List all uploads
- `DELETE /api/upload/{upload_id}` - Delete uploaded file

### Knowledge Management
- `GET /api/knowledge/` - List all knowledge about Assaf
- `GET /api/knowledge/search` - Search through information about Assaf
- `GET /api/knowledge/profile` - Get agent's understanding of Assaf
- `DELETE /api/knowledge/{document_id}` - Remove document
- `POST /api/knowledge/retrain` - Re-process all files
- `GET /api/knowledge/stats` - Get knowledge base statistics

## 💡 Usage Examples

### Upload Information About Assaf
```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@assaf_resume.pdf"
```

### Ask About Assaf
```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are Assaf''s main skills?",
    "language": "en"
  }'
```

### Search Information About Assaf
```bash
curl -X GET "http://localhost:8000/api/knowledge/search?query=projects&limit=3"
```

## 🧠 What the Agent Knows About Assaf

The agent learns and understands:

- **🏠 Personal Background**: Where Assaf is from, heritage, cultural context
- **💼 Skills & Expertise**: Technical abilities, professional capabilities
- **🎭 Personality Traits**: How Assaf thinks, behaves, his character
- **📅 Life Experiences**: Important events, achievements, challenges
- **👥 Relationships**: Key people in Assaf's life
- **❤️ Passions & Interests**: What Assaf loves doing
- **🎯 Goals & Dreams**: What Assaf is working toward
- **🗣️ Communication Style**: How Assaf expresses himself
- **⚖️ Values & Beliefs**: What's important to Assaf

## 🗣️ Conversation Style

The agent speaks as Assaf's close friend would:

- **🤗 Warm and Natural**: Like a real friend talking about someone they care about
- **✅ Authentic**: Based on real knowledge from Assaf's files
- **🏆 Proud but Humble**: Represents Assaf genuinely
- **🎭 Context-Aware**: Adapts tone based on who's asking
- **🌐 Bilingual**: Fluent in Hebrew and English
- **📖 Personal**: Shares insights and stories naturally

## 🏛️ Architecture

### Core Components
- **FastAPI**: Web framework and API server
- **OpenAI GPT-4**: Chat, knowledge extraction, understanding Assaf
- **Qdrant**: Vector database for semantic search about Assaf
- **File Processor**: Multi-format text extraction and OCR
- **Personal Agent**: Friend-like conversation about Assaf

### Knowledge Pipeline
1. **📁 File Upload**: Documents about Assaf (PDF, TXT, DOCX, images, audio)
2. **📄 Text Extraction**: OCR, transcription, document parsing
3. **🧠 Knowledge Extraction**: AI analyzes and structures information about Assaf
4. **🔢 Embedding Generation**: Semantic embeddings for search
5. **💾 Vector Storage**: Information stored with metadata
6. **👤 Profile Building**: Dynamic understanding of who Assaf is

## ⚙️ Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
QDRANT_HOST=localhost
QDRANT_PORT=6334
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=pdf,txt,docx,jpg,jpeg,png,wav,mp3,m4a
```

## 🛠️ Development

### Adding Information About Assaf
Upload any of these file types:
- **📄 Documents**: PDF, TXT, DOCX (resumes, stories, descriptions)
- **🖼️ Images**: JPG, JPEG, PNG (photos with OCR)
- **🎵 Audio**: WAV, MP3, M4A (interviews, conversations)

The agent will extract and understand:
- Professional skills and experience
- Personality traits and characteristics
- Life events and achievements
- Relationships and connections
- Goals and aspirations

### Project Structure
```
AssafsAgent/
├── app/                    # Backend FastAPI application
│   ├── core/              # Core agent logic
│   ├── services/          # Business services
│   ├── api/               # API endpoints
│   └── models/            # Data models
├── frontend/              # Next.js React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── types/         # TypeScript types
├── assaf_files/           # Personal files about Assaf
├── uploads/               # Uploaded files
└── docker-compose.yml     # Docker configuration
```

## 🔒 Privacy and Security

- 🔐 All personal data about Assaf is stored locally
- 🛡️ File uploads are processed securely
- 🤝 OpenAI API calls respect privacy settings
- 🚫 No data is shared with third parties
- 👤 Assaf controls all his personal information

## 🤝 Contributing

This is Assaf Azran's personal agent. For contributions or questions about the system, please reach out directly.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions about Assaf or this AI agent, please reach out directly to Assaf Azran.

---

**⭐ If you find this project interesting, consider giving it a star!**
#   M y _ A g e n t  
 