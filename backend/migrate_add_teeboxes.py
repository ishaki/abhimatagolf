#!/usr/bin/env python3
"""
Database migration script to add teebox table and create default teeboxes for existing courses.
This script should be run after the backend models have been updated.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from core.database import engine
from sqlmodel import Session, select, text
from models.course import Course, Teebox

def create_teebox_table():
    """Create the teebox table"""
    print("Creating teebox table...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS teebox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        name VARCHAR(50) NOT NULL,
        course_rating REAL NOT NULL,
        slope_rating INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES course (id)
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("Teebox table created successfully")

def add_default_teeboxes():
    """Add default teeboxes to existing courses"""
    print("Adding default teeboxes to existing courses...")
    
    with Session(engine) as session:
        # Get all existing courses
        courses = session.exec(select(Course)).all()
        
        if not courses:
            print("No courses found to add teeboxes to")
            return
        
        print(f"Found {len(courses)} courses to process")
        
        for course in courses:
            # Check if course already has teeboxes
            existing_teeboxes = session.exec(select(Teebox).where(Teebox.course_id == course.id)).all()
            
            if existing_teeboxes:
                print(f"Course '{course.name}' already has {len(existing_teeboxes)} teeboxes, skipping")
                continue
            
            # Create default teeboxes for this course
            default_teeboxes = [
                {"name": "Blue", "course_rating": 72.0, "slope_rating": 130},
                {"name": "White", "course_rating": 70.0, "slope_rating": 125},
                {"name": "Red", "course_rating": 68.0, "slope_rating": 120},
            ]
            
            for teebox_data in default_teeboxes:
                teebox = Teebox(
                    course_id=course.id,
                    name=teebox_data["name"],
                    course_rating=teebox_data["course_rating"],
                    slope_rating=teebox_data["slope_rating"]
                )
                session.add(teebox)
            
            print(f"Added 3 default teeboxes to course '{course.name}'")
        
        session.commit()
        print("All default teeboxes added successfully")

def verify_migration():
    """Verify the migration was successful"""
    print("Verifying migration...")
    
    with Session(engine) as session:
        # Check if teebox table exists and has data
        teeboxes = session.exec(select(Teebox)).all()
        courses = session.exec(select(Course)).all()
        
        print(f"Migration verification:")
        print(f"   - Courses: {len(courses)}")
        print(f"   - Teeboxes: {len(teeboxes)}")
        
        if courses:
            avg_teeboxes_per_course = len(teeboxes) / len(courses)
            print(f"   - Average teeboxes per course: {avg_teeboxes_per_course:.1f}")
        
        # Show sample teebox data
        if teeboxes:
            print(f"   - Sample teebox: {teeboxes[0].name} (Course Rating: {teeboxes[0].course_rating}, Slope Rating: {teeboxes[0].slope_rating})")

def main():
    """Run the migration"""
    print("Starting teebox migration...")
    print("=" * 50)
    
    try:
        create_teebox_table()
        add_default_teeboxes()
        verify_migration()
        
        print("=" * 50)
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
