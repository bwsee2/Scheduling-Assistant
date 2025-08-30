from flask import Flask, redirect, request, session, url_for, render_template, jsonify
import os
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import re
from collections import defaultdict
import time
import json



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# Set OAuth insecure transport for development
if os.environ.get('FLASK_ENV') != 'production':
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Dynamic redirect URI based on environment
if os.environ.get('RENDER'):
    # Running on Render
    REDIRECT_URI = "https://scheduling-assistant-blan.onrender.com/oauth2callback"
else:
    # Running locally
    REDIRECT_URI = "http://localhost:8080/oauth2callback"





class SchedulingAgent:
    """Intelligent agent for understanding and processing scheduling requests"""
    
    def __init__(self):
        self.query_patterns = defaultdict(int)
        self.successful_queries = []
    
    def learn_from_query(self, query, result, success=True):
        """Learn from user queries to improve future responses"""
        query_lower = query.lower()
        
        # Extract patterns
        patterns = self.extract_patterns(query_lower)
        for pattern in patterns:
            self.query_patterns[pattern] += 1
        
        # Store successful queries
        if success:
            self.successful_queries.append({
                'query': query,
                'result': result,
                'timestamp': datetime.datetime.now()
            })
            
            # Limit history to last 100 queries
            if len(self.successful_queries) > 100:
                self.successful_queries.pop(0)
    
    def extract_patterns(self, query):
        """Extract meaningful patterns from queries"""
        patterns = []
        
        # Time patterns
        time_patterns = [
            r'\d+\s*(?:min|minute|hour|hr)s?',
            r'(?:next|this)\s+week',
            r'(?:next|this)\s+month',
            r'today|tomorrow',
            r'a\s+week|one\s+week|7\s+days'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, query):
                patterns.append(pattern)
        
        return patterns
    
    def get_contextual_response(self, query, result):
        """Provide contextual response based on the query and result"""
        query_lower = query.lower()
        
        # Create the response structure that frontend expects
        response = {
            'contextual_message': '',
            'suggestions': [],
            'patterns_learned': len(self.query_patterns),
            'successful_queries': len(self.successful_queries)
        }
        
        # Analyze the query intent
        if 'urgent' in query_lower or 'asap' in query_lower:
            response['contextual_message'] = "🚨 I found urgent time slots for you!"
        elif 'flexible' in query_lower or 'anytime' in query_lower:
            response['contextual_message'] = "📅 Here are all available flexible time slots!"
        elif 'meeting' in query_lower:
            response['contextual_message'] = "🤝 Perfect meeting times found!"
        elif 'call' in query_lower:
            response['contextual_message'] = "📞 Available call slots!"
        else:
            response['contextual_message'] = "⏰ Available time slots found!"
        
        # Add contextual information based on time range
        if result.get('time_range') == 'a_week':
            response['contextual_message'] += " (Showing next 7 days including weekends)"
        elif result.get('time_range') == 'next_week':
            response['contextual_message'] += " (Showing business days of next week)"
        elif result.get('time_range') == 'today':
            response['contextual_message'] += " (Showing remaining time today)"
        elif result.get('time_range') == 'tomorrow':
            response['contextual_message'] += " (Showing available slots for tomorrow)"
        
        # Add suggestions based on patterns
        if len(self.successful_queries) > 0:
            response['suggestions'].append("Try asking for specific time ranges like 'between 2 pm and 5 pm'")
            response['suggestions'].append("You can also specify duration like '1 hour meeting'")
        
        return response

# Initialize the agent
scheduling_agent = SchedulingAgent()

@app.route('/')
def index():
    if 'credentials' not in session:
        return render_template('landing.html')
    return render_template('index.html')

@app.route('/test')
def test_css():
    return render_template('test_css.html')

@app.route('/authorize')
def authorize():
    if "GOOGLE_CLIENT_SECRET_JSON" in os.environ:
    # Render or other production environment
        client_config = json.loads(os.environ["GOOGLE_CLIENT_SECRET_JSON"])
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
    )
    else:
    # Local development
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    auth_url, state = flow.authorization_url(prompt='consent')
    session['state'] = state
    return redirect(auth_url)


@app.route('/oauth2callback')
def callback():
    try:
        state = session['state']
        
        # Use environment variable for Render, file for local development
        if os.environ.get('RENDER'):
            # Render or other production environment
            client_config = json.loads(os.environ["GOOGLE_CLIENT_SECRET_JSON"])
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                state=state,
                redirect_uri=REDIRECT_URI
            )
        else:
            # Local development
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                state=state,
                redirect_uri=REDIRECT_URI
            )
        
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        return redirect(url_for('index'))
    except Exception as e:
        return f"<h2>Error during callback:</h2><pre>{str(e)}</pre>"

