# Demo Quick Reference Card

## 🚀 Quick Start
1. **Start Application:** `python main.py`
2. **Access URL:** http://localhost:8001
3. **Health Check:** http://localhost:8001/health
4. **API Docs:** http://localhost:8001/docs

## 📋 Essential Demo Flow (40 minutes total)

### Phase 1: Overview (5 min)
- **Dashboard:** Show portfolio overview
- **Navigation:** Click through all main sections
- **Key Point:** AI integration throughout

### Phase 2: Core Features (10 min)
- **Projects:** Show list → Click "View" → Demonstrate tabs (Tasks, Dependencies, Risks, Files, History)
- **Resources:** Show list → Click "View" → Demonstrate tabs (Profile, Allocation, Skills, Utilization)
- **Key Point:** Comprehensive project and resource management

### Phase 3: AI Features (8 min)
- **AI Copilot:** Show chat interface
- **Sample Queries:**
  - "Create a project plan for mobile app development"
  - "Analyze risks for ALPHA project"
  - "Optimize resource allocation for Q1"
- **Key Point:** AI-driven decision making

### Phase 4: Advanced Features (7 min)
- **Finance:** Show budget tracking and alerts
- **Vector Index:** Admin → Data & Governance → Show collections
- **Alerts:** Show monitoring and notifications
- **Key Point:** Real-time monitoring and controls

### Phase 5: Admin & Developer (10 min)
- **Admin Dashboard:** Show all sections (Tenant, AI Control, Connectors, etc.)
- **Developer Workbench:** Show all sections (My Workbench, DevOps, RAG, etc.)
- **Key Point:** Role-based access and specialized interfaces

## 🎯 Key Demo Scripts

### Opening Script
*"Welcome to our AI-based Project Management Automation system. This system transforms traditional project management by integrating AI capabilities throughout - from planning to execution to monitoring."*

### AI Copilot Script
*"This is our AI Copilot. It can help with project planning, risk assessment, resource optimization, and decision-making. Watch how it creates comprehensive project plans in seconds."*

### Admin Script
*"The Admin dashboard provides comprehensive system management. Note this is a demo version with placeholder data for demonstration purposes."*

### Developer Script
*"The Developer Workbench provides specialized tools for development teams, including AI-assisted coding, log analysis, and automated testing."*

## 🚨 Quick Troubleshooting

### If Application Won't Start
```bash
# Check if port is in use
lsof -i :8001
# Kill process if needed
pkill -f "python main.py"
# Restart
python main.py
```

### If Pages Don't Load
1. Clear browser cache
2. Check browser console (F12)
3. Verify application is running: `curl http://localhost:8001/health`

### If AI Not Working
1. Check Ollama: `ollama list`
2. Test AI endpoint: `curl http://localhost:8001/api/v1/ai-copilot/chat`
3. Verify models are available

## 📊 Success Metrics
- ✅ All pages load without errors
- ✅ AI Copilot responds within 3 seconds
- ✅ Tabbed interfaces work smoothly
- ✅ Demo data displays correctly
- ✅ Navigation is consistent

## 🎬 Demo Variations

### For Executives
- Focus on ROI and business value
- Show executive dashboards
- Emphasize cost savings and risk mitigation

### For Technical Teams
- Show API documentation
- Demonstrate integration capabilities
- Highlight AI model configurations

### For Project Managers
- Focus on project portfolio benefits
- Show resource optimization
- Demonstrate risk management

## 📞 Support
- **Technical Issues:** Check application logs
- **Demo Questions:** Reference DEMO_GUIDE.md
- **System Status:** http://localhost:8001/health

---

*Keep this card handy during the demo for quick reference and troubleshooting.*
