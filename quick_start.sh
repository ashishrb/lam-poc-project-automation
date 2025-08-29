#!/bin/bash

# Project Portfolio Management System - Quick Start Script

set -e

echo "🚀 Project Portfolio Management System - Quick Start"
echo "=================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first."
    echo "Visit: https://ollama.ai/download"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Check if Ollama is running
echo "🔍 Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama service is not running. Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Check required models
echo "🤖 Checking required AI models..."

# Check gpt-oss:20b
if ! ollama list | grep -q "gpt-oss:20b"; then
    echo "📥 Installing gpt-oss:20b model..."
    ollama pull gpt-oss:20b
else
    echo "✅ gpt-oss:20b model found"
fi

# Check nomic-embed-text:v1.5
if ! ollama list | grep -q "nomic-embed-text:v1.5"; then
    echo "📥 Installing nomic-embed-text:v1.5 model..."
    ollama pull nomic-embed-text:v1.5
else
    echo "✅ nomic-embed-text:v1.5 model found"
fi

# Setup environment
echo "⚙️  Setting up environment..."
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please review and edit if needed."
else
    echo "✅ .env file already exists"
fi

# Start services
echo "🚀 Starting services..."
make build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
make health

# Seed database
echo "🌱 Seeding database with sample data..."
make seed

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📱 Access your system at:"
echo "   • Web Interface: http://localhost"
echo "   • API Documentation: http://localhost:8001/docs"
echo "   • API Endpoints: http://localhost:8001/api/v1"
echo ""
echo "🔧 Useful commands:"
echo "   • make status     - Check service status"
echo "   • make logs       - View service logs"
echo "   • make restart    - Restart services"
echo "   • make clean      - Clean up everything"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "Happy project managing! 🚀"
