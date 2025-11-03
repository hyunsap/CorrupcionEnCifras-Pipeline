#!/bin/bash

# Manual pipeline runner for testing or one-off runs
# This runs the entire pipeline sequentially

set -e  # Exit on error

echo "=========================================="
echo "Starting Corrupcion Data Pipeline"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if database is up
echo -e "${YELLOW}Checking database connection...${NC}"
until docker-compose exec -T postgres pg_isready -U admin -d corrupcion_db > /dev/null 2>&1; do
  echo "Waiting for database..."
  sleep 2
done
echo -e "${GREEN}✓ Database is ready${NC}"

# Step 1: Run scrapers
echo ""
echo "=========================================="
echo "Step 1: Running scrapers"
echo "=========================================="
docker-compose run --rm scraper
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Scrapers completed successfully${NC}"
else
    echo -e "${RED}✗ Scrapers failed${NC}"
    exit 1
fi

# Step 2: Run ETL
echo ""
echo "=========================================="
echo "Step 2: Running ETL"
echo "=========================================="
docker-compose run --rm etl
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ETL completed successfully${NC}"
else
    echo -e "${RED}✗ ETL failed${NC}"
    exit 1
fi

# Step 3: Load data
echo ""
echo "=========================================="
echo "Step 3: Loading data into database"
echo "=========================================="
docker-compose run --rm loader
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Data loaded successfully${NC}"
else
    echo -e "${RED}✗ Data loading failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Pipeline completed successfully!${NC}"
echo "=========================================="

# Show some stats
echo ""
echo "Database stats:"
docker-compose exec -T postgres psql -U admin -d corrupcion_db -c "
SELECT 
    schemaname,
    relname as tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"