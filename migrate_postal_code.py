#!/usr/bin/env python3
"""
Migration script to fix postal_code field length in student_profile table
"""

import os
import sys
from sqlalchemy import text

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_postal_code():
    """Increase postal_code field from VARCHAR(20) to VARCHAR(100)"""
    
    with app.app_context():
        try:
            # Check current column length
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'student_profile' 
                AND column_name = 'postal_code'
            """))
            current_length = result.fetchone()[0]
            
            print(f"Current postal_code length: {current_length}")
            
            if current_length < 100:
                # Alter the column to increase length
                db.session.execute(text("""
                    ALTER TABLE student_profile 
                    ALTER COLUMN postal_code TYPE VARCHAR(100)
                """))
                
                db.session.commit()
                print("✅ Successfully increased postal_code field to VARCHAR(100)")
            else:
                print("✅ postal_code field already has sufficient length")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    print("🔄 Starting postal_code field migration...")
    if migrate_postal_code():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
