#!/usr/bin/env python3
"""
Sequential scraper runner - runs all scrapers in order
"""
import subprocess
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/app/logs/scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

SCRAPERS = [
    'scraper_entramite.py',
    'scraper_completas.py',
    'scraper_jueces.py'
]

def run_scraper(script_name):
    """Run a single scraper script"""
    logger.info(f"Starting {script_name}...")
    try:
        result = subprocess.run(
            ['python', script_name],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"✓ {script_name} completed successfully")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {script_name} failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error running {script_name}: {str(e)}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("Starting scraper pipeline")
    logger.info("=" * 60)
    
    failed_scrapers = []
    
    for scraper in SCRAPERS:
        success = run_scraper(scraper)
        if not success:
            failed_scrapers.append(scraper)
    
    logger.info("=" * 60)
    if not failed_scrapers:
        logger.info("✓ All scrapers completed successfully!")
        logger.info("CSV files should be available in /app/data/")
        sys.exit(0)
    else:
        logger.error(f"✗ {len(failed_scrapers)} scraper(s) failed:")
        for scraper in failed_scrapers:
            logger.error(f"  - {scraper}")
        sys.exit(1)

if __name__ == "__main__":
    main()