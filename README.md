# Names App - React + FastAPI + PostgreSQL

A full-stack application with a React frontend, FastAPI backend, and PostgreSQL database. Fully compatible with Google Cloud SQL and Cloud Run.

## 📁 Project Structure

```
terraform/
├── frontend/                    # React + Vite
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   ├── main.jsx            # React entry point
│   │   └── index.css           # Styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/                     # FastAPI + SQLAlchemy
│   ├── main.py                 # FastAPI app with Cloud SQL models
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml          # Production setup
└── docker-compose.dev.yml      # Development setup (hot reload)
```

## 🚀 Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (if running without Docker)
- Python 3.11+ (if running without Docker)

### Option 1: Docker Compose (Recommended)

```bash
cd d:\terraform
docker-compose -f docker-compose.dev.yml up --build
```

Then open http://localhost:5173 in your browser.

**Services:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8080
- Database: localhost:5432

### Option 2: Local Development (Without Docker)

#### Backend
```bash
cd backend
pip install -r requirements.txt
# Set DATABASE_URL environment variable (or use default)
uvicorn main:app --reload
# API runs on http://localhost:8080
```

#### Frontend (in new terminal)
```bash
cd frontend
npm install
npm run dev
# App opens at http://localhost:5173
```

## 🌐 Deploying to Google Cloud

### ⚡ Automated Deployment with GitHub Actions (Recommended)

We provide a fully automated CI/CD pipeline that deploys everything with a single `git push`:

**Features:**
- ✅ Automatic frontend build and deploy to Google Cloud Storage
- ✅ Automatic backend Docker image build and push to Artifact Registry
- ✅ Automatic Cloud SQL setup (PostgreSQL 15)
- ✅ Automatic Cloud Run deployment
- ✅ Automatic secrets management in GCP Secret Manager
- ✅ Health check verification

**Quick Start:**
1. Configure GitHub secrets (see [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md))
2. Push to `main` branch
3. Watch deployment in GitHub Actions tab

**For detailed setup, see:**
- 📖 [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - Quick reference guide
- 📖 [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - Secret configuration
- 📖 [GCP_DEPLOYMENT_CONFIG.md](GCP_DEPLOYMENT_CONFIG.md) - Complete architecture details
- 📖 [.github/workflows/backend.yml](.github/workflows/backend.yml) - Workflow source

---

### Manual Deployment (Alternative)

If you prefer manual deployment steps:

### Prerequisites
- Google Cloud project with Cloud SQL and Cloud Run enabled
- `gcloud` CLI installed and authenticated

### Step 1: Build and Push Docker Images

```bash
# Set your Google Cloud project
export PROJECT_ID=your-gcp-project
export REGION=us-central1

# Build and push backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/names-backend:latest ./backend

# Build and push frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/names-frontend:latest ./frontend
```

### Step 2: Set Up Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create names-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region $REGION

# Create database
gcloud sql databases create names_db --instance=names-db

# Create user
gcloud sql users create postgres \
  --instance=names-db \
  --password
```

### Step 3: Deploy Backend to Cloud Run

```bash
gcloud run deploy names-backend \
  --image gcr.io/$PROJECT_ID/names-backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:names-db \
  --set-env-vars DATABASE_URL="postgresql://postgres:PASSWORD@/names_db?unix_socket_dir=/cloudsql/$PROJECT_ID:$REGION:names-db"
```

### Step 4: Deploy Frontend to Cloud Run

```bash
gcloud run deploy names-frontend \
  --image gcr.io/$PROJECT_ID/names-frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL="https://names-backend-xxxxx.a.run.app"
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/names` | List all names |
| POST | `/api/names` | Create a new name |
| GET | `/api/names/{id}` | Get a specific name |
| DELETE | `/api/names/{id}` | Delete a name |
| GET | `/health` | Health check |

## 💾 Database Schema

The `names` table is automatically created on startup:

```sql
CREATE TABLE names (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
  - Local: `postgresql://postgres:postgres@localhost:5432/names_db`
  - Cloud SQL: `postgresql://user:password@/dbname?unix_socket_dir=/cloudsql/PROJECT:REGION:INSTANCE`
- `PORT` - Server port (default: 8080)

### Frontend
- `VITE_API_URL` - Backend API URL (default: empty for same-origin)

## 🛠️ Development Tips

### Hot Reload
Both frontend and backend support hot reload in development mode:
- Frontend: Changes to `.jsx` and `.css` auto-refresh browser
- Backend: Changes to `.py` auto-restart server

### Database Inspection
```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/names_db

# List tables
\dt

# Query names
SELECT * FROM names;
```

### Docker Cleanup
```bash
# Stop all containers
docker-compose -f docker-compose.dev.yml down

# Remove volumes (clears database)
docker-compose -f docker-compose.dev.yml down -v
```

## 📝 CORS Configuration

CORS is enabled for all origins in development. For production, update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## 🐛 Troubleshooting

### CORS Errors
- Ensure backend is running on `http://localhost:8080`
- Check `VITE_API_URL` environment variable
- Frontend dev server proxy is configured in `vite.config.js`

### Database Connection Errors
- Verify PostgreSQL is running
- Check `DATABASE_URL` format
- Ensure database and user exist

### Port Already in Use
```bash
# Find and kill process on port 8080 (backend)
lsof -ti:8080 | xargs kill -9

# Find and kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

## 📄 License

MIT
