#!/bin/bash

# =============================================================================
# Secrets Setup Script for Production Deployment
# =============================================================================
# This script generates secure secrets for the application
# Run this script before deploying to production
# =============================================================================

set -e

echo "🔐 Setting up production secrets..."

# Create secrets directory if it doesn't exist
mkdir -p secrets

# Generate JWT Secret
echo "📝 Generating JWT secret..."
python3 -c "import secrets; print(secrets.token_urlsafe(32))" > secrets/jwt_secret.txt
echo "✅ JWT secret generated"

# Generate Database Password
echo "🗄️ Generating database password..."
python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))" > secrets/db_password.txt
echo "✅ Database password generated"

# Generate Redis Password
echo "🔴 Generating Redis password..."
python3 -c "import secrets; import string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24)))" > secrets/redis_password.txt
echo "✅ Redis password generated"

# Generate SMTP Password placeholder
echo "📧 Creating SMTP password placeholder..."
echo "your-smtp-app-password-here" > secrets/smtp_password.txt
echo "⚠️  Please update secrets/smtp_password.txt with your actual SMTP password"

# Set proper permissions
echo "🔒 Setting file permissions..."
chmod 600 secrets/*.txt
echo "✅ File permissions set to 600"

# Create .env template
echo "📋 Creating .env template..."
cat > .env.template << 'EOF'
# =============================================================================
# Production Environment Configuration
# =============================================================================
# Copy this file to .env and update with your actual values
# =============================================================================

# Database Configuration
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=$(cat secrets/db_password.txt)

# Redis Configuration
REDIS_PASSWORD=$(cat secrets/redis_password.txt)

# JWT Configuration
JWT_SECRET=$(cat secrets/jwt_secret.txt)

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=$(cat secrets/smtp_password.txt)
FROM_EMAIL=your-email@gmail.com
LEADERSHIP_EMAILS=leader1@company.com,leader2@company.com

# Application Configuration
ENVIRONMENT=production
DEBUG=False
TIMEZONE=UTC
TENANT_DEFAULT=demo

# AI/ML Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
AI_FIRST_MODE=true
AI_AUTOPUBLISH_DEFAULT=false
ENABLE_OCR=true

# File Storage
FILE_STORAGE_ROOT=/app/storage
EOF

echo "✅ .env.template created"

echo ""
echo "🎉 Secrets setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Update secrets/smtp_password.txt with your actual SMTP password"
echo "2. Copy .env.template to .env and update email configuration"
echo "3. Review and update LEADERSHIP_EMAILS in .env"
echo "4. Deploy using: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🔒 Security notes:"
echo "- All secret files have 600 permissions"
echo "- Secrets are stored in ./secrets/ directory"
echo "- Never commit .env or secrets/ to version control"
echo "- Use Docker secrets in production for additional security"
