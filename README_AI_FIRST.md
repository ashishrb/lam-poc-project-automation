# 🚀 AI-First PPM System

A comprehensive Project Portfolio Management system built with **AI-first principles**, where AI proactively plans, creates, allocates, and schedules work while humans review, modify, and override as needed.

## ✨ Key Features

### 🤖 AI-First Operating Mode
- **Auto-Plan**: AI generates draft WBS (milestones, tasks, dependencies, dates) when projects are created or documents are uploaded
- **Auto-Create**: Draft tasks are created in staging and optionally auto-published based on project policy
- **Auto-Allocate**: AI assigns assignees based on skill match, velocity, availability, and performance
- **Auto-Schedule**: AI proposes start/due dates and effort estimates
- **Explainability**: Per-item rationale + confidence scores with model reasoning surfaced in UI

### 🛡️ AI Guardrails
- **JSON Schema Validation**: Ensures AI outputs conform to expected structure
- **Hard Constraints**: No due dates beyond project end, budget caps, workload limits
- **Auto-Repair**: Automatic repair pass when model output is invalid
- **Business Rule Enforcement**: Project duration limits, task dependencies, resource allocation rules

### 📊 Role-Tailored Dashboards
- **Developer**: My Tasks Kanban with AI "next best action" chips
- **Manager**: Portfolio overview with AI insights and auto-generated weekly plans
- **Admin**: Model settings, feature flags, and system configuration

### 📝 Configurable Status Updates
- **AI-Generated Nudges**: Pre-filled status updates based on task history and LLM analysis
- **Policy-Driven**: Configurable frequency, requirements, and escalation rules
- **One-Click Submit**: Developers can submit AI-generated updates with minimal effort

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.x**: Next-generation Python ORM
- **PostgreSQL**: Primary database with JSONB support for AI outputs
- **Redis**: Caching and session management
- **ChromaDB**: Vector database for document embeddings and RAG
- **Ollama**: Local LLM integration for AI operations

### AI Services
- **AI-First Service**: Core AI orchestration and planning
- **AI Guardrails**: Validation and repair of AI outputs
- **RAG Engine**: Document processing and retrieval
- **Background Tasks**: Celery for async AI operations

### Security & Compliance
- **JWT Authentication**: Secure token-based auth with refresh
- **RBAC**: Role-based access control (Developer, Manager, Admin)
- **Audit Logging**: Complete audit trail for all AI actions
- **Rate Limiting**: API protection and abuse prevention

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Ollama with `gpt-oss:20b` model
- PostgreSQL 15+
- Redis 7+

### 1. Clone and Setup
```bash
git clone <repository>
cd lam-poc-project-automation-1
```

### 2. Environment Configuration
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```env
# Database
DATABASE_URL=postgresql+psycopg://ppm_user:ppm_pass@localhost:5432/ppm
REDIS_URL=redis://localhost:6379/0

# AI Configuration
OLLAMA_BASE_URL=http://127.0.0.1:11434
AI_MODEL_NAME=gpt-oss:20b
AI_FIRST_MODE=true
AI_AUTOPUBLISH_DEFAULT=false
ENABLE_OCR=true

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Or use Makefile
make up
```

### 4. Seed Demo Data
```bash
# Run the seed script
python scripts/seed_ai_first.py
```

### 5. Access the System
- **API**: http://localhost:8001
- **Admin Panel**: http://localhost:8001/admin
- **API Docs**: http://localhost:8001/docs

## 📚 API Endpoints

### AI-First Operations
```
POST /api/ai-first/autoplan          # Auto-plan project with AI
POST /api/ai-first/upload-and-plan   # Upload doc + auto-plan
POST /api/ai-first/allocate-resources # AI resource allocation
POST /api/ai-first/generate-status-update # AI status update draft
POST /api/ai-first/refine-task       # Ask AI to refine task
POST /api/ai-first/publish-from-draft # Publish AI draft
POST /api/ai-first/reallocate        # Re-run AI allocation
```

### AI Draft Management
```
GET    /api/ai-first/drafts/{project_id}     # Get project drafts
PUT    /api/ai-first/drafts/{id}/approve     # Approve draft
PUT    /api/ai-first/drafts/{id}/reject      # Reject draft
POST   /api/ai-first/validate-output         # Validate AI output
```

