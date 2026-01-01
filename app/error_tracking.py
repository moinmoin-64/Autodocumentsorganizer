"""
Error Tracking Backend - Sentry-compatible error collection
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from functools import wraps

from app.database import db
from app.auth import require_auth

logger = logging.getLogger(__name__)
error_bp = Blueprint('errors', __name__, url_prefix='/api/errors')


class ErrorLog(db.Model):
    """Error log model"""
    __tablename__ = 'error_logs'

    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255))
    lineno = db.Column(db.Integer)
    colno = db.Column(db.Integer)
    stack = db.Column(db.Text)
    url = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    user_id = db.Column(db.String(100))
    environment = db.Column(db.String(50), default='production')
    release = db.Column(db.String(50))
    is_offline = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(db.Text)

    __table_args__ = (
        db.Index('idx_error_timestamp', 'timestamp'),
        db.Index('idx_error_type', 'error_type'),
        db.Index('idx_error_user', 'user_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.error_type,
            'message': self.message,
            'filename': self.filename,
            'lineno': self.lineno,
            'colno': self.colno,
            'stack': self.stack,
            'url': self.url,
            'userAgent': self.user_agent,
            'userId': self.user_id,
            'environment': self.environment,
            'release': self.release,
            'offline': self.is_offline,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolutionNotes': self.resolution_notes
        }


class ErrorGroup(db.Model):
    """Group similar errors together"""
    __tablename__ = 'error_groups'

    id = db.Column(db.Integer, primary_key=True)
    error_message = db.Column(db.String(500), nullable=False, unique=True)
    count = db.Column(db.Integer, default=1)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('idx_group_resolved', 'resolved'),
        db.Index('idx_group_last_seen', 'last_seen'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.error_message,
            'count': self.count,
            'lastSeen': self.last_seen.isoformat(),
            'firstSeen': self.first_seen.isoformat(),
            'resolved': self.resolved
        }


@error_bp.route('', methods=['POST'])
def collect_errors():
    """
    Collect errors from frontend
    POST /api/errors
    """
    try:
        data = request.get_json()
        if not data or 'errors' not in data:
            return jsonify({'error': 'No errors provided'}), 400

        errors = data.get('errors', [])
        inserted_count = 0

        for error_data in errors:
            try:
                # Create error log
                error_log = ErrorLog(
                    error_type=error_data.get('type', 'error'),
                    message=error_data.get('message', ''),
                    filename=error_data.get('filename'),
                    lineno=error_data.get('lineno'),
                    colno=error_data.get('colno'),
                    stack=error_data.get('stack'),
                    url=error_data.get('url'),
                    user_agent=error_data.get('userAgent'),
                    user_id=error_data.get('context', {}).get('userId'),
                    environment=error_data.get('context', {}).get('environment', 'production'),
                    release=error_data.get('context', {}).get('release'),
                    is_offline=error_data.get('context', {}).get('offline', False)
                )
                db.session.add(error_log)

                # Update or create error group
                message = error_data.get('message', '')
                group = ErrorGroup.query.filter_by(error_message=message).first()

                if group:
                    group.count += 1
                    group.last_seen = datetime.utcnow()
                else:
                    group = ErrorGroup(
                        error_message=message,
                        count=1
                    )
                    db.session.add(group)

                inserted_count += 1

            except Exception as e:
                logger.error(f"Failed to process error: {str(e)}")
                continue

        db.session.commit()

        logger.info(f"Collected {inserted_count} errors from frontend")

        return jsonify({
            'success': True,
            'inserted': inserted_count,
            'total': len(errors)
        }), 201

    except Exception as e:
        logger.error(f"Error collection endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@error_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_error_dashboard():
    """
    Get error statistics for dashboard
    GET /api/errors/dashboard
    """
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        # Total errors
        total_errors = ErrorLog.query.filter(
            ErrorLog.timestamp >= since
        ).count()

        # Errors by type
        errors_by_type = db.session.query(
            ErrorLog.error_type,
            db.func.count(ErrorLog.id)
        ).filter(
            ErrorLog.timestamp >= since
        ).group_by(ErrorLog.error_type).all()

        # Top error messages
        top_errors = db.session.query(
            ErrorGroup.error_message,
            ErrorGroup.count,
            ErrorGroup.last_seen
        ).filter(
            ErrorGroup.last_seen >= since
        ).order_by(ErrorGroup.count.desc()).limit(10).all()

        # Errors by environment
        errors_by_env = db.session.query(
            ErrorLog.environment,
            db.func.count(ErrorLog.id)
        ).filter(
            ErrorLog.timestamp >= since
        ).group_by(ErrorLog.environment).all()

        # Offline vs online
        offline_count = ErrorLog.query.filter(
            ErrorLog.is_offline == True,
            ErrorLog.timestamp >= since
        ).count()

        # Errors by hour (last 24h)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        errors_by_hour = db.session.query(
            db.func.date_format(ErrorLog.timestamp, '%Y-%m-%d %H:00:00').label('hour'),
            db.func.count(ErrorLog.id)
        ).filter(
            ErrorLog.timestamp >= last_24h
        ).group_by('hour').order_by('hour').all()

        return jsonify({
            'period': f'{days} days',
            'total': total_errors,
            'byType': dict(errors_by_type),
            'topErrors': [
                {
                    'message': msg,
                    'count': count,
                    'lastSeen': last_seen.isoformat()
                }
                for msg, count, last_seen in top_errors
            ],
            'byEnvironment': dict(errors_by_env),
            'offline': offline_count,
            'online': total_errors - offline_count,
            'byHour': [
                {
                    'hour': hour,
                    'count': count
                }
                for hour, count in errors_by_hour
            ]
        }), 200

    except Exception as e:
        logger.error(f"Dashboard endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@error_bp.route('/groups', methods=['GET'])
@require_auth
def get_error_groups():
    """
    Get grouped errors
    GET /api/errors/groups?resolved=false&limit=20
    """
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        query = ErrorGroup.query.filter_by(resolved=resolved)
        query = query.order_by(ErrorGroup.last_seen.desc())

        total = query.count()
        groups = query.limit(limit).offset(offset).all()

        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'groups': [g.to_dict() for g in groups]
        }), 200

    except Exception as e:
        logger.error(f"Groups endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@error_bp.route('/groups/<int:group_id>', methods=['GET'])
@require_auth
def get_error_group_details(group_id):
    """
    Get details for a specific error group
    GET /api/errors/groups/<id>
    """
    try:
        group = ErrorGroup.query.get_or_404(group_id)
        errors = ErrorLog.query.filter_by(
            message=group.error_message
        ).order_by(ErrorLog.timestamp.desc()).limit(50).all()

        return jsonify({
            'group': group.to_dict(),
            'errors': [e.to_dict() for e in errors]
        }), 200

    except Exception as e:
        logger.error(f"Group details endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@error_bp.route('/groups/<int:group_id>/resolve', methods=['PUT'])
@require_auth
def resolve_error_group(group_id):
    """
    Mark error group as resolved
    PUT /api/errors/groups/<id>/resolve
    """
    try:
        data = request.get_json() or {}
        group = ErrorGroup.query.get_or_404(group_id)

        group.resolved = True
        db.session.commit()

        logger.info(f"Error group {group_id} marked as resolved")

        return jsonify({
            'success': True,
            'group': group.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Resolve endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@error_bp.route('/cleanup', methods=['POST'])
@require_auth
def cleanup_errors():
    """
    Clean up old errors (keep last 30 days)
    POST /api/errors/cleanup
    """
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = ErrorLog.query.filter(
            ErrorLog.timestamp < cutoff_date
        ).delete()

        db.session.commit()

        logger.info(f"Deleted {deleted} old error logs")

        return jsonify({
            'success': True,
            'deleted': deleted
        }), 200

    except Exception as e:
        logger.error(f"Cleanup endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_error_stats(days=7):
    """Helper function to get error statistics"""
    since = datetime.utcnow() - timedelta(days=days)
    return {
        'total_errors': ErrorLog.query.filter(ErrorLog.timestamp >= since).count(),
        'unresolved_groups': ErrorGroup.query.filter_by(resolved=False).count(),
        'recent_errors': ErrorLog.query.filter(
            ErrorLog.timestamp >= since
        ).order_by(ErrorLog.timestamp.desc()).limit(10).all()
    }
