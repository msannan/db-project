from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, static_folder="static", template_folder=".")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin123@localhost/db1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # For session management

# Initialize the database
db = SQLAlchemy(app)

# Models matching your schema
class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    FName = db.Column(db.String(100), nullable=False)
    LName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    gender = db.Column(db.String(10))
    DOB = db.Column(db.Date)
    password = db.Column(db.String(255), nullable=False)  # Added for authentication

class Creator(db.Model):
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    events = db.relationship('Event', backref='creator', lazy=True)

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator.creator_id', ondelete='CASCADE'))
    event_name = db.Column(db.String(255), nullable=False)
    event_place = db.Column(db.Text)
    event_start_date = db.Column(db.DateTime, nullable=False)
    event_end_date = db.Column(db.DateTime, nullable=False)
    deadline_enforced = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50))
    
class Participants(db.Model):
    P_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    user = db.relationship('Users', backref='participations')
    event = db.relationship('Event', backref='participants')

class Eligibility_Criteria(db.Model):
    criteria_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    rule_type = db.Column(db.String(255), nullable=False)
    rule_value = db.Column(db.Text, nullable=False)
    event = db.relationship('Event', backref='eligibility_criteria')

class Inputs(db.Model):
    input_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    label = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    default_value = db.Column(db.Text)
    validation_rules = db.Column(db.Text)
    event = db.relationship('Event', backref='inputs')

