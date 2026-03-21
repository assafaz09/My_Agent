#!/usr/bin/env python3
"""
Manual upload script for Qdrant - bypasses the complex API
"""

import asyncio
import os
import sys
from pathlib import Path
import PyPDF2
from docx import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
import json
from datetime import datetime

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6334
COLLECTION_NAME = "personal_knowledge"

class ManualQdrantUploader:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT
        )
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_text(self, file_path: str) -> str:
        """Extract text based on file extension"""
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            return self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            return self.extract_text_from_txt(file_path)
        elif ext == '.md':  # Added Markdown support
            return self.extract_text_from_txt(file_path)  # Same as txt for now
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def generate_embedding(self, text: str) -> list:
        """Generate embedding using OpenAI"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            
            chunks.append(text[start:end])
            
            if end >= len(text):
                break
            
            start = end - overlap
        
        return chunks
    
    def create_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                collection.name == COLLECTION_NAME 
                for collection in collections.collections
            )
            
            if not collection_exists:
                self.qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created collection: {COLLECTION_NAME}")
            else:
                print(f"✅ Collection {COLLECTION_NAME} already exists")
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            raise
    
    def upload_file(self, file_path: str):
        """Upload a single file to Qdrant"""
        try:
            print(f"📤 Processing: {Path(file_path).name}")
            
            # Extract text
            text = self.extract_text(file_path)
            print(f"📄 Extracted {len(text)} characters")
            
            # Create chunks
            chunks = self.chunk_text(text)
            print(f"🔢 Created {len(chunks)} chunks")
            
            import uuid

# Generate embeddings and create points
            points = []
            for i, chunk_text in enumerate(chunks):
                print(f"🧠 Generating embedding for chunk {i+1}/{len(chunks)}")
                embedding = self.generate_embedding(chunk_text)
                
                point = PointStruct(
                    id=str(uuid.uuid4()),  # Use UUID instead of string
                    vector=embedding,
                    payload={
                        "content": chunk_text,
                        "metadata": {
                            "filename": Path(file_path).name,
                            "file_path": str(file_path),
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "file_size": os.path.getsize(file_path),
                            "processed_at": datetime.now().isoformat()
                        }
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            print(f"💾 Uploading {len(points)} points to Qdrant...")
            self.qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            
            print(f"✅ Successfully uploaded: {Path(file_path).name}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return False
    
    def upload_directory(self, directory_path: str):
        """Upload all supported files from directory"""
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return
        
        # Find supported files
        supported_extensions = {'.pdf', '.txt', '.docx', '.md'}  # Added .md support
        files = [f for f in directory.rglob('*') if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not files:
            print(f"❌ No supported files found in {directory}")
            return
        
        print(f"📁 Found {len(files)} files to upload")
        
        # Create collection
        self.create_collection()
        
        # Upload files
        successful = 0
        failed = 0
        
        for file_path in files:
            if self.upload_file(str(file_path)):
                successful += 1
            else:
                failed += 1
        
        print(f"\n📊 Upload Summary:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Total: {len(files)}")
    
    def search_knowledge(self, query: str, limit: int = 3):
        """Search the knowledge base"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.5
            )
            
            print(f"\n🔍 Search results for: '{query}'")
            for i, hit in enumerate(search_result):
                print(f"\n{i+1}. Score: {hit.score:.3f}")
                print(f"   File: {hit.payload['metadata']['filename']}")
                print(f"   Content: {hit.payload['content'][:200]}...")
                
        except Exception as e:
            print(f"❌ Search error: {e}")

def main():
    uploader = ManualQdrantUploader()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manual_upload.py <file_path>")
        print("  python manual_upload.py <directory_path>")
        print("  python manual_upload.py search <query>")
        return
    
    command = sys.argv[1]
    
    if command == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        uploader.search_knowledge(query)
    elif os.path.isfile(command):
        uploader.create_collection()
        uploader.upload_file(command)
    elif os.path.isdir(command):
        uploader.upload_directory(command)
    else:
        print(f"❌ Invalid path: {command}")

if __name__ == "__main__":
    main()
