#!/bin/bash

# Pipeline status checker
# Shows current state of all services and recent activity

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Corrupción Pipeline Status"
echo "=========================================="

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}🗄️  Database Connection:${NC}"
if docker-compose exec -T postgres pg_isready -U admin -d corrupcion_db > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database is healthy${NC}"
    
    # Get table row counts
    echo ""
    echo -e "${BLUE}📈 Database Statistics:${NC}"
    docker-compose exec -T postgres psql -U admin -d corrupcion_db -t -c "
        SELECT 
            tablename,
            n_live_tup as rows
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC;
    " 2>/dev/null || echo "Could not fetch statistics"
else
    echo -e "${RED}✗ Database is not responding${NC}"
fi

echo ""
echo -e "${BLUE}📁 Recent CSV Files:${NC}"
if [ -d "data" ] && [ "$(ls -A data 2>/dev/null)" ]; then
    ls -lht data/*.csv 2>/dev/null | head -5 || echo "No CSV files found"
else
    echo "No data directory or files found"
fi

echo ""
echo -e "${BLUE}📝 Recent Logs:${NC}"
if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    echo "Latest scraper log:"
    ls -t logs/scraper_*.log 2>/dev/null | head -1
    
    echo ""
    echo "Last 10 log entries:"
    latest_log=$(ls -t logs/scraper_*.log 2>/dev/null | head -1)
    if [ -f "$latest_log" ]; then
        tail -10 "$latest_log"
    fi
else
    echo "No logs directory or files found"
fi

echo ""
echo -e "${BLUE}⏰ Next Scheduled Run:${NC}"
if docker-compose ps scheduler | grep -q "Up"; then
    echo "Scheduler is running"
    echo "Check docker-compose.yml for schedule configuration"
    echo ""
    echo "Current schedule (from docker-compose.yml):"
    grep -A 1 "ofelia.job-run" docker-compose.yml | grep "schedule" || echo "Could not read schedule"
else
    echo -e "${YELLOW}⚠ Scheduler is not running${NC}"
fi

echo ""
echo -e "${BLUE}🔄 Recent Container Activity:${NC}"
docker-compose logs --tail=20 scraper 2>/dev/null | tail -10 || echo "No recent scraper activity"

echo ""
echo "=========================================="
echo "Status check complete"
echo "=========================================="