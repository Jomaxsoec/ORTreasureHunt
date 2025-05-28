"""
Service to sync data from external project's database to local TeamAccess table
"""

import logging
from app import app, db
from models import TeamAccess, User, QRScan
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# External database connection
EXTERNAL_DB_URL = "postgresql://neondb_owner:npg_H3kow5svXVZE@ep-steep-sea-a5qeiihm.us-east-2.aws.neon.tech/neondb?sslmode=require"


class DataSyncService:

    def __init__(self):
        self.external_engine = create_engine(EXTERNAL_DB_URL)
        self.external_session_factory = sessionmaker(bind=self.external_engine)

    def sync_team_access_data(self):
        print("🔄 Starting TeamAccess data sync...")

        with app.app_context():
            external_session = self.external_session_factory()
            try:
                # Fetch data from external database
                external_data = external_session.execute(
                    text("""
                    SELECT 
                        u.name as user_name,
                        q.otp as team_code,
                        q.qr_id as qr_id,
                        q.user_id
                    FROM qr_scan q
                    LEFT JOIN "user" u ON q.user_id = u.id
                    ORDER BY q.id
                """)).fetchall()

                synced_count = 0
                updated_count = 0

                for row in external_data:
                    user_name = row.user_name or f"Team-{row.team_code}"
                    team_code = row.team_code
                    qr_id = row.qr_id
                    qr_id = qr_id.replace('qr_',
                                          '')  # Remove the 'qr_id' prefix

                    # Check if TeamAccess entry exists
                    existing_team = TeamAccess.query.filter_by(
                        team_code=team_code, qr_id=qr_id).first()

                    if existing_team:
                        # Update existing entry if name changed
                        if existing_team.team_name != user_name:
                            existing_team.team_name = user_name
                            updated_count += 1
                            print(
                                f"  ✏️  Updated: {user_name} | {team_code} | QR:{qr_id}"
                            )
                    else:
                        # Create new TeamAccess entry
                        new_team = TeamAccess()
                        new_team.team_name = user_name
                        new_team.team_code = team_code
                        new_team.qr_id = qr_id
                        db.session.add(new_team)
                        synced_count += 1
                        print(
                            f"  ➕ Added: {user_name} | {team_code} | QR:{qr_id}"
                        )

                # Commit all changes
                db.session.commit()

                print(f"✅ Sync completed!")
                print(f"  📊 New entries: {synced_count}")
                print(f"  📊 Updated entries: {updated_count}")

                return {
                    "success": True,
                    "new": synced_count,
                    "updated": updated_count
                }

            except Exception as e:
                db.session.rollback()
                print(f"❌ Sync failed: {str(e)}")
                return {"success": False, "error": str(e)}
            finally:
                external_session.close()

    def get_external_data_summary(self):
        """Get summary of data in external database"""
        external_session = self.external_session_factory()
        try:
            users_count = external_session.execute(
                text('SELECT COUNT(*) FROM "user"')).scalar()
            qr_scans_count = external_session.execute(
                text("SELECT COUNT(*) FROM qr_scan")).scalar()
            return {"users": users_count, "qr_scans": qr_scans_count}
        except Exception as e:
            print(f"Error getting external data summary: {str(e)}")
            return {"users": 0, "qr_scans": 0}
        finally:
            external_session.close()


def manual_sync():
    """Manual sync function for testing"""
    sync_service = DataSyncService()

    print("🔍 External Database Summary:")
    summary = sync_service.get_external_data_summary()
    print(f"  📊 Users: {summary['users']}")
    print(f"  📊 QR Scans: {summary['qr_scans']}")
    print()

    # Perform sync
    result = sync_service.sync_team_access_data()

    if result["success"]:
        print(f"\n🎉 TeamAccess sync successful!")
        with app.app_context():
            local_count = TeamAccess.query.count()
            print(f"  📊 Total TeamAccess entries: {local_count}")
    else:
        print(f"\n❌ Sync failed: {result['error']}")


if __name__ == "__main__":
    manual_sync()
