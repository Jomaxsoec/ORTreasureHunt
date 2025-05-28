"""
Script to initialize the database with sample data
Run this script to populate the database with team access data and game code pools
"""

import os
import sys
from app import app, db
from models import TeamAccess, GameCodePool
from sync_service import DataSyncService

def sync_team_access_from_external():
    """Sync TeamAccess data from external database instead of using sample data"""
    print("Syncing TeamAccess data from external database...")
    sync_service = DataSyncService()
    result = sync_service.sync_team_access_data()
    
    if result["success"]:
        print(f"✅ Synced {result['new']} new teams and updated {result['updated']} existing teams")
    else:
        print(f"❌ Sync failed: {result['error']}")
        # Fallback: no sample data, real data only
        print("No sample data will be added - waiting for external data sync")

def init_game_code_pool():
    """Initialize GameCodePool with 10 codes for each question (1-9)"""
    
    # Check if codes already exist
    existing_codes = GameCodePool.query.count()
    if existing_codes > 0:
        print(f"GameCodePool already has {existing_codes} codes. Skipping initialization.")
        return
    
    import random
    import string
    
    def generate_unique_code(question_num, code_num):
        """Generate a unique code for a question"""
        # Format: Q{question_num}-{random_string}
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"Q{question_num}-{random_part}-{code_num:02d}"
    
    for question_num in range(1, 10):  # Questions 1-9
        for code_num in range(1, 11):  # 10 codes per question
            code = generate_unique_code(question_num, code_num)
            
            game_code = GameCodePool(
                question_number=question_num,
                code=code,
                is_assigned=False
            )
            db.session.add(game_code)
        
        print(f"Added 10 codes for question {question_num}")

def main():
    """Main function to initialize all data"""
    print("Initializing Treasure Hunt Game Database...")
    
    with app.app_context():
        try:
            # Sync team access data from external database
            print("\n1. Syncing TeamAccess data from external database...")
            sync_team_access_from_external()
            
            # Initialize game code pool
            print("\n2. Initializing GameCodePool data...")
            init_game_code_pool()
            
            # Commit all changes
            db.session.commit()
            print("\n✅ Database initialization completed successfully!")
            
            # Print summary
            team_count = TeamAccess.query.count()
            code_count = GameCodePool.query.count()
            print(f"\nSummary:")
            print(f"- Teams: {team_count}")
            print(f"- Game codes: {code_count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during initialization: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
