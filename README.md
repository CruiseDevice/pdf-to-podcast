# PDF to Podcast

Convert PDF documents to podcast audio using AI.

## Project Structure

```
pdf_to_podcast/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic
│   │   └── utils/     # Helper functions
│   ├── tests/         # Test files
│   └── requirements.txt
├── frontend/          # Next.js frontend
```

## Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit http://localhost:8000/docs
