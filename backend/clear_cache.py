from sqlmodel import Session, select
from core.database import get_session
from models.leaderboard_cache import LeaderboardCache

def clear_leaderboard_cache():
    with Session(get_session()) as session:
        # Get all cache entries
        cache_entries = session.exec(select(LeaderboardCache)).all()
        print(f"Found {len(cache_entries)} cache entries")
        
        # Delete all cache entries
        for entry in cache_entries:
            session.delete(entry)
        
        session.commit()
        print("Cleared all leaderboard cache entries")

if __name__ == "__main__":
    clear_leaderboard_cache()
