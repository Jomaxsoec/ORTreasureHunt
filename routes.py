from flask import render_template, request, jsonify, session
from app import app, db
from models import TeamAccess, GameCodePool, AssignedCodes
from utils import generate_device_fingerprint, validate_team_and_qr
from sync_service import DataSyncService
import logging

@app.route('/')
def index():
    """Main page for teams to submit their credentials"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin page to view all assigned codes"""
    return render_template('admin.html')

@app.route('/verify', methods=['POST'])
def verify_team():
    """
    POST endpoint to verify team credentials and assign a code
    Expected JSON: {"team_name": "...", "team_code": "...", "qr_id": "..."}
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'error': 'No JSON data provided'
            }), 400
        
        team_name = data.get('team_name', '').strip()
        team_code = data.get('team_code', '').strip()
        qr_id = data.get('qr_id', '').strip()
        
        # Validate input
        if not all([team_name, team_code, qr_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: team_name, team_code, qr_id'
            }), 400
        
        # Generate device fingerprint
        user_agent = request.headers.get('User-Agent', '')
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        device_fingerprint = generate_device_fingerprint(user_agent, client_ip)
        
        # Validate team and QR ID
        validation_result = validate_team_and_qr(team_name, team_code, qr_id)
        
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['error']
            }), 400
        
        question_number = int(qr_id)
        
        # Check if team already has a code for this question
        existing_assignment = AssignedCodes.query.filter_by(
            team_name=team_name,
            question_number=question_number
        ).first()
        
        if existing_assignment:
            return jsonify({
                'success': False,
                'error': f'Team {team_name} already has a code assigned for question {question_number}'
            }), 400
        
        # Check if this device already submitted for this question
        device_assignment = AssignedCodes.query.filter_by(
            device_fingerprint=device_fingerprint,
            question_number=question_number
        ).first()
        
        if device_assignment:
            return jsonify({
                'success': False,
                'error': 'This device has already submitted for this question'
            }), 400
        
        # Get an available code from the pool
        available_code = GameCodePool.query.filter_by(
            question_number=question_number,
            is_assigned=False
        ).first()
        
        if not available_code:
            return jsonify({
                'success': False,
                'error': f'No more codes available for question {question_number}'
            }), 400
        
        # Mark code as assigned
        available_code.is_assigned = True
        
        # Create assignment record
        assignment = AssignedCodes(
            team_name=team_name,
            question_number=question_number,
            assigned_code=available_code.code,
            device_fingerprint=device_fingerprint
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        app.logger.info(f'Code {available_code.code} assigned to team {team_name} for question {question_number}')
        
        return jsonify({
            'success': True,
            'assigned_code': available_code.code,
            'question_number': question_number,
            'team_name': team_name
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error in verify_team: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/codes', methods=['GET'])
def get_assigned_codes():
    """
    GET endpoint to retrieve all assigned codes (for admin/testing)
    """
    try:
        assignments = AssignedCodes.query.order_by(AssignedCodes.assigned_at.desc()).all()
        
        codes_data = []
        for assignment in assignments:
            codes_data.append({
                'id': assignment.id,
                'team_name': assignment.team_name,
                'question_number': assignment.question_number,
                'assigned_code': assignment.assigned_code,
                'assigned_at': assignment.assigned_at.isoformat(),
                'device_fingerprint': assignment.device_fingerprint[:8] + '...'  # Partial for privacy
            })
        
        return jsonify({
            'success': True,
            'assigned_codes': codes_data,
            'total_count': len(codes_data)
        })
        
    except Exception as e:
        app.logger.error(f'Error in get_assigned_codes: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    GET endpoint to retrieve game statistics
    """
    try:
        # Get total assignments per question
        stats = {}
        for question_num in range(1, 10):
            assigned_count = AssignedCodes.query.filter_by(question_number=question_num).count()
            available_count = GameCodePool.query.filter_by(
                question_number=question_num,
                is_assigned=False
            ).count()
            
            stats[f'question_{question_num}'] = {
                'assigned': assigned_count,
                'available': available_count,
                'total': assigned_count + available_count
            }
        
        # Get unique teams that have participated
        unique_teams = db.session.query(AssignedCodes.team_name).distinct().count()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'unique_teams': unique_teams
        })
        
    except Exception as e:
        app.logger.error(f'Error in get_stats: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/sync', methods=['POST'])
def sync_external_data():
    """
    POST endpoint to manually sync data from external database
    """
    try:
        sync_service = DataSyncService()
        result = sync_service.sync_team_access_data()
        
        if result["success"]:
            return jsonify({
                'success': True,
                'message': f'Sync completed! Added {result["new"]} new teams, updated {result["updated"]} teams.',
                'new_teams': result["new"],
                'updated_teams': result["updated"]
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Sync failed: {result["error"]}'
            }), 500
            
    except Exception as e:
        app.logger.error(f'Error in sync_external_data: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error during sync'
        }), 500

@app.route('/generate_qr')
def generate_qr_code():
    """Generate and display QR code for the home page"""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        # Get the current request URL to build the home page URL
        home_url = request.url_root
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(home_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Treasure Hunt QR Code</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 text-center">
                        <h2>Treasure Hunt QR Code</h2>
                        <p class="text-muted">Share this QR code with participants</p>
                        <div class="card">
                            <div class="card-body">
                                <img src="data:image/png;base64,{img_base64}" class="img-fluid" alt="QR Code">
                                <p class="mt-3"><strong>URL:</strong> {home_url}</p>
                                <small class="text-muted">Scanning this QR code will take users to the treasure hunt home page</small>
                            </div>
                        </div>
                        <div class="mt-3">
                            <a href="/admin" class="btn btn-secondary">Back to Admin</a>
                            <a href="/" class="btn btn-primary">Home Page</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'QR code library not installed. Please install qrcode[pil]'
        }), 500
    except Exception as e:
        app.logger.error(f'Error generating QR code: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Failed to generate QR code'
        }), 500

@app.route('/reset', methods=['POST'])
def reset_game_data():
    """
    POST endpoint for admin to reset game data (clear team_access and assigned_codes)
    """
    try:
        # Clear assigned codes first (due to potential foreign key constraints)
        assigned_count = AssignedCodes.query.count()
        AssignedCodes.query.delete()
        
        # Clear team access
        team_count = TeamAccess.query.count()
        TeamAccess.query.delete()
        
        # Reset game code pool (mark all codes as unassigned)
        GameCodePool.query.update({'is_assigned': False})
        
        db.session.commit()
        
        app.logger.info(f'Admin reset: Cleared {team_count} teams and {assigned_count} assignments')
        
        return jsonify({
            'success': True,
            'message': f'Game data reset successfully! Cleared {team_count} teams and {assigned_count} code assignments.',
            'cleared_teams': team_count,
            'cleared_assignments': assigned_count
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error in reset_game_data: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Internal server error during reset'
        }), 500
