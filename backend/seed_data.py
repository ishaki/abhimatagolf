#!/usr/bin/env python3
"""
Seed data for the Abhimata Golf Tournament System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from core.database import engine
from models.course import Course, Hole
from models.user import User
from datetime import datetime

def create_seed_courses():
    """Create seed courses with holes data"""
    
    courses_data = [
        {
            "name": "BICC - Batam Island Country Club",
            "location": "Batam, Indonesia",
            "holes": [
                {"number": 1, "par": 4, "handicap_index": 17},
                {"number": 2, "par": 5, "handicap_index": 7},
                {"number": 3, "par": 4, "handicap_index": 5},
                {"number": 4, "par": 3, "handicap_index": 13},
                {"number": 5, "par": 4, "handicap_index": 15},
                {"number": 6, "par": 4, "handicap_index": 3},
                {"number": 7, "par": 3, "handicap_index": 9},
                {"number": 8, "par": 5, "handicap_index": 11},
                {"number": 9, "par": 4, "handicap_index": 1},
                {"number": 10, "par": 4, "handicap_index": 6},
                {"number": 11, "par": 5, "handicap_index": 14},
                {"number": 12, "par": 4, "handicap_index": 10},
                {"number": 13, "par": 3, "handicap_index": 12},
                {"number": 14, "par": 4, "handicap_index": 8},
                {"number": 15, "par": 3, "handicap_index": 18},
                {"number": 16, "par": 4, "handicap_index": 4},
                {"number": 17, "par": 5, "handicap_index": 16},
                {"number": 18, "par": 4, "handicap_index": 2}
            ]
        },
        {
            "name": "PGS - Padang Golf Sukajadi",
            "location": "Batam, Indonesia",
            "holes": [
                {"number": 1, "par": 4, "handicap_index": 14},
                {"number": 2, "par": 4, "handicap_index": 2},
                {"number": 3, "par": 5, "handicap_index": 6},
                {"number": 4, "par": 3, "handicap_index": 16},
                {"number": 5, "par": 4, "handicap_index": 8},
                {"number": 6, "par": 4, "handicap_index": 4},
                {"number": 7, "par": 4, "handicap_index": 12},
                {"number": 8, "par": 5, "handicap_index": 10},
                {"number": 9, "par": 3, "handicap_index": 18},
                {"number": 10, "par": 3, "handicap_index": 15},
                {"number": 11, "par": 4, "handicap_index": 13},
                {"number": 12, "par": 4, "handicap_index": 5},
                {"number": 13, "par": 4, "handicap_index": 9},
                {"number": 14, "par": 3, "handicap_index": 17},
                {"number": 15, "par": 5, "handicap_index": 3},
                {"number": 16, "par": 4, "handicap_index": 11},
                {"number": 17, "par": 4, "handicap_index": 1},
                {"number": 18, "par": 5, "handicap_index": 7}
            ]
        },
        {
            "name": "IP - Indah Puri Golf Batam",
            "location": "Batam, Indonesia",
            "holes": [
                {"number": 1, "par": 5, "handicap_index": 9},
                {"number": 2, "par": 4, "handicap_index": 1},
                {"number": 3, "par": 3, "handicap_index": 15},
                {"number": 4, "par": 4, "handicap_index": 7},
                {"number": 5, "par": 3, "handicap_index": 17},
                {"number": 6, "par": 4, "handicap_index": 3},
                {"number": 7, "par": 5, "handicap_index": 5},
                {"number": 8, "par": 3, "handicap_index": 13},
                {"number": 9, "par": 5, "handicap_index": 11},
                {"number": 10, "par": 4, "handicap_index": 10},
                {"number": 11, "par": 5, "handicap_index": 8},
                {"number": 12, "par": 4, "handicap_index": 16},
                {"number": 13, "par": 3, "handicap_index": 18},
                {"number": 14, "par": 5, "handicap_index": 4},
                {"number": 15, "par": 3, "handicap_index": 12},
                {"number": 16, "par": 4, "handicap_index": 2},
                {"number": 17, "par": 4, "handicap_index": 14},
                {"number": 18, "par": 4, "handicap_index": 6}
            ]
        },
        {
            "name": "BH - Batam Hills Golf Resort",
            "location": "Batam, Indonesia",
            "holes": [
                {"number": 1, "par": 4, "handicap_index": 3},
                {"number": 2, "par": 3, "handicap_index": 11},
                {"number": 3, "par": 4, "handicap_index": 13},
                {"number": 4, "par": 3, "handicap_index": 17},
                {"number": 5, "par": 5, "handicap_index": 1},
                {"number": 6, "par": 4, "handicap_index": 5},
                {"number": 7, "par": 5, "handicap_index": 9},
                {"number": 8, "par": 4, "handicap_index": 15},
                {"number": 9, "par": 4, "handicap_index": 7},
                {"number": 10, "par": 4, "handicap_index": 14},
                {"number": 11, "par": 5, "handicap_index": 4},
                {"number": 12, "par": 3, "handicap_index": 12},
                {"number": 13, "par": 4, "handicap_index": 10},
                {"number": 14, "par": 4, "handicap_index": 16},
                {"number": 15, "par": 4, "handicap_index": 2},
                {"number": 16, "par": 5, "handicap_index": 6},
                {"number": 17, "par": 3, "handicap_index": 18},
                {"number": 18, "par": 4, "handicap_index": 8}
            ]
        }
    ]
    
    with Session(engine) as session:
        # Get the first user to use as created_by (we'll use the admin user)
        admin_user = session.exec(select(User).where(User.email == "admin@abhimatagolf.com")).first()
        
        if not admin_user:
            print("Warning: No admin user found. Courses will be created without created_by reference.")
            admin_user_id = None
        else:
            admin_user_id = admin_user.id
        
        for course_data in courses_data:
            # Check if course already exists
            existing_course = session.exec(
                select(Course).where(Course.name == course_data["name"])
            ).first()
            
            if existing_course:
                print(f"Course '{course_data['name']}' already exists, skipping...")
                continue
            
            # Create course
            course = Course(
                name=course_data["name"],
                location=course_data["location"],
                total_holes=18,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(course)
            session.flush()  # Get the course ID
            
            # Create holes for this course
            for hole_data in course_data["holes"]:
                hole = Hole(
                    course_id=course.id,
                    number=hole_data["number"],
                    par=hole_data["par"],
                    handicap_index=hole_data["handicap_index"],
                    created_at=datetime.utcnow()
                )
                session.add(hole)
            
            print(f"Created course: {course_data['name']} with {len(course_data['holes'])} holes")
        
        session.commit()
        print("All seed courses created successfully!")

if __name__ == "__main__":
    create_seed_courses()
