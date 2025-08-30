# Database Seeding System

This directory contains scripts for populating the PPM+AI database with sample data for development and testing.

## Scripts Overview

### `seed.py` - Comprehensive PPM+AI Seed Script
**Main seed script** that creates a complete demo environment with:
- **Users**: 1 admin, 1 manager, 20 developers
- **Projects**: ALPHA (AI-Powered PPM) and BETA (ML Model Deployment)
- **Tasks**: Realistic task breakdowns with dependencies
- **Resources**: Skill-based resource profiles
- **AI Drafts**: Sample AI-generated content
- **Documents**: Project charters and requirements
- **Audit Logs**: Comprehensive activity tracking
- **Financial Data**: Project budgets and expenses

**Features:**
- Deterministic randomness (seed=42)
- IST timezone handling
- Proper relationship establishment
- Data quality constraints
- Upsert logic for repeatable execution

### `seed_data.py` - Basic Seed Script
**Legacy script** for basic demo data:
- Simple tenant, roles, users setup
- Basic projects and resources
- Minimal data structure

### `seed_ai_first.py` - AI-First Specific Data
**Specialized script** for AI-First PPM features:
- AI draft examples
- Status update policies
- AI-specific configurations

### `clear_db.py` - Database Cleanup
**Utility script** to clear all data:
- Removes all records from all tables
- Resets auto-increment sequences
- Double confirmation required
- Safe for development environments

## Usage

### Using Make Commands (Recommended)
```bash
# Seed with comprehensive PPM+AI data
make seed

# Seed with basic data only
make seed-basic

# Seed with AI-First specific data
make seed-ai

# Clear database (WARNING: removes all data)
make clear-db
```

### Direct Script Execution
```bash
# Activate conda environment
conda activate lam-pm-311

# Run comprehensive seed
python scripts/seed.py

# Run basic seed
python scripts/seed_data.py

# Run AI-First seed
python scripts/seed_ai_first.py

# Clear database
python scripts/clear_db.py
```

### Docker Environment
```bash
# Seed database in running container
docker-compose exec api python scripts/seed.py

# Clear database in running container
docker-compose exec api python scripts/clear_db.py
```

## Data Structure

### Users and Roles
- **ADMIN**: Full system access
- **MANAGER**: Project management capabilities
- **DEVELOPER**: Task and timesheet access

### Projects
- **ALPHA**: AI-Powered Project Management Platform
  - Status: Active (Execution phase)
  - AI Autopublish: Enabled
  - Duration: 90 days
  
- **BETA**: Machine Learning Model Deployment System
  - Status: Planning phase
  - AI Autopublish: Disabled
  - Duration: 120 days

### Skills and Resources
- 15 technical skills (Python, JavaScript, React, etc.)
- 20 developer resources with skill assignments
- Realistic hourly rates and capacity

### AI Features
- AI-generated task drafts
- Status update automation policies
- Document processing examples
- Audit trail for AI actions

## Configuration

### Environment Variables
The seed scripts use the following environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `TIMEZONE`: Default timezone (Asia/Kolkata)

### Deterministic Data
All scripts use `random.seed(42)` for:
- Repeatable data generation
- Consistent test results
- Predictable development environment

## Validation

### Seed Integrity Tests
Run validation tests to ensure data quality:
```bash
# Run seed validation tests
python -m pytest tests/seed_validation/test_seed_integrity.py -v

# Run with coverage
python -m pytest tests/seed_validation/test_seed_integrity.py --cov=app --cov-report=term-missing
```

### Data Quality Checks
Tests verify:
- No duplicate emails/usernames
- Valid date ranges
- Proper relationships
- Required field completion
- Constraint compliance

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in environment
   - Verify database permissions

2. **Import Errors**
   - Activate conda environment: `conda activate lam-pm-311`
   - Check Python path in scripts
   - Verify model imports

3. **Constraint Violations**
   - Clear database first: `make clear-db`
   - Check for existing data conflicts
   - Verify model relationships

4. **Permission Errors**
   - Ensure database user has CREATE/INSERT permissions
   - Check file permissions on scripts
   - Verify Docker container access

### Reset and Restart
```bash
# Complete reset
make down
make clear-db
make up
make seed

# Or step by step
docker-compose down
python scripts/clear_db.py
docker-compose up -d
python scripts/seed.py
```

## Development

### Adding New Seed Data
1. Create new method in `PPMSeedData` class
2. Add to `seed_all()` method in correct order
3. Update validation tests
4. Document in this README

### Modifying Existing Data
1. Update seed methods
2. Adjust validation tests
3. Test with `make clear-db && make seed`
4. Update documentation

### Customizing for Different Environments
- Modify `IST_TIMEZONE` constant
- Adjust user counts and project details
- Customize skill sets and resource profiles
- Update financial data ranges

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review validation test output
3. Check database logs
4. Verify environment configuration

---

**Note**: These scripts are designed for development and testing environments. Do not use in production without proper review and modification.
