"""
Test script to verify external database connection and automatic TeamAccess population
"""

import os
from app import app, db
from models import TeamAccess, User, QRScan, GameCodePool

def test_database_connection():
    """Test connection to the external database"""
    print("Testing database connection...")
    
    with app.app_context():
        try:
            # Test basic connection
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            print("✅ Database connection successful!")
            
            # Check if tables exist
            tables_to_check = ['users', 'qr_scans', 'team_access', 'game_code_pool']
            for table in tables_to_check:
                try:
                    result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    print(f"✅ Table '{table}' exists with {result[0]} records")
                except Exception as e:
                    print(f"⚠️  Table '{table}' check failed: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False

def test_existing_data():
    """Check existing data in the tables"""
    print("\nChecking existing data...")
    
    with app.app_context():
        try:
            # Check Users
            users = User.query.limit(5).all()
            print(f"Found {len(users)} users (showing first 5):")
            for user in users:
                print(f"  - User {user.id}: {user.name}")
            
            # Check QRScans
            qr_scans = QRScan.query.limit(5).all()
            print(f"\nFound {len(qr_scans)} QR scans (showing first 5):")
            for scan in qr_scans:
                print(f"  - QR Scan {scan.id}: OTP={scan.otp}, QR_ID={scan.qr_id}, User_ID={scan.user_id}")
            
            # Check TeamAccess
            team_access = TeamAccess.query.limit(10).all()
            print(f"\nFound {len(team_access)} TeamAccess entries:")
            for team in team_access:
                print(f"  - Team {team.id}: {team.team_name} | Code: {team.team_code} | QR: {team.qr_id}")
                
        except Exception as e:
            print(f"❌ Error checking existing data: {str(e)}")

def create_sample_qr_scan():
    """Create a sample QR scan to test the automatic population"""
    print("\nTesting automatic TeamAccess population...")
    
    with app.app_context():
        try:
            # Create a test user first
            test_user = User(name="Test Team Alpha")
            db.session.add(test_user)
            db.session.flush()  # Get the ID without committing
            
            # Create a QR scan - this should trigger the TeamAccess population
            test_qr_scan = QRScan(
                otp="TEST001",
                qr_id="5",
                user_id=test_user.id
            )
            db.session.add(test_qr_scan)
            db.session.commit()
            
            print(f"✅ Created test QR scan: OTP=TEST001, QR_ID=5, User={test_user.name}")
            
            # Check if TeamAccess was automatically populated
            team_access = TeamAccess.query.filter_by(team_code="TEST001", qr_id="5").first()
            if team_access:
                print(f"✅ TeamAccess automatically created: {team_access.team_name} | {team_access.team_code} | {team_access.qr_id}")
                return True
            else:
                print("❌ TeamAccess was not automatically created")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test data: {str(e)}")
            db.session.rollback()
            return False

def initialize_game_codes():
    """Initialize GameCodePool if empty"""
    print("\nInitializing game codes...")
    
    with app.app_context():
        try:
            existing_codes = GameCodePool.query.count()
            if existing_codes > 0:
                print(f"✅ GameCodePool already has {existing_codes} codes")
                return
            
            import random
            import string
            
            def generate_unique_code(question_num, code_num):
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
            
            db.session.commit()
            print("✅ GameCodePool initialization completed!")
            
        except Exception as e:
            print(f"❌ Error initializing game codes: {str(e)}")
            db.session.rollback()

def main():
    """Main test function"""
    print("🔍 External Database Integration Test")
    print("=" * 50)
    
    # Test connection
    if not test_database_connection():
        return
    
    # Check existing data
    test_existing_data()
    
    # Initialize game codes if needed
    initialize_game_codes()
    
    # Test automatic population
    create_sample_qr_scan()
    
    print("\n" + "=" * 50)
    print("🎉 External database integration test completed!")

if __name__ == "__main__":
    main()