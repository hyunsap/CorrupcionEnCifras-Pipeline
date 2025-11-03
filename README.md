# Corrupción Data Pipeline

Automated data scraping, ETL, and loading pipeline for corruption case data.

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 2GB of free disk space
- Internet connection for scraping

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd corrupcion-pipeline

# Create required directories
mkdir -p data logs initdb

# Copy your init.sql to initdb/
cp /path/to/your/init.sql initdb/

# Create environment file (optional)
cp .env.example .env
```

### 2. Start the Services

```bash
# Start database and scheduler
docker-compose up -d postgres scheduler

# Wait for database to be ready (about 10 seconds)
docker-compose logs -f postgres
# Press Ctrl+C when you see "database system is ready to accept connections"
```

### 3. Run Pipeline Manually (First Time)

```bash
# Make the script executable
chmod +x run_pipeline.sh

# Run the entire pipeline
./run_pipeline.sh
```

Or run each step individually:

```bash
# Step 1: Run scrapers
docker-compose run --rm scraper

# Step 2: Run ETL
docker-compose run --rm etl

# Step 3: Load data
docker-compose run --rm loader
```

## 📅 Automated Weekly Runs

The pipeline runs automatically every **Sunday at 2:00 AM** via the scheduler service.

The schedule:
- **2:00 AM** - Scrapers run (generates CSVs)
- **4:00 AM** - ETL processes the CSVs (2 hours after scrapers)
- **4:15 AM** - Loader inserts data into database

To modify the schedule, edit the `ofelia.job-run.*.schedule` labels in `docker-compose.yml`.

### Cron Schedule Format
```
0 0 2 * * 0  = Every Sunday at 2:00 AM
│ │ │ │ │ │
│ │ │ │ │ └─── Day of week (0-6, 0=Sunday)
│ │ │ │ └───── Month (1-12)
│ │ │ └─────── Day of month (1-31)
│ │ └───────── Hour (0-23)
│ └─────────── Minute (0-59)
└───────────── Second (0-59)
```

## 📊 Monitoring

### Check Scheduler Status
```bash
docker-compose logs -f scheduler
```

### Check Last Run Logs
```bash
# Scraper logs
ls -lht logs/scraper_*.log | head -1

# ETL logs
docker-compose logs etl

# Loader logs
docker-compose logs loader
```

### View Generated CSVs
```bash
ls -lh data/
```

### Query Database
```bash
# Connect to database
docker-compose exec postgres psql -U admin -d corrupcion_db

# Check row counts
SELECT tablename, n_live_tup 
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;
```

## 🛠️ Management Commands

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove All Data
```bash
docker-compose down -v
# WARNING: This deletes the database!
```

### Restart a Specific Service
```bash
docker-compose restart scheduler
```

### View All Logs
```bash
docker-compose logs -f
```

### Rebuild After Code Changes
```bash
docker-compose build scraper etl loader
```

## 📁 Project Structure

```
.
├── docker-compose.yml          # Main orchestration file
├── Dockerfile.scraper          # Scraper container
├── Dockerfile.etl              # ETL container (same for loader)
├── run_scrapers.py             # Sequential scraper runner
├── run_pipeline.sh             # Manual pipeline runner
├── requirements.txt            # Python dependencies
├── scraper_entramite.py       # Scraper script 1
├── scraper_completas.py        # Scraper script 2
├── scraper_jueces.py          # Scraper script 3
├── transform_expedientes.py          # ETL processor
├── cargar_etl.py               # Database loader
├── data/                       # Generated CSVs (gitignored)
├── logs/                       # Application logs (gitignored)
└── initdb/
    └── init.sql                # Database initialization
```

## 🔧 Configuration

### Database Connection

Set via environment variables in `docker-compose.yml`:
- `DB_HOST=postgres`
- `DB_PORT=5432`
- `DB_NAME=corrupcion_db`
- `DB_USER=admin`
- `DB_PASSWORD=td8corrupcion`

### Changing Schedule

Edit `docker-compose.yml` scheduler labels:
```yaml
labels:
  # Run every day at 3 AM instead
  ofelia.job-run.scraper.schedule: "0 0 3 * * *"
```

## 🐛 Troubleshooting

### Database won't start
```bash
# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Scraper fails
```bash
# Check logs
docker-compose logs scraper
cat logs/scraper_*.log | tail -50

# Run in interactive mode for debugging
docker-compose run --rm scraper /bin/bash
```

### ETL fails
```bash
# Check if CSVs exist
ls -lh data/

# Check ETL logs
docker-compose logs etl
```

### Scheduler not running
```bash
# Check scheduler logs
docker-compose logs scheduler

# Restart scheduler
docker-compose restart scheduler
```

## 🔒 Security Notes

- **Change default passwords** in production!
- Don't commit `.env` files with credentials
- Restrict database port (5432) in production
- Consider using Docker secrets for sensitive data

## 🤝 For Other Users

To run this pipeline:

1. Install Docker and Docker Compose
2. Clone this repository
3. Place `init.sql` in `initdb/` folder
4. Run `docker-compose up -d`
5. Run `./run_pipeline.sh` for first-time setup
6. Pipeline will run automatically every Sunday

That's it! No Python environment setup, no dependency issues.