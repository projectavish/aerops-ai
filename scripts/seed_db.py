"""Initialize the database with reference data and demo flights."""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    from aerops.config import DB_PATH, IATA_CODES_JSON
    from aerops.db import init_db, get_connection, table_row_count
    from aerops.data.iata_codes import load_iata_codes
    from aerops.data.airports import load_airports_to_db
    from aerops.data.demo_generator import generate_demo_data

    logger.info("Initializing database at %s", DB_PATH)
    init_db(DB_PATH)

    # Load IATA delay codes
    logger.info("Loading IATA delay codes ...")
    codes = load_iata_codes(IATA_CODES_JSON)
    if codes:
        conn = get_connection(DB_PATH)
        conn.execute("DELETE FROM iata_delay_codes")
        for c in codes:
            conn.execute(
                "INSERT OR REPLACE INTO iata_delay_codes "
                "(code, category, subcategory, description, responsibility) "
                "VALUES (?, ?, ?, ?, ?)",
                (c["code"], c["category"], c.get("subcategory", ""),
                 c["description"], c.get("responsibility", "")),
            )
        conn.commit()
        conn.close()
        logger.info("Loaded %d IATA delay codes", len(codes))

    # Load airports
    logger.info("Loading airport reference data ...")
    try:
        airport_count = load_airports_to_db()
        logger.info("Loaded %d airports", airport_count)
    except Exception as e:
        logger.warning("Airport loading failed (will retry on next run): %s", e)

    # Check if flights exist, if not generate demo data
    try:
        flight_count = table_row_count(DB_PATH, "flights")
    except Exception:
        flight_count = 0

    if flight_count == 0:
        logger.info("No flight data found. Generating demo data ...")
        count = generate_demo_data(DB_PATH)
        logger.info("Generated %d demo flights", count)
    else:
        logger.info("Database already has %d flights", flight_count)

    logger.info("Database seeded successfully!")


if __name__ == "__main__":
    main()
