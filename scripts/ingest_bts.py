"""CLI script to ingest BTS On-Time Performance CSV files into SQLite."""
import sys
import os
import glob
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    from aerops.config import DB_PATH, BTS_DATA_DIR
    from aerops.db import init_db, table_row_count
    from aerops.data.bts_loader import ingest_bts_file

    if len(sys.argv) > 1:
        # User provided specific file(s)
        patterns = sys.argv[1:]
    else:
        # Default: look in data/bts/
        patterns = [os.path.join(BTS_DATA_DIR, "*.csv")]

    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    if not files:
        logger.error(
            "No BTS CSV files found.\n"
            "Usage: python scripts/ingest_bts.py [path/to/bts_data.csv ...]\n\n"
            "Download BTS On-Time Performance data from:\n"
            "  https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoession_VQ=FGJ\n\n"
            "Place CSV files in data/bts/ or provide paths as arguments."
        )
        sys.exit(1)

    init_db(DB_PATH)
    total = 0

    for csv_file in sorted(files):
        logger.info("Processing: %s", csv_file)
        try:
            count = ingest_bts_file(csv_file, DB_PATH)
            total += count
            logger.info("  -> %d flights loaded", count)
        except Exception as e:
            logger.error("  -> Failed: %s", e)

    final_count = table_row_count(DB_PATH, "flights")
    logger.info("Done! Total flights in database: %d (added %d this run)", final_count, total)


if __name__ == "__main__":
    main()
