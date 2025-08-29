# 🚀 Project Portfolio Management System

A comprehensive, AI-powered project and portfolio management platform built with FastAPI, PostgreSQL, Chroma vector database, and Ollama AI models.

## ✨ Features

### 🎯 Core Management
- **Project Management**: Full lifecycle management with WBS, Gantt charts, and Kanban boards
- **Resource Management**: Capacity planning, skill mapping, and allocation optimization
- **Budget Management**: Multi-version budgets, actuals tracking, and variance analysis
- **Risk Management**: Risk identification, assessment, and mitigation planning
- **Portfolio Analytics**: Health scoring, dependency mapping, and scenario planning

### 🤖 AI-Powered Intelligence
- **AI Copilot**: Natural language interface for project queries and actions
- **RAG Engine**: Document ingestion, semantic search, and knowledge retrieval
- **Predictive Analytics**: Budget forecasting, resource optimization, and risk prediction
- **Automated Insights**: Variance explanations, anomaly detection, and recommendations

### 🔒 Enterprise Features
- **Multi-tenancy**: Isolated workspaces for different organizations
- **RBAC**: Role-based access control with fine-grained permissions
- **Audit Logging**: Complete audit trail for all system actions
- **Compliance**: PII detection, data residency, and export controls

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI API   │    │   AI Services   │
│   (HTML/CSS/JS) │◄──►│   (Async)       │◄──►│   (Ollama)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Queue   │    │   Chroma DB     │
│   (Main Data)   │    │   (Background)  │    │   (Vectors)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Backend**: FastAPI with async SQLAlchemy
- **Database**: PostgreSQL with advanced indexing
- **Vector DB**: Chroma for RAG and semantic search
- **AI Models**: Ollama with gpt-oss:20b and nomic-embed-text:v1.5
- **Queue**: Redis with RQ for background jobs
- **Frontend**: Vanilla HTML/CSS/JS (React-ready)
- **Infrastructure**: Docker Compose with health checks

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB RAM minimum (16GB recommended)
- Ollama running locally with required models

### 1. Install Ollama Models
```bash
# Install reasoning model
ollama pull gpt-oss:20b

# Install embedding model
ollama pull nomic-embed-text:v1.5
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd project-portfolio-management
cp env.example .env
# Edit .env with your configuration
```

### 3. Start the System
```bash
# One-command setup (first time)
make setup

# Or step by step:
make build
make seed
```

### 4. Access the System
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8001/docs
- **API Endpoints**: http://localhost:8001/api/v1

## 📊 Sample Data

The system comes pre-loaded with:

### Projects (3)
- **E-commerce Platform Redesign** (Green - 85% health)
- **Mobile App Development** (Green - 95% health)  
- **Data Migration Project** (Red - 65% health)

### Resources (20)
- **Engineering**: 12 developers, architects, DevOps engineers
- **Design**: 4 UI/UX designers and visual designers
- **Product**: 2 product managers and business analysts
- **Marketing**: 2 marketing specialists
- **Sales**: 1 sales representative

### Budgets
- **Development**: $150,000 (Project 1)
- **Design**: $80,000 (Project 2)
- **Infrastructure**: $120,000 (Project 3)

## 🎮 Usage Examples

### AI Copilot Queries
```
"Explain this month's budget variance for Project A"
"Generate a WBS for the mobile app project"
"Plan staffing for Sprint 14"
"Create a risk assessment for the data migration"
"Generate an executive weekly report"
```

### API Endpoints
```bash
# List projects with filtering
GET /api/v1/projects?status=active&risk_level=high

# Get project health metrics
GET /api/v1/projects/{id}/health

# AI-powered budget forecast
POST /api/v1/ai/forecast-budget
{
  "project_id": 1,
  "horizon": "3months",
  "drivers": {"scope_change": 0.1}
}

# Document search with RAG
POST /api/v1/ai/search
{
  "query": "project requirements and constraints",
  "filters": {"project_id": 1}
}
```

