"""
Migration script to update WinnerResult table schema
Makes overall_rank nullable to support division-only winners
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from core.database import engine


def migrate():
    """Drop and recreate winnerresult table with updated schema"""

    with Session(engine) as session:
        try:
            print("Dropping winnerresult table...")
            session.exec(text("DROP TABLE IF EXISTS winnerresult"))
            session.commit()
            print("[OK] Table dropped successfully")

            # Now recreate the table by importing the model and creating it
            from core.database import create_db_and_tables
            print("Recreating tables with new schema...")
            create_db_and_tables()
            print("[OK] Tables recreated successfully")

            print("\n[SUCCESS] Migration completed!")
            print("   - winnerresult table now has nullable overall_rank")
            print("   - Ready for division-based winner calculation")

        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            return False

    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
