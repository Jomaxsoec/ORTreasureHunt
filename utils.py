import hashlib
from models import TeamAccess

def generate_device_fingerprint(user_agent, client_ip):
    """
    Generate SHA-256 hash of user-agent + IP for device fingerprinting
    """
    fingerprint_string = f"{user_agent}:{client_ip}"
    return hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()

def validate_team_and_qr(team_name, team_code, qr_id):
    """
    Validate team credentials and QR ID
    Returns dict with 'valid' boolean and 'error' message if invalid
    """
    # Check if QR ID is a valid number between 1-9
    try:
        qr_id_num = int(qr_id)
        if qr_id_num < 1 or qr_id_num > 9:
            return {
                'valid': False,
                'error': 'QR ID must be between 1 and 9'
            }
    except ValueError:
        return {
            'valid': False,
            'error': 'QR ID must be a valid number'
        }
    
    # Look up team in TeamAccess table
    team_access = TeamAccess.query.filter_by(
        team_name=team_name,
        team_code=team_code
    ).first()
    
    if not team_access:
        return {
            'valid': False,
            'error': 'Invalid team name or team code'
        }
    
    # Check if the provided QR ID matches the expected one for this team
    if team_access.qr_id != qr_id:
        return {
            'valid': False,
            'error': f'QR ID mismatch. Expected: {team_access.qr_id}, Provided: {qr_id}'
        }
    
    return {'valid': True, 'error': None}
