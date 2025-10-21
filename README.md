# Abhimata Golf Tournament Scoring System

A comprehensive web-based tournament scoring application for golf event organizers, built with FastAPI (Python) and React (TypeScript).

## 🏌️ Features

- **Multi-format Scoring**: Stroke Play, Net Stroke, System 36, Stableford
- **User Management**: Role-based access control (Super Admin, Event Admin, Event User)
- **Course Management**: Complete course and hole configuration
- **Event Management**: Tournament creation and participant management
- **Real-time Scoring**: Live leaderboard updates
- **Export Capabilities**: Excel reports and scorecards
- **Responsive Design**: Mobile-friendly interface

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**:
   ```bash
   python -m core.seed_data
   ```

5. **Start the server**:
   ```bash
   uvicorn main:app --reload
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## 🐳 Docker Setup

### Using Docker Compose

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f
   ```

3. **Stop services**:
   ```bash
   docker-compose down
   ```

## 🔐 Demo Accounts

The system comes with pre-configured demo accounts:

- **Super Admin**: `admin@abhimatagolf.com` / `admin123`
- **Event Admin**: `eventadmin@abhimatagolf.com` / `event123`
- **Event User**: `eventuser@abhimatagolf.com` / `user123`

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🏗️ Project Structure

```
AbhimataGolf/
├── backend/                 # FastAPI backend
│   ├── api/                # API route handlers
│   ├── core/               # Core utilities
│   ├── models/             # SQLModel database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── main.py            # FastAPI app entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   ├── store/         # State management
│   │   └── services/      # API services
│   └── package.json
├── specs/                  # Documentation
└── docker-compose.yml     # Docker configuration
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLModel**: Type-safe database ORM
- **SQLite**: Database (easily configurable for PostgreSQL)
- **JWT**: Authentication tokens
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool
- **TailwindCSS**: Styling
- **React Router**: Navigation
- **Zustand**: State management
- **React Query**: Data fetching

## 🔧 Configuration

### Backend Environment Variables

```env
DATABASE_URL=sqlite:///./abhimata_golf.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:5173"]
APP_VERSION=1.0.0
APP_NAME=Abhimata Golf API
DEBUG=true
```

### Frontend Configuration

The frontend automatically proxies API requests to the backend. No additional configuration needed for development.

## 📊 Database Schema

The system uses the following main entities:

- **Users**: System users with role-based permissions
- **Courses**: Golf courses with hole configurations
- **Events**: Tournament events
- **Participants**: Event participants
- **Scorecards**: Individual hole scores
- **Leaderboard Cache**: Cached leaderboard data

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment

1. **Build frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Set production environment variables**:
   ```bash
   export DATABASE_URL=postgresql://user:pass@host:port/db
   export SECRET_KEY=your-production-secret-key
   export DEBUG=false
   ```

3. **Run with production server**:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## 📝 Development Roadmap

### Phase 1: Core Foundation ✅
- [x] Project setup and structure
- [x] Database models and relationships
- [x] Authentication system
- [x] User management
- [x] Course management

### Phase 2: Event Management (Next)
- [ ] Event creation and management
- [ ] Participant registration
- [ ] Event configuration

### Phase 3: Scoring System
- [ ] Scorecard entry
- [ ] Scoring calculations
- [ ] Leaderboard generation

### Phase 4: Advanced Features
- [ ] Export functionality
- [ ] Real-time updates
- [ ] Mobile optimization

### Phase 5: Testing & Deployment
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Production deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team

---

**Abhimata Golf** - Making tournament scoring simple and efficient! 🏌️‍♂️