@app.route('/logout')
def logout():
    """Clear session and redirect to landing page"""
    session.clear()
    return redirect(url_for('index'))



# Simple cache for calendar events (in-memory, will reset when server restarts)
_calendar_cache = {}
_cache_timestamp = 0
CACHE_DURATION = 300  # 5 minutes

def get_calendar_events():
    """Get calendar events from all available Google Calendars"""
    global _calendar_cache, _cache_timestamp
    
    # Check if we have recent cached data
    current_time = time.time()
    if current_time - _cache_timestamp < CACHE_DURATION and _calendar_cache:
        return _calendar_cache.copy()
    
    try:
        if 'credentials' not in session:
            return []
        
        creds = session['credentials']
        credentials = Credentials(**creds)
        service = build('calendar', 'v3', credentials=credentials)
        
        now = datetime.datetime.now()
        # Start from 6 months ago
        start_time = now - datetime.timedelta(days=180)
        # End 2 years from now
        end_time = now + datetime.timedelta(days=730)
        
        # Get list of all available calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        # Fetch events from all calendars
        all_events = fetch_events_from_calendars(service, calendars, start_time, end_time)
        
        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'])
        
        # Cache the results
        _calendar_cache = all_events
        _cache_timestamp = current_time
        
        return all_events
        
    except Exception as e:
        print(f"ERROR getting calendar events: {str(e)}")
        return []



def fetch_events_from_calendars(service, calendars, start_time, end_time):
    """Fetch events from multiple calendars"""
    all_events = []
    
    for calendar in calendars:
        calendar_id = calendar['id']
        calendar_summary = calendar.get('summary', 'Unknown Calendar')
        calendar_color = calendar.get('backgroundColor', '#4285f4')
        
        try:
            events = fetch_events_from_calendar(
                service,
                calendar_id,
                calendar_summary,
                calendar_color,
                start_time,
                end_time
            )
            all_events.extend(events)
        except Exception as e:
            print(f"ERROR fetching events from {calendar_summary}: {str(e)}")
            continue
    
    return all_events

def fetch_events_from_calendar(service, calendar_id, calendar_summary, calendar_color, start_time, end_time):
    """Fetch events from a single calendar"""
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime',
            maxResults=1000
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'No title')
            
            formatted_events.append({
                'summary': summary,
                'start': start,
                'end': end,
                'calendar_id': calendar_id,
                'calendar_name': calendar_summary,
                'calendar_color': calendar_color
            })
        
        return formatted_events
        
    except Exception as e:
        print(f"ERROR fetching events from calendar {calendar_summary}: {str(e)}")
        return []

def get_calendar_events_for_range(start_date_str, end_date_str):
    """Get calendar events for a specific date range from all calendars with optimized fetching"""
    try:
        if 'credentials' not in session:
            return []
        
        creds = session['credentials']
        credentials = Credentials(**creds)
        service = build('calendar', 'v3', credentials=credentials)
        
        # Parse date strings
        start_time = datetime.datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        # Get list of all available calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        # Fetch events from all calendars for the specified range
        all_events = fetch_events_from_calendars(service, calendars, start_time, end_time)
        
        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'])
        
        return all_events
        
    except Exception as e:
        print(f"ERROR getting calendar events for range: {str(e)}")
        return []

@app.route('/get_events')
def get_events():
    """API endpoint to get calendar events"""
    events = get_calendar_events()
    return jsonify({
        'success': True,
        'events': events
    })

