# 🚀 Quick Setup Guide

## Prerequisites
- Python 3.8+
- Git

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/Weche/agent-farmacia-chile.git
cd agent-farmacia-chile
```

### 2. Install dependencies

**Option A: Using pip**
```bash
pip install -r requirements_updated.txt
```

**Option B: Using the install script (Windows)**
```powershell
.\install_dependencies.ps1
```

**Option C: Using the install script (Linux/Mac)**
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 4. Run the application
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

### 5. Run tests
```bash
pytest tests/ -v
```

## 📁 Project Structure
- `app/` - Main application code
- `tests/` - Test suite (34 test files)
- `utils/` - Utility scripts
- `data/` - Data processing scripts
- `templates/` - Frontend templates
- `docs/` - Documentation

## 🔧 Key Features
- Spanish AI pharmacy assistant
- Smart commune matching with fuzzy search
- Real-time pharmacy data from MINSAL
- Comprehensive testing suite
- Docker deployment ready