## 🛠️ Development

### Project Structure
```
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Configuration and database
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic services
│   └── web/                  # Web interface routes
├── scripts/                  # Database seeding and utilities
├── web/                      # Static files and templates
├── docker-compose.yml        # Service orchestration
├── Makefile                  # Development commands
└── requirements.txt          # Python dependencies
```

### Common Commands
```bash
# Development
make dev              # Start development mode
make logs             # View service logs
make shell            # Open API container shell
make test             # Run tests

# Database
make seed             # Seed sample data
make backup           # Backup database
make restore          # Restore from backup

# Operations
make status           # Check service status
make health           # Health check
make restart          # Restart services
make clean            # Clean up everything
```

### Adding New Features
1. **Models**: Add SQLAlchemy models in `app/models/`
2. **Schemas**: Create Pydantic schemas in `app/schemas/`
3. **API**: Add endpoints in `app/api/v1/endpoints/`
4. **Services**: Implement business logic in `app/services/`
5. **Frontend**: Add HTML templates in `web/templates/`

## 🔧 Configuration

### Environment Variables
```bash
# Core Settings
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+psycopg://app:app@db:5432/app

# AI Models
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_REASONER_MODEL=gpt-oss:20b
OLLAMA_EMBED_MODEL=nomic-embed-text:v1.5

# Security
JWT_SECRET=your-secure-secret
TENANT_DEFAULT=demo

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Ollama Model Configuration
```bash
# Install required models
ollama pull gpt-oss:20b
ollama pull nomic-embed-text:v1.5

# Verify models are available
ollama list
```

## 📈 Performance

### Benchmarks
- **API Response**: <200ms p95 for CRUD operations
- **RAG Search**: <2s p95 for document retrieval
- **AI Reasoning**: <5s p95 for complex queries
- **Database**: <100ms p95 for indexed queries

### Scaling
- **Horizontal**: Add API instances behind load balancer
- **Vertical**: Increase container resources
- **Database**: Read replicas and connection pooling
- **Vector DB**: Multiple Chroma instances

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Tenant isolation
- API rate limiting

### Data Protection
- PII detection and masking
- Encrypted data transmission
- Audit logging for compliance
- Data residency controls

### Network Security
- CORS configuration
- Security headers
- Input validation
- SQL injection prevention

## 🚨 Monitoring & Alerts

### Built-in Alerts
- **Budget Variance**: >±10% threshold
- **Schedule Slip**: >3 days critical path
- **Resource Overallocation**: >110% utilization
- **Quality Issues**: >30% defect increase

### Monitoring
- Service health checks
- Performance metrics
- Error tracking
- Resource utilization

## 🧪 Testing

### Test Coverage
```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/api/            # API tests
```

### Test Data
- In-memory SQLite for unit tests
- Test fixtures and factories
- Mock external services
- Automated test data cleanup

## 📚 API Documentation

### OpenAPI/Swagger
- Interactive API docs at `/docs`
- ReDoc documentation at `/redoc`
- OpenAPI schema export
- Request/response examples

### API Versioning
- Current: v1
- Backward compatibility
- Deprecation notices
- Migration guides

## 🌐 Deployment

### Production Setup
```bash
# Production configuration
cp env.example .env.prod
# Edit production settings

# Start production services
make prod

# Monitor deployment
make status
make health
```

### Docker Compose Overrides
```bash
# Development
docker-compose -f docker-compose.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request
5. Code review and merge

### Code Standards
- Black code formatting
- Flake8 linting
- Type hints required
- Docstring coverage
- Test coverage >80%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Reference](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### Community
- GitHub Issues for bugs
- GitHub Discussions for questions
- Wiki for user guides
- Examples and tutorials

### Enterprise Support
- Professional services
- Custom development
- Training and consulting
- SLA guarantees

---

**Built with ❤️ using modern AI and cloud-native technologies**

*For more information, visit our [documentation](docs/) or [contact us](mailto:support@example.com)*