@app.route('/get_events_range', methods=['POST'])
def get_events_range():
    """API endpoint to get calendar events for a specific date range"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Start and end dates required'})
        
        events = get_calendar_events_for_range(start_date, end_date)
        return jsonify({
            'success': True,
            'events': events
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@app.route('/find_slots', methods=['POST'])
def find_slots():
    """Find available time slots based on user query"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'})
        
        # Parse the query first
        query_params = parse_scheduling_query(query)
        
        # Learn from this query
        scheduling_agent.learn_from_query(query, query_params)
        
        # Get events from all connected calendars
        events = get_calendar_events()
        
        # Find available slots
        available_slots = find_available_slots(events, query_params['start_time'], query_params['end_time'], query_params)
        
        # Get agent insights
        agent_insights = scheduling_agent.get_contextual_response(query, query_params)
        
        # Prepare response
        response_data = {
            'success': True,
            'slots': available_slots,
            'events': events,  # Include events for frontend filtering
            'agent_insights': agent_insights
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def parse_scheduling_query(query):
    """Use simple parser for all queries"""
    print("DEBUG: Using simple parser for all queries")
    return simple_query_parser(query)

def get_next_weekday(current_date, target_weekday):
    """Get the next occurrence of a specific weekday (0=Monday, 6=Sunday)"""
    days_ahead = target_weekday - current_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    next_date = current_date + datetime.timedelta(days=days_ahead)
    print(f"DEBUG: Current date: {current_date.strftime('%Y-%m-%d %A')}, Target weekday: {target_weekday}, Days ahead: {days_ahead}, Next date: {next_date.strftime('%Y-%m-%d %A')}")
    return next_date

def simple_query_parser(query):
    """Simple and intuitive query parser for finding free time"""
    query_lower = query.lower()
    
    # Default values
    duration_minutes = 30
    buffer_minutes = 30
    
    # Extract duration
    duration_patterns = [
        (r'(\d+)\s*(?:min|minute|minutes)', lambda m: int(m.group(1))),
        (r'(\d+)\s*(?:hour|hours)', lambda m: int(m.group(1)) * 60),
        (r'(\d+)\s*(?:hr|hrs)', lambda m: int(m.group(1)) * 60),
    ]
    
    for pattern, converter in duration_patterns:
        match = re.search(pattern, query_lower)
        if match:
            duration_minutes = converter(match)
            break
    
    # Extract buffer time
    buffer_patterns = [
        (r'(\d+)\s*(?:min|minute|minutes?)\s*(?:break|buffer)', lambda m: int(m.group(1))),
        (r'(\d+)\s*(?:hour|hours?)\s*(?:break|buffer)', lambda m: int(m.group(1)) * 60),
        (r'no\s+break', lambda m: 0),
        (r'no\s+buffer', lambda m: 0),
    ]
    
    for pattern, converter in buffer_patterns:
        match = re.search(pattern, query_lower)
        if match:
            buffer_minutes = converter(match)
            break
    
    # Calculate start and end times based on intuitive patterns
    now = datetime.datetime.now()
    
    # Simple, intuitive time range detection
    if 'tomorrow' in query_lower:
        # Tomorrow = next day
        start_time = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'tomorrow'
        
    elif 'next week' in query_lower:
        # Next week = next 7 days from today
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=7)
        num_days = 7
        time_range = 'next_week'
        
    elif 'this week' in query_lower:
        # This week = next 7 days from today (same as next week for simplicity)
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=7)
        num_days = 7
        time_range = 'this_week'
        
    elif 'a week' in query_lower or 'one week' in query_lower or '7 days' in query_lower:
        # A week = next 7 days from today
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=7)
        num_days = 7
        time_range = 'a_week'
        
    elif 'today' in query_lower:
        # Today = remaining time today
        start_time = now
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        num_days = 1
        time_range = 'today'
        
    elif 'weekend' in query_lower:
        # Weekend = next Saturday and Sunday
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0:  # Today is Saturday
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_time = (now + datetime.timedelta(days=days_until_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=2)
        num_days = 2
        time_range = 'weekend'
        
    elif 'next month' in query_lower:
        # Next month = next 30 days
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=30)
        num_days = 30
        time_range = 'next_month'
        
    elif '2 days' in query_lower or 'two days' in query_lower:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=2)
        num_days = 2
        time_range = 'two_days'
        
    elif '3 days' in query_lower or 'three days' in query_lower:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=3)
        num_days = 3
        time_range = 'three_days'
        
    elif '5 days' in query_lower or 'five days' in query_lower:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=5)
        num_days = 5
        time_range = 'five_days'
        
    elif 'next monday' in query_lower:
        # Next Monday (weekday 0)
        next_monday = get_next_weekday(now, 0)
        start_time = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_monday'
        print(f"DEBUG: Query 'next monday' - Next Monday calculated: {next_monday.strftime('%Y-%m-%d %A')}")
        
    elif 'next tuesday' in query_lower:
        # Next Tuesday (weekday 1)
        next_tuesday = get_next_weekday(now, 1)
        start_time = next_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_tuesday'
        
    elif 'next wednesday' in query_lower:
        # Next Wednesday (weekday 2)
        next_wednesday = get_next_weekday(now, 2)
        start_time = next_wednesday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_wednesday'
        
    elif 'next thursday' in query_lower:
        # Next Thursday (weekday 3)
        next_thursday = get_next_weekday(now, 3)
        start_time = next_thursday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_thursday'
        
    elif 'next friday' in query_lower:
        # Next Friday (weekday 4)
        next_friday = get_next_weekday(now, 4)
        start_time = next_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_friday'
        
    elif 'next saturday' in query_lower:
        # Next Saturday (weekday 5)
        next_saturday = get_next_weekday(now, 5)
        start_time = next_saturday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_saturday'
        
    elif 'next sunday' in query_lower:
        # Next Sunday (weekday 6)
        next_sunday = get_next_weekday(now, 6)
        start_time = next_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)
        num_days = 1
        time_range = 'next_sunday'
        
    else:
        # Default: next 7 days
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=7)
        num_days = 7
        time_range = 'default'
    
    return {
        'duration_minutes': duration_minutes,
        'buffer_minutes': buffer_minutes,
        'time_range': time_range,
        'start_time': start_time,
        'end_time': end_time,
        'num_days': num_days
    }



