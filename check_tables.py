"""
Simple script to check external database table structure
"""
from sqlalchemy import create_engine, text

EXTERNAL_DB_URL = "postgresql://neondb_owner:npg_H3kow5svXVZE@ep-steep-sea-a5qeiihm.us-east-2.aws.neon.tech/neondb?sslmode=require"

def check_table_structure():
    engine = create_engine(EXTERNAL_DB_URL)
    
    with engine.connect() as conn:
        print('=== USER TABLE STRUCTURE ===')
        try:
            user_columns = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user'
                ORDER BY ordinal_position
            """)).fetchall()
            
            if user_columns:
                for col in user_columns:
                    print(f'{col[0]} ({col[1]})')
            else:
                print("No columns found or table doesn't exist")
        except Exception as e:
            print(f"Error checking user table: {e}")
        
        print('\n=== QR_SCAN TABLE STRUCTURE ===')
        try:
            qr_columns = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'qr_scan'
                ORDER BY ordinal_position
            """)).fetchall()
            
            if qr_columns:
                for col in qr_columns:
                    print(f'{col[0]} ({col[1]})')
            else:
                print("No columns found or table doesn't exist")
        except Exception as e:
            print(f"Error checking qr_scan table: {e}")
        
        print('\n=== ALL TABLES ===')
        try:
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
            
            for table in tables:
                print(table[0])
        except Exception as e:
            print(f"Error listing tables: {e}")

if __name__ == "__main__":
    check_table_structure()