class Submissions(db.Model):
    submission_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    P_id = db.Column(db.Integer, db.ForeignKey('participants.P_id', ondelete='CASCADE'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    event = db.relationship('Event', backref='submissions')
    participant = db.relationship('Participants', backref='submissions')

class Submission_Values(db.Model):
    suva_id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.submission_id', ondelete='CASCADE'))
    input_id = db.Column(db.Integer, db.ForeignKey('inputs.input_id', ondelete='CASCADE'))
    value = db.Column(db.Text)
    submission = db.relationship('Submissions', backref='values')
    input = db.relationship('Inputs', backref='submission_values')

class Event_Statistics(db.Model):
    stat_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    summary_type = db.Column(db.String(255))
    public_viewable = db.Column(db.Boolean, default=False)
    event = db.relationship('Event', backref='statistics')

class Reminders(db.Model):
    reminder_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'))
    P_id = db.Column(db.Integer, db.ForeignKey('participants.P_id', ondelete='CASCADE'))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    event = db.relationship('Event', backref='reminders')
    participant = db.relationship('Participants', backref='reminders')

# Helper function to convert model objects to dictionaries
def to_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

# Routes for serving HTML pages
@app.route('/')
def index():
    return render_template('main.html')

# Authentication routes

@app.route('/api/creator/register', methods=['POST'])
def creator_register():
    data = request.json
    
    # Check if email already exists
    if Users.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    try:
        # Create user
        user = Users(
            FName=data['firstName'],
            LName=data['lastName'],
            email=data['email'],
            gender=data['gender'],
            DOB=datetime.strptime(data['dob'], '%Y-%m-%d'),
            password=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.flush()  # Get the user_id without committing
        
        # Create creator
        creator = Creator(creator_id=user.user_id)
        db.session.add(creator)
        db.session.commit()
        
        return jsonify({"message": "Creator registered successfully", "creator_id": creator.creator_id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/creator/login', methods=['POST'])
def creator_login():
    data = request.json
    
    user = Users.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    creator = Creator.query.filter_by(creator_id=user.user_id).first()
    
    if not creator:
        return jsonify({"error": "User is not registered as a creator"}), 403
    
    session['creator_id'] = creator.creator_id
    session['user_id'] = user.user_id
    session['user_name'] = f"{user.FName} {user.LName}"
    
    return jsonify({
        "message": "Login successful",
        "creator_id": creator.creator_id,
        "name": f"{user.FName} {user.LName}"
    })

@app.route('/api/participant/register', methods=['POST'])
def participant_register():
    data = request.json
    
    # Check if email already exists
    if Users.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    try:
        # Create user
        user = Users(
            FName=data['firstName'],
            LName=data['lastName'],
            email=data['email'],
            gender=data['gender'],
            DOB=datetime.strptime(data['dob'], '%Y-%m-%d'),
            password=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "Participant registered successfully", "user_id": user.user_id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/participant/login', methods=['POST'])
def participant_login():
    data = request.json
    
    user = Users.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    session['user_id'] = user.user_id
    session['user_name'] = f"{user.FName} {user.LName}"
    
    return jsonify({
        "message": "Login successful",
        "user_id": user.user_id,
        "name": f"{user.FName} {user.LName}"
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

# Event management routes

@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([to_dict(event) for event in events])

@app.route('/api/creator/events', methods=['GET'])
def get_creator_events():
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    events = Event.query.filter_by(creator_id=session['creator_id']).all()
    return jsonify([to_dict(event) for event in events])

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(to_dict(event))

@app.route('/api/events', methods=['POST'])
def create_event():
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    data = request.json
    
    try:
        event = Event(
            creator_id=session['creator_id'],
            event_name=data['eventName'],
            event_place=data['place'],
            event_start_date=datetime.strptime(data['startDate'], '%Y-%m-%d'),
            event_end_date=datetime.strptime(data['endDate'], '%Y-%m-%d'),
            deadline_enforced=data.get('deadlineEnforced', False),
            status='Open'
        )
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            "message": "Event created successfully", 
            "event_id": event.event_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to update this event"}), 403
    
    data = request.json
    
    try:
        if 'eventName' in data:
            event.event_name = data['eventName']
        if 'place' in data:
            event.event_place = data['place']
        if 'startDate' in data:
            event.event_start_date = datetime.strptime(data['startDate'], '%Y-%m-%d')
        if 'endDate' in data:
            event.event_end_date = datetime.strptime(data['endDate'], '%Y-%m-%d')
        if 'deadlineEnforced' in data:
            event.deadline_enforced = data['deadlineEnforced']
        if 'status' in data:
            event.status = data['status']
        
        db.session.commit()
        
        return jsonify({"message": "Event updated successfully"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to delete this event"}), 403
    
    try:
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({"message": "Event deleted successfully"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Eligibility criteria routes

@app.route('/api/events/<int:event_id>/criteria', methods=['POST'])
def add_criteria(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to add criteria to this event"}), 403
    
    data = request.json
    
    try:
        criteria = Eligibility_Criteria(
            event_id=event_id,
            rule_type=data['ruleType'],
            rule_value=data['ruleValue']
        )
        db.session.add(criteria)
        db.session.commit()
        
        return jsonify({
            "message": "Eligibility criteria added successfully", 
            "criteria_id": criteria.criteria_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/<int:event_id>/criteria', methods=['GET'])
def get_criteria(event_id):
    criteria = Eligibility_Criteria.query.filter_by(event_id=event_id).all()
    return jsonify([to_dict(c) for c in criteria])

# Input fields routes

@app.route('/api/events/<int:event_id>/inputs', methods=['POST'])
def add_input(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to add inputs to this event"}), 403
    
    data = request.json
    
    try:
        input_field = Inputs(
            event_id=event_id,
            label=data['label'],
            field_type=data['fieldType'],
            default_value=data.get('defaultValue'),
            validation_rules=data.get('validationRules')
        )
        db.session.add(input_field)
        db.session.commit()
        
        return jsonify({
            "message": "Input field added successfully", 
            "input_id": input_field.input_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/<int:event_id>/inputs', methods=['GET'])
def get_inputs(event_id):
    inputs = Inputs.query.filter_by(event_id=event_id).all()
    return jsonify([to_dict(i) for i in inputs])

# Participant management routes

@app.route('/api/events/<int:event_id>/participate', methods=['POST'])
def participate_in_event(event_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if user is already a participant
    existing = Participants.query.filter_by(user_id=session['user_id'], event_id=event_id).first()
    if existing:
        return jsonify({"error": "Already participating in this event"}), 400
    
    try:
        participant = Participants(
            user_id=session['user_id'],
            event_id=event_id
        )
        db.session.add(participant)
        db.session.commit()
        
        return jsonify({
            "message": "Successfully joined event", 
            "P_id": participant.P_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/events', methods=['GET'])
def get_user_events():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    participations = Participants.query.filter_by(user_id=session['user_id']).all()
    events = []
    
    for p in participations:
        event = Event.query.get(p.event_id)
        if event:
            event_dict = to_dict(event)
            event_dict['P_id'] = p.P_id
            events.append(event_dict)
    
    return jsonify(events)

# Submission routes

@app.route('/api/events/<int:event_id>/submit', methods=['POST'])
def submit_responses(event_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    participant = Participants.query.filter_by(user_id=session['user_id'], event_id=event_id).first()
    if not participant:
        return jsonify({"error": "Not participating in this event"}), 403
    
    data = request.json
    
    try:
        # Create submission record
        submission = Submissions(
            event_id=event_id,
            P_id=participant.P_id
        )
        db.session.add(submission)
        db.session.flush()  # To get the submission ID
        
        # Add each response value
        for input_id, value in data['responses'].items():
            submission_value = Submission_Values(
                submission_id=submission.submission_id,
                input_id=int(input_id),
                value=value
            )
            db.session.add(submission_value)
        
        db.session.commit()
        
        return jsonify({
            "message": "Submission successful", 
            "submission_id": submission.submission_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Event statistics routes

@app.route('/api/events/<int:event_id>/statistics', methods=['GET'])
def get_event_statistics(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Get public statistics or check if creator is requesting
    stats = Event_Statistics.query.filter_by(
        event_id=event_id,
        public_viewable=True
    ).all()
    
    if 'creator_id' in session and event.creator_id == session['creator_id']:
        # Creator can see all statistics
        stats = Event_Statistics.query.filter_by(event_id=event_id).all()
    
    # Additional computed statistics
    participant_count = Participants.query.filter_by(event_id=event_id).count()
    submission_count = Submissions.query.filter_by(event_id=event_id).count()
    
    return jsonify({
        "stored_statistics": [to_dict(s) for s in stats],
        "computed_statistics": {
            "participant_count": participant_count,
            "submission_count": submission_count,
            "submission_rate": participant_count and round((submission_count / participant_count) * 100, 2) or 0
        }
    })

@app.route('/api/events/<int:event_id>/statistics', methods=['POST'])
def add_event_statistics(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to add statistics to this event"}), 403
    
    data = request.json
    
    try:
        stat = Event_Statistics(
            event_id=event_id,
            summary_type=data['summaryType'],
            public_viewable=data.get('publicViewable', False)
        )
        db.session.add(stat)
        db.session.commit()
        
        return jsonify({
            "message": "Statistic added successfully", 
            "stat_id": stat.stat_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Reminder routes

@app.route('/api/events/<int:event_id>/reminders', methods=['POST'])
def send_reminder(event_id):
    if 'creator_id' not in session:
        return jsonify({"error": "Not authenticated as creator"}), 401
    
    event = Event.query.get_or_404(event_id)
    
    # Check if the logged-in creator owns this event
    if event.creator_id != session['creator_id']:
        return jsonify({"error": "Not authorized to send reminders for this event"}), 403
    
    data = request.json
    participants = data.get('participants', [])
    
    if not participants:  # If empty, send to all participants
        participant_records = Participants.query.filter_by(event_id=event_id).all()
        participants = [p.P_id for p in participant_records]
    
    reminders_sent = []
    
    try:
        for p_id in participants:
            reminder = Reminders(
                event_id=event_id,
                P_id=p_id
            )
            db.session.add(reminder)
            reminders_sent.append(p_id)
        
        db.session.commit()
        
        return jsonify({
            "message": f"Reminders sent to {len(reminders_sent)} participants", 
            "participants": reminders_sent
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Initialize the database tables
@app.route('/api/init-db', methods=['GET'])
def init_db():
    try:
        db.create_all()
        return jsonify({"message": "Database initialized successfully!"})
    except Exception as e:
        return jsonify({"error": f"Database initialization error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)