def find_available_slots(events, start_time, end_time, query_params):
    """Find available time slots, excluding times that conflict with existing events"""
    available_slots = []
    now = datetime.datetime.now()
    
    # Parse time constraints from query params
    start_time_constraint = query_params.get('start_time_constraint')
    end_time_constraint = query_params.get('end_time_constraint')
    
    # Convert events to datetime objects for comparison
    event_times = []
    for event in events:
        try:
            # Parse event times and convert to local timezone
            event_start_str = event['start']
            event_end_str = event['end']
            
            # Handle different timezone formats
            if 'T' in event_start_str:
                # ISO format with timezone
                if event_start_str.endswith('Z'):
                    event_start_str = event_start_str.replace('Z', '+00:00')
                if event_end_str.endswith('Z'):
                    event_end_str = event_end_str.replace('Z', '+00:00')
                
                event_start = datetime.datetime.fromisoformat(event_start_str)
                event_end = datetime.datetime.fromisoformat(event_end_str)
                
                # Convert to local timezone (remove timezone info for comparison)
                event_start = event_start.replace(tzinfo=None)
                event_end = event_end.replace(tzinfo=None)
            else:
                # Date-only format
                event_start = datetime.datetime.fromisoformat(event_start_str)
                event_end = datetime.datetime.fromisoformat(event_end_str)
            
            event_times.append((event_start, event_end))
        except Exception as e:
            continue
    
    # Generate slots for each day in the range
    current_date = start_time.date()
    end_date = end_time.date()
    
    while current_date <= end_date:
        current_day = current_date
        weekday = current_day.weekday()
        
        # Check if we should include weekends
        include_weekends = query_params.get('time_range') in ['a_week', 'next_week', 'two_weeks', 'three_weeks', 'four_weeks']
        
        # For specific day requests, always include the requested day regardless of weekend
        if query_params.get('time_range') in ['specific_day', 'next_specific_day']:
            include_weekends = True
        
        # Skip weekends unless explicitly requested
        if weekday >= 5 and not include_weekends:  # Saturday = 5, Sunday = 6
            current_date += datetime.timedelta(days=1)
            continue
        
        # Set business hours for this day
        day_start = datetime.datetime.combine(current_day, datetime.time(9, 0))  # 9 AM
        day_end = datetime.datetime.combine(current_day, datetime.time(17, 0))   # 5 PM
        
        # If it's today, start from now instead of 9 AM
        if current_day == now.date():
            day_start = now
        
        # Apply time constraints if specified
        if start_time_constraint:
            constraint_hour, constraint_minute = map(int, start_time_constraint.split(':'))
            day_start = datetime.datetime.combine(current_day, datetime.time(constraint_hour, constraint_minute))
            
        if end_time_constraint:
            constraint_hour, constraint_minute = map(int, end_time_constraint.split(':'))
            day_end = datetime.datetime.combine(current_day, datetime.time(constraint_hour, constraint_minute))
        
        # Generate 30-minute slots
        slot_start = day_start
        day_slots_count = 0
        
        while slot_start < day_end:
            slot_end = slot_start + datetime.timedelta(minutes=30)
            
            # Check if this slot conflicts with any events
            slot_conflicts = False
            for event_start, event_end in event_times:
                # Check if the slot overlaps with the event
                # A slot conflicts if it starts before the event ends AND ends after the event starts
                if (slot_start < event_end and slot_end > event_start):
                    slot_conflicts = True
                    break
            
            # Only add slot if it doesn't conflict with events
            if not slot_conflicts and slot_start > now:
                available_slots.append({
                    'start_time': slot_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': slot_end.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': 30
                })
                day_slots_count += 1
            
            slot_start = slot_end
        
        current_date += datetime.timedelta(days=1)
    
    return available_slots

if __name__ == '__main__':
    # Get port from environment variable (for Render) or use default
    port = int(os.environ.get('PORT', 8080))
    
    # Set debug mode based on environment
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    # Use 0.0.0.0 for Render, localhost for local development
    host = '0.0.0.0' if os.environ.get('RENDER') else 'localhost'
    
    app.run(host=host, port=port, debug=debug)
