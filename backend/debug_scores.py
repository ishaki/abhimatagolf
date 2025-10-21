from sqlmodel import Session, select
from core.database import get_session
from models.scorecard import Scorecard

def debug_scorecard_net_scores():
    with Session(get_session()) as session:
        scorecards = session.exec(select(Scorecard)).all()
        print(f"Total scorecards: {len(scorecards)}")
        for i, sc in enumerate(scorecards):
            print(f"Scorecard {i+1}: net_score={sc.net_score} (type: {type(sc.net_score)})")

if __name__ == "__main__":
    debug_scorecard_net_scores()
