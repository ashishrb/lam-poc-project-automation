#!/usr/bin/env python3
import os


class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    DATABASE_URL = os.getenv('DATABASE_URL', 'autonomous_projects.db')
    API_VERSION = os.getenv('API_VERSION', 'v1')

