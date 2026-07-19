"""DockerConfig — generate Docker configurations."""
from __future__ import annotations
from typing import Any, Dict

class DockerConfig:
    @staticmethod
    def generate_dockerfile() -> str:
        return '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    @staticmethod
    def generate_compose() -> Dict[str, Any]:
        return {
            'version': '3.8',
            'services': {
                'aios': {'build': '.', 'ports': ['8000:8000'],
                         'environment': ['AIOS_ENV=production']},
                'redis': {'image': 'redis:7-alpine', 'ports': ['6379:6379']},
                'postgres': {'image': 'postgres:16-alpine', 'ports': ['5432:5432'],
                             'environment': {'POSTGRES_DB': 'aios', 'POSTGRES_USER': 'aios',
                                             'POSTGRES_PASSWORD': 'aios_secret'}},
            }
        }

    @staticmethod
    def generate_requirements() -> str:
        return '''# AI OS Dependencies
aiohttp>=3.9.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
redis>=5.0.0
pydantic>=2.0.0
structlog>=24.0.0
'''
