from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.orm import Session


class TeamAccess(db.Model):
    """Table to store team credentials and their expected QR IDs"""
    __tablename__ = 'team_access'

    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    team_code = db.Column(db.String(50), nullable=False)
    qr_id = db.Column(db.Integer, nullable=False)

    # Ensure unique combination of team_name and team_code
    __table_args__ = (UniqueConstraint('team_name',
                                       'team_code',
                                       name='_team_name_code_uc'), )

    def __repr__(self):
        return f'<TeamAccess {self.team_name}:{self.team_code}>'


class GameCodePool(db.Model):
    """Table to store available codes for each question/QR ID"""
    __tablename__ = 'game_code_pool'

    id = db.Column(db.Integer, primary_key=True)
    question_number = db.Column(
        db.Integer, nullable=False)  # 1 to 9, corresponding to QR ID
    code = db.Column(db.String(100), nullable=False, unique=True)
    is_assigned = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<GameCodePool Q{self.question_number}:{self.code}>'


class AssignedCodes(db.Model):
    """Table to track code assignments to teams"""
    __tablename__ = 'assigned_codes'

    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    assigned_code = db.Column(db.String(100), nullable=False)
    device_fingerprint = db.Column(db.String(64),
                                   nullable=False)  # SHA-256 hash
    assigned_at = db.Column(db.DateTime,
                            default=datetime.utcnow,
                            nullable=False)

    # Ensure one code per team per question
    __table_args__ = (UniqueConstraint('team_name',
                                       'question_number',
                                       name='_team_question_uc'), )

    def __repr__(self):
        return f'<AssignedCodes {self.team_name}:Q{self.question_number}:{self.assigned_code}>'


# External tables from Project A (read-only, bound to external database)
class User(db.Model):
    """User table from Project A (external database)"""
    __tablename__ = 'user'
    __bind_key__ = 'external'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Add other columns as needed

    def __repr__(self):
        return f'<User {self.name}>'


class QRScan(db.Model):
    """QRScan table from Project A (external database)"""
    __tablename__ = 'qr_scan'
    __bind_key__ = 'external'

    id = db.Column(db.Integer, primary_key=True)
    otp = db.Column(db.String(50), nullable=False)
    qr_id = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)

    # Add other columns as needed

    def __repr__(self):
        return f'<QRScan {self.otp}:{self.qr_id}>'
