# VonBot - Academic Scheduling Tool

**AI-powered academic scheduling and course recommendation system for university administration**

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Key Features](#key-features)
- [Database Schema](#database-schema)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

---

## 📖 Project Overview

VonBot is a Streamlit-based web application designed to help university administrators:
1. **Select Active Students** - Query students based on recent activity
2. **Match Courses** - Analyze curriculum requirements vs. completed courses
3. **Create Rosters** - Build class rosters with conflict checking
4. **Optimize Schedules** - Assign time slots while avoiding student conflicts
5. **Send Notifications** - Email and Telegram integration for communications

### Use Case
Academic staff need to identify which students need which courses, create balanced class sections, schedule them without conflicts, and notify students - all from a legacy MSSQL 2012 database.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Web UI (app.py)          │
│  - Admin Dashboard                          │
│  - Student Portal (placeholder)             │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴─────────────┬──────────────┬─────────────┐
    │                        │              │             │
┌───▼────┐            ┌──────▼───┐   ┌─────▼─────┐  ┌───▼────┐
│ Logic  │            │ Database │   │  Models   │  │Services│
│ Layer  │            │  Layer   │   │           │  │        │
└────────┘            └──────────┘   └───────────┘  └────────┘
    │                      │                             │
    ├─ student_selection   ├─ connection.py             ├─ email_service
    ├─ course_matching     ├─ local_db.py               └─ telegram_bot
    └─ optimization        │
                           └─ Legacy MSSQL 2012 (pymssql + FreeTDS)

┌─────────────────────────────────────────────┐
│   Legacy Adapter Service (Separate)        │
│   FastAPI REST bridge to MSSQL 2012        │
│   (services/legacy-adapter/)                │
└─────────────────────────────────────────────┘
```

### Key Components

1. **Frontend (Streamlit)**
   - Interactive dashboard with tabs
   - Real-time progress indicators
   - Session state management
   - CSV export capabilities

2. **Logic Layer**
   - Student filtering and selection
   - Course requirement matching
   - Schedule optimization
   - Conflict detection

3. **Database Layer**
   - Legacy MSSQL 2012 connection (pymssql)
   - SQLite for session management
   - FreeTDS configuration for compatibility

4. **Services Layer**
   - Email notifications (SMTP)
   - Telegram bot integration
   - Future: SMS, webhooks, etc.

5. **Legacy Adapter (Microservice)**
   - FastAPI REST API
   - Secure bridge to MSSQL
   - Schema mapping
   - Audit logging

---

## 🛠️ Tech Stack

### Core
- **Python 3.12** - Primary language
- **Streamlit** - Web UI framework
- **Pandas** - Data manipulation
- **Polars** - High-performance data processing

### Database
- **pymssql** - MSSQL 2012 driver
- **FreeTDS 7.3** - TDS protocol for legacy MSSQL
- **SQLite** - Local session storage

### Services
- **SMTP** - Email delivery
- **Telegram Bot API** - Instant messaging
- **python-dotenv** - Environment management

### Development
- **pytest** - Testing framework (in progress)
- **Docker** - Legacy adapter containerization

---

## 📁 Project Structure

```
vonbot/
├── app.py                          # Main Streamlit application
├── main.py                         # CLI entry point (minimal)
├── .env                            # Environment variables (DO NOT COMMIT)
├── .env.example                    # Template for credentials
├── requirements.txt                # Python dependencies
├── freetds.conf                    # FreeTDS configuration for MSSQL 2012
│
├── database/
│   ├── connection.py               # MSSQL connection & settings
│   └── local_db.py                 # SQLite for session management
│
├── logic/
│   ├── student_selection.py       # Query active students
│   ├── course_matching.py         # Match students to required courses
│   └── optimization.py             # Schedule optimization & conflict checking
│
├── models/
│   └── data_models.py              # Data classes (Student, Course, Recommendation)
│
├── services/
│   ├── email_service.py            # SMTP email sending
│   ├── telegram_bot.py             # Telegram notifications
│   └── legacy-adapter/             # Separate FastAPI microservice
│       ├── app/
│       │   ├── main.py             # FastAPI app
│       │   ├── config.py           # Configuration
│       │   ├── models.py           # Pydantic models
│       │   ├── mappers.py          # Schema mapping
│       │   └── database.py         # MSSQL connection
│       ├── tests/                  # API tests
│       ├── Dockerfile
│       └── README.md               # Detailed adapter docs
│
├── tests/
│   ├── test_db_real.py             # Database connection tests
│   ├── diagnose_connection.py      # Connection diagnostics
│   ├── test_imports.py             # Import verification
│   └── inspect_*.py                # Schema inspection utilities
│
├── .github/
│   └── copilot-instructions.md     # AI coding assistant guidelines
│
└── WARP.md                         # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.12+
- Access to MSSQL 2012 database
- SMTP server (Gmail, etc.) for email
- Telegram Bot Token (optional)

### Installation Steps

```bash
# 1. Clone the repository
cd ~/Development/key/vonbot

# 2. Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Configure credentials (see Configuration section)
nano .env

# 6. Test database connection
python tests/diagnose_connection.py

# 7. Run the application
streamlit run app.py
```

### macOS-Specific (M1/M2)
If you encounter pymssql build issues:
```bash
# Install FreeTDS via Homebrew
brew install freetds

# Set environment variables before pip install
export LDFLAGS="-L/opt/homebrew/opt/freetds/lib"
export CPPFLAGS="-I/opt/homebrew/opt/freetds/include"
pip install pymssql
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following:

```bash
# Database Configuration
LEGACY_DB_HOST=96.9.90.64
LEGACY_DB_PORT=1500
LEGACY_DB_USER=sa
LEGACY_DB_PASSWORD=your_password_here
LEGACY_DB_NAME=New_PUCDB

# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Email/SMTP Configuration
# For Gmail, use an App Password (not your regular password)
# https://support.google.com/accounts/answer/185833
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

### FreeTDS Configuration

The `freetds.conf` file is configured for MSSQL 2012 compatibility:
- TDS version 7.3
- Encryption disabled (legacy server)
- Connection timeout: 10 seconds

**Location**: Project root (`/Users/jeffreystark/Development/key/vonbot/freetds.conf`)

The application automatically sets `FREETDSCONF` environment variable on startup.

---

## 🎯 Key Features

### 1. Student Selection
**File**: `logic/student_selection.py`

- Query students active in last N months
- Uses `vw_BAlatestgrade` view
- Filters by BatchIDForMaster (major code)
- Returns: StudentId, Name, Email, MajorCode, Cohort, LastActiveDate

### 2. Course Matching
**File**: `logic/course_matching.py`

- Loads curriculum requirements from CSV: `curriculum_canonical_requirements_majors_1-6.csv`
- Maps student major code to requirements
- Queries student transcript (`vw_BAlatestgrade`)
- Identifies missing courses (not yet completed)
- Generates needs matrix (Students × Courses)
- Fetches course offering history

**Major Mappings**:
```python
major_map = {
    'BAD': 1,  # Business Administration
    'THM': 3,  # Tourism & Hospitality
    'FIN': 4,  # Finance
    'TES': 5,  # TESOL
    'INT': 6,  # International Relations
}
```

### 3. Class Rosters
**UI Tab**: "Class Rosters"

- Select course from demand list
- Filter eligible students by cohort
- Interactive multi-select table
- Avoid duplicate assignments
- Export roster as CSV

### 4. Schedule Optimization
**File**: `logic/optimization.py`

**Available Time Slots**:
- MW_1800, MW_1930
- TTh_1800, TTh_1930
- Sat_AM, Sat_PM
- Fri_Eve

**Conflict Detection**:
- Identifies students needing multiple courses in same time slot
- Reports: StudentId, Name, ConflictSlot, Courses[]

### 5. Communications
**Files**: `services/email_service.py`, `services/telegram_bot.py`

- Bulk email to students with course lists
- Telegram broadcast to channels/groups
- Graceful fallback to mock output if credentials not configured

---

## 🗄️ Database Schema

### Legacy MSSQL 2012 Tables/Views

**Students Table**
```sql
ID                  -- Student ID (numeric)
Name                -- Full name
schoolemail         -- Student email
BatchIDForMaster    -- Major code (e.g., 'TES-53E')
lastenroll          -- Last enrollment date
selprogram          -- Program ID (e.g., 87 for BA)
bagraddate          -- Expected graduation date
```

**vw_BAlatestgrade View** (Student transcript)
```sql
id                  -- Student ID
coursecode          -- Course code (e.g., 'LAW-273')
grade               -- Letter grade (A-F, IP, I, W)
termid              -- Term ID (e.g., '2023T2')
termstart           -- Term start date
```

**AcademicCourseTakers Table** (Course sections)
```sql
ClassId             -- Format: TermId!$CourseId!$Section
StudentID           -- Student ID
-- Note: Used to check course offering history
```

**Terms Table**
```sql
TermId              -- Term ID
TermName            -- Display name
StartDate           -- Term start date
```

### Local SQLite (admin_session.db)

**session_students**
```sql
id                  -- Primary key
student_id          -- Student ID
name                -- Student name
major               -- Major code
selected            -- Boolean flag
```

**course_recommendations**
```sql
id                  -- Primary key
student_id          -- Student ID
course_id           -- Course code
course_name         -- Course display name
priority            -- Integer priority
status              -- 'pending', 'approved', etc.
```

---

## 💻 Development Workflow

### Running the App

```bash
# Start Streamlit app
streamlit run app.py

# Runs on http://localhost:8501
```

### Testing Database Connection

```bash
# Comprehensive connection diagnostics
python tests/diagnose_connection.py

# Test real database queries
python tests/test_db_real.py

# Inspect database schema
python tests/inspect_students.py
python tests/inspect_terms_view.py
```

### Adding New Features

1. **Add logic** in `logic/` directory
2. **Update UI** in `app.py` (add new tab or modify existing)
3. **Add tests** in `tests/` directory
4. **Update requirements** if new dependencies added
5. **Document** in this WARP.md file

### Working with Session State

Streamlit uses `st.session_state` for data persistence:

```python
# Store data
st.session_state['students_df'] = df

# Retrieve data
if 'students_df' in st.session_state:
    df = st.session_state['students_df']
```

**Important session state keys**:
- `students_df` - Active students DataFrame
- `needs_df` - Course needs matrix
- `demand_df` - Course demand summary
- `rosters` - Dict of course rosters: `{course_code: [student_dicts]}`
- `final_schedule` - Dict of time slot assignments: `{course_code: time_slot}`

---

## 🧪 Testing

### Current Tests

```bash
# Test database connection
python tests/test_db_real.py

# Diagnose connection issues
python tests/diagnose_connection.py

# Verify imports
python tests/test_imports.py

# Inspect database schema
python tests/inspect_students.py
python tests/inspect_terms_view.py
```

### Adding Unit Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Create test file
touch tests/test_student_selection.py

# Run tests
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/ --cov=logic  # With coverage
```

### Test Structure Example

```python
# tests/test_student_selection.py
import pytest
from logic.student_selection import get_active_students

def test_get_active_students_valid():
    df = get_active_students(6)
    assert not df.empty
    assert 'StudentId' in df.columns
    assert 'Name' in df.columns

def test_get_active_students_no_results():
    df = get_active_students(0)
    assert df.empty or len(df) == 0
```

---

## 🚢 Deployment

### Local Development (Current)

```bash
streamlit run app.py
```

### Production Deployment (Future)

#### Option 1: Streamlit Cloud
1. Push to GitHub
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Set secrets in dashboard (replaces .env)

#### Option 2: VPS/Server

```bash
# Install as systemd service
sudo nano /etc/systemd/system/vonbot.service

[Unit]
Description=VonBot Academic Scheduling Tool
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/vonbot
Environment="PATH=/home/ubuntu/vonbot/.venv/bin"
ExecStart=/home/ubuntu/vonbot/.venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable vonbot
sudo systemctl start vonbot

# Setup nginx reverse proxy
sudo nano /etc/nginx/sites-available/vonbot
# Configure SSL with Let's Encrypt
```

#### Option 3: Docker

```bash
# Create Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]

# Build and run
docker build -t vonbot .
docker run -p 8501:8501 --env-file .env vonbot
```

---

## 📋 Common Tasks

### Add a New Time Slot

1. Edit `logic/optimization.py`:
```python
TIME_SLOTS = [
    "MW_1800", "MW_1930",
    "TTh_1800", "TTh_1930",
    "Sat_AM", "Sat_PM",
    "Fri_Eve",
    "Sun_AM"  # New slot
]
```

2. No other changes needed - UI auto-updates

### Add a New Major

1. Edit `logic/course_matching.py`:
```python
major_map = {
    'BAD': 1,
    'THM': 3,
    'FIN': 4,
    'TES': 5,
    'INT': 6,
    'PSY': 7,  # New major
}
```

2. Ensure curriculum CSV has requirements for major_id=7

### Export All Rosters at Once

```python
# Add to app.py in Class Rosters tab
if st.button("Export All Rosters"):
    for course, roster in st.session_state['rosters'].items():
        if roster:
            df = pd.DataFrame(roster)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Download {course}",
                data=csv,
                file_name=f"roster_{course}.csv",
                mime="text/csv",
                key=f"export_{course}"
            )
```

### Change Database Connection

```bash
# Edit .env file
nano .env

# Update connection details
LEGACY_DB_HOST=new_host
LEGACY_DB_PORT=new_port
LEGACY_DB_USER=new_user
LEGACY_DB_PASSWORD=new_password
LEGACY_DB_NAME=new_database

# Test connection
python tests/diagnose_connection.py

# Restart app
streamlit run app.py
```

---

## 🔧 Troubleshooting

### Database Connection Issues

**Problem**: "Database connection failed"

**Solutions**:
1. Check `.env` file exists and has correct credentials
2. Verify MSSQL server is running and accessible
3. Test connectivity: `telnet 96.9.90.64 1500`
4. Check FreeTDS configuration: `cat freetds.conf`
5. Run diagnostics: `python tests/diagnose_connection.py`
6. Check firewall rules on MSSQL server

### FreeTDS/pymssql Issues

**Problem**: "Error: DB-Lib error message" or "Login timeout"

**Solutions**:
1. Verify TDS version in `freetds.conf` (should be 7.3 for MSSQL 2012)
2. Check encryption settings (should be `off` for legacy)
3. Increase timeout: edit `freetds.conf` → `connect timeout = 30`
4. Enable logging:
   ```conf
   [global]
   dump file = /tmp/freetds.log
   ```
5. Review logs: `tail -f /tmp/freetds.log`

### Empty Data / No Students Found

**Problem**: Queries return empty DataFrames

**Solutions**:
1. Check date filters in `student_selection.py`
2. Verify view permissions: `SELECT * FROM vw_BAlatestgrade LIMIT 10`
3. Inspect actual data: `python tests/inspect_students.py`
4. Adjust SQL query date range
5. Check if students have BatchIDForMaster populated

### Email Not Sending

**Problem**: Emails not being sent

**Solutions**:
1. Check SMTP credentials in `.env`
2. For Gmail: Enable 2FA and create App Password
3. Check SMTP host/port: `telnet smtp.gmail.com 587`
4. Review logs in terminal for error messages
5. Test with mock mode (no credentials) to verify logic works

### Telegram Bot Not Working

**Problem**: Telegram messages not sending

**Solutions**:
1. Verify bot token from @BotFather
2. Ensure bot is added to channel/group
3. Get correct chat ID:
   - For channels: `@channel_name` or numeric ID
   - For groups: Numeric ID (usually negative)
4. Test token: `curl https://api.telegram.org/bot<TOKEN>/getMe`
5. Check bot permissions in channel/group settings

### Session State Not Persisting

**Problem**: Data disappears on page reload

**Solutions**:
1. Streamlit session state resets on browser reload
2. Use SQLite for persistent storage:
   ```python
   from database.local_db import get_local_connection
   conn = get_local_connection()
   df.to_sql('my_table', conn, if_exists='replace')
   ```
3. Export important data as CSV before closing

### Conflicts Not Detected Properly

**Problem**: Schedule shows no conflicts but students can't attend both courses

**Solutions**:
1. Verify time slots are assigned (not "Unassigned")
2. Check needs matrix has correct course columns
3. Ensure roster data structure is correct:
   ```python
   st.session_state['rosters'] = {
       'COURSE-101': [{'StudentId': 123, 'Name': 'John'}],
       'COURSE-102': [{'StudentId': 123, 'Name': 'John'}]
   }
   ```
4. Debug: Print conflicts list before displaying

---

## 🔮 Future Enhancements

### Short-Term (1-2 months)

- [ ] **Add course prerequisites** - Check if students meet prereqs
- [ ] **Room assignment** - Track available classrooms
- [ ] **Instructor assignment** - Assign faculty to courses
- [ ] **Student login portal** - Let students view their recommended schedule
- [ ] **Export to PDF** - Generate printable class rosters
- [ ] **Undo/Redo** - Allow reverting roster changes
- [ ] **Search/Filter** - Quick student/course search across tabs

### Medium-Term (3-6 months)

- [ ] **PostgreSQL migration** - Move away from legacy MSSQL
- [ ] **API endpoint** - RESTful API for external integrations
- [ ] **Mobile responsiveness** - Better UI on tablets/phones
- [ ] **Authentication** - User login system with roles
- [ ] **Audit log** - Track who made what changes when
- [ ] **Batch operations** - Select multiple courses at once
- [ ] **Smart recommendations** - ML-based course suggestions

### Long-Term (6+ months)

- [ ] **AI chatbot** - Natural language course queries
- [ ] **Predictive analytics** - Forecast course demand
- [ ] **Integration with LMS** - Sync with Moodle/Canvas
- [ ] **Multi-university support** - Support multiple institutions
- [ ] **Advanced optimization** - Genetic algorithms for scheduling
- [ ] **Mobile app** - Native iOS/Android apps
- [ ] **Real-time collaboration** - Multiple admins working simultaneously

---

## 📞 Support & Contact

### Documentation
- This file: `WARP.md`
- Legacy Adapter: `services/legacy-adapter/README.md`
- GitHub Copilot Guidelines: `.github/copilot-instructions.md`

### Getting Help

1. **Check documentation** - Read this file and related docs
2. **Run diagnostics** - Use tools in `tests/` directory
3. **Review logs** - Check terminal output for errors
4. **Test in isolation** - Isolate the problem (DB? Logic? UI?)
5. **GitHub Issues** - Create an issue with reproduction steps

### Project Maintainer

Jeffrey Stark
- Project: Naga University Academic Scheduling Tool
- Location: `/Users/jeffreystark/Development/key/vonbot`

---

## 📄 License

Internal use only - Naga University Student Information System

---

## 🔄 Changelog

### 2024-11-26
- Moved database credentials to .env file
- Added environment variable validation
- Added .env.example template
- Updated .gitignore to exclude .env
- Added Telegram and email configuration to .env

### Earlier (Pre-WARP.md)
- Initial Streamlit application
- Student selection logic
- Course matching algorithm
- Roster management
- Schedule optimization
- Email/Telegram integration
- Legacy adapter microservice

---

**Last Updated**: November 26, 2024  
**Version**: 1.0.0  
**Status**: Active Development
