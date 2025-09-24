# Pookie Backend - BTEB Results API

Production-ready backend API for BTEB Results mobile application.

## Features

- **5 Supabase Projects**: Multi-project database support with automatic fallback
- **Web API Fallback**: External API integration for additional coverage
- **CGPA Support**: Comprehensive CGPA data retrieval
- **Production Ready**: Optimized for Vercel deployment

## Architecture

### Database Layer
- **Primary**: Main production database
- **Secondary**: Backup database with CGPA records
- **Tertiary**: Extended coverage database
- **Backup1 & Backup2**: Additional redundancy

### API Endpoints

- `POST /api/search-result` - Search student results
- `GET /health` - Health check
- `GET /api/projects` - List Supabase projects
- `GET /api/web-apis` - List web APIs
- `GET /api/stats` - Database statistics

## Deployment

### Vercel Deployment
1. Connect GitHub repository to Vercel
2. Set environment variables for Supabase projects
3. Deploy automatically on push

### Environment Variables Required
```
SUPABASE_PRIMARY_URL=https://hddphaneexloretrisiy.supabase.co
SUPABASE_PRIMARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SECONDARY_URL=https://ncjleyktzilulflbjfdg.supabase.co
SUPABASE_SECONDARY_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Testing

Test with known roll numbers:
- `502760` (2016, Diploma in Engineering) - Found in secondary project with CGPA
- `721942` (2022, Diploma in Engineering) - Found in primary project
- `999999` (2022, Diploma in Engineering) - Not found (tests web API fallback)

## Dependencies

- Flask 2.3.3
- Supabase 2.0.3
- Flask-CORS 4.0.0
- Requests 2.31.0

## Status

✅ **Production Ready**
✅ **Vercel Compatible**
✅ **Multi-Project Support**
✅ **Web API Fallback**
✅ **CGPA Integration**
