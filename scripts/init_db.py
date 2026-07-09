import os
import sys

# Add project root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db


def main():
    print("Initializing SQLite database...")
    try:
        init_db()
        print("✓ Database and tables initialized successfully in ./data/metrics.db")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
