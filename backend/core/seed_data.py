from sqlmodel import Session, select
from core.database import engine
from core.security import get_password_hash
from models.user import User, UserRole
from models.course import Course, Hole


def create_seed_data():
    """Create seed data for development and testing"""
    
    with Session(engine) as session:
        # Check if users already exist
        user_statement = select(User)
        existing_users = session.exec(user_statement).first()
        
        if not existing_users:
            # Create default users
            users = [
                User(
                    full_name="Super Admin",
                    email="admin@abhimatagolf.com",
                    hashed_password=get_password_hash("admin123"),
                    role=UserRole.SUPER_ADMIN,
                    is_active=True
                ),
                User(
                    full_name="Event Admin",
                    email="eventadmin@abhimatagolf.com",
                    hashed_password=get_password_hash("event123"),
                    role=UserRole.EVENT_ADMIN,
                    is_active=True
                ),
                User(
                    full_name="Event User",
                    email="eventuser@abhimatagolf.com",
                    hashed_password=get_password_hash("user123"),
                    role=UserRole.EVENT_USER,
                    is_active=True
                )
            ]
            
            for user in users:
                session.add(user)
            
            session.commit()
            print("Created default users")
        
        # Check if courses already exist
        course_statement = select(Course)
        existing_courses = session.exec(course_statement).first()
        
        if not existing_courses:
            # Create sample course
            course = Course(
                name="Abhimata Golf Course",
                location="Jakarta, Indonesia",
                total_holes=18
            )
            session.add(course)
            session.commit()
            session.refresh(course)
            
            # Create holes for the course
            holes_data = [
                {"number": 1, "par": 4, "handicap_index": 5, "distance_meters": 350},
                {"number": 2, "par": 3, "handicap_index": 15, "distance_meters": 150},
                {"number": 3, "par": 5, "handicap_index": 1, "distance_meters": 520},
                {"number": 4, "par": 4, "handicap_index": 7, "distance_meters": 380},
                {"number": 5, "par": 3, "handicap_index": 17, "distance_meters": 140},
                {"number": 6, "par": 4, "handicap_index": 3, "distance_meters": 420},
                {"number": 7, "par": 5, "handicap_index": 9, "distance_meters": 480},
                {"number": 8, "par": 3, "handicap_index": 13, "distance_meters": 160},
                {"number": 9, "par": 4, "handicap_index": 11, "distance_meters": 360},
                {"number": 10, "par": 4, "handicap_index": 8, "distance_meters": 390},
                {"number": 11, "par": 3, "handicap_index": 16, "distance_meters": 145},
                {"number": 12, "par": 5, "handicap_index": 2, "distance_meters": 510},
                {"number": 13, "par": 4, "handicap_index": 6, "distance_meters": 370},
                {"number": 14, "par": 3, "handicap_index": 14, "distance_meters": 155},
                {"number": 15, "par": 4, "handicap_index": 4, "distance_meters": 410},
                {"number": 16, "par": 5, "handicap_index": 10, "distance_meters": 490},
                {"number": 17, "par": 3, "handicap_index": 18, "distance_meters": 135},
                {"number": 18, "par": 4, "handicap_index": 12, "distance_meters": 340}
            ]
            
            for hole_data in holes_data:
                hole = Hole(
                    course_id=course.id,
                    number=hole_data["number"],
                    par=hole_data["par"],
                    handicap_index=hole_data["handicap_index"],
                    distance_meters=hole_data["distance_meters"]
                )
                session.add(hole)
            
            session.commit()
            print("Created sample course with holes")


if __name__ == "__main__":
    create_seed_data()