### Status Update Management
```
GET /api/ai-first/status-update-policies/{project_id}
GET /api/ai-first/required-updates/{user_id}
GET /api/ai-first/ai-insights/{project_id}
```

## 🔧 Configuration

### AI-First Mode Settings
```python
# app/core/config.py
AI_FIRST_MODE = True                    # Enable AI-first mode
AI_AUTOPUBLISH_DEFAULT = False          # Default auto-publish setting
ENABLE_OCR = True                       # Enable OCR for documents
AI_GUARDRAILS_ENABLED = True            # Enable AI guardrails
AI_CONTINUOUS_LEARNING = True           # Enable continuous learning

# Guardrail Limits
AI_MAX_PROJECT_DURATION_DAYS = 730      # 2 years max
AI_MAX_TASK_DURATION_DAYS = 90         # 3 months max
AI_MAX_WORKLOAD_PERCENT = 120          # 120% max workload
```

### Project-Level Settings
```python
# Each project can override defaults
project.ai_autopublish = True           # Auto-publish AI tasks
project.allow_dev_task_create = True    # Allow devs to create tasks
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run AI-first specific tests
pytest tests/test_ai_first.py -v

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage Targets
- **Services**: ≥80% coverage
- **Overall**: ≥70% coverage
- **AI-First Flows**: 100% coverage

## 📊 Demo Data

The seed script creates:

### Users
- **Admin**: `admin@demo.com` / `admin123`
- **Manager**: `manager@demo.com` / `manager123`
- **Developer 1**: `dev1@demo.com` / `dev123`
- **Developer 2**: `dev2@demo.com` / `dev123`

### Projects
- **AI-First PPM System**: Active project with AI-generated tasks
- **Mobile App Development**: Planning phase project

### AI Drafts
- **WBS Draft**: Approved work breakdown structure
- **Allocation Draft**: Pending resource allocation

## 🔄 Background Tasks

### Celery Configuration
```python
# app/core/celery_app.py
celery_app = Celery(
    'ppm_ai_first',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)
```

### Scheduled Tasks
- **Status Update Checks**: Every 5 minutes
- **AI Insights Generation**: Every hour
- **Draft Cleanup**: Daily

### Task Queues
- **ai_queue**: AI operations and model training
- **status_queue**: Status update processing
- **document_queue**: Document processing and OCR

## 🛡️ Security Features

### Authentication
- JWT tokens with refresh mechanism
- Session audit logging
- Rate limiting per user/IP

### Authorization
- Role-based access control
- Project-level permissions
- API endpoint protection

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CORS configuration

## 📈 Monitoring & Observability

### Health Checks
```bash
# System health
GET /api/ai-first/health

# Service status
GET /api/ai/status
```

### Metrics
- AI operation latency
- Token usage and costs
- Validation success rates
- Background task performance

### Logging
- Structured JSON logging
- AI operation audit trails
- Error tracking and alerting

## 🚀 Deployment

### Production Considerations
- **Environment Variables**: Secure configuration management
- **Database**: Connection pooling and read replicas
- **Redis**: Cluster configuration for high availability
- **Monitoring**: APM integration and alerting
- **Backup**: Automated database and file backups

### Docker Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale worker=3
```

## 🔮 Future Enhancements

### Planned Features
- **Advanced AI Models**: Integration with GPT-4, Claude, and others
- **Machine Learning**: Predictive analytics and risk assessment
- **Natural Language**: Conversational project management
- **Integration**: Jira, Azure DevOps, GitHub integration
- **Mobile App**: React Native mobile application

### AI Improvements
- **Fine-tuning**: Custom model training on project data
- **Multi-modal**: Image and document understanding
- **Collaborative AI**: Team-based AI learning
- **Explainable AI**: Enhanced reasoning and transparency

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Run linting
black app/
ruff check app/

# Run tests
pytest
```

### Code Standards
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit and integration test coverage
- **Linting**: Black + Ruff for code quality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Reference](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER.md)

### Issues
- [GitHub Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

### Community
- [Discord Server](https://discord.gg/your-server)
- [Slack Workspace](https://your-slack.slack.com)

---

**Built with ❤️ and AI 🤖 for modern project management**
