import sqlite3
import json
import os
from datetime import datetime
from config import DB_CONFIG

class DatabaseManager:
    """
    Manages storage of traffic patterns, decisions, and learning history
    """
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_CONFIG['db_path']
        self.conn = None
        self.init_database()
        
    def init_database(self):
        """Initialize database and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                num_lanes INTEGER,
                total_vehicles INTEGER,
                total_passed INTEGER,
                avg_wait_time REAL,
                emergencies_handled INTEGER,
                accidents_handled INTEGER
            )
        ''')
        
        # Decisions table (RL agent decisions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                state_json TEXT,
                action INTEGER,
                lane_id INTEGER,
                duration INTEGER,
                reward REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Traffic patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lane_data_json TEXT,
                total_weight REAL,
                emergency_active BOOLEAN,
                accident_active BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Events table (emergencies, accidents)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                lane_id INTEGER,
                response_time REAL,
                cleared BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Model checkpoints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filepath TEXT,
                episodes INTEGER,
                avg_reward REAL,
                epsilon REAL
            )
        ''')
        
        # Analytics aggregates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                hour INTEGER,
                avg_wait_time REAL,
                total_vehicles INTEGER,
                emergency_count INTEGER,
                most_congested_lane INTEGER
            )
        ''')
        
        self.conn.commit()
        
    def start_session(self, num_lanes):
        """Start a new simulation session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (num_lanes, total_vehicles, total_passed,
                                avg_wait_time, emergencies_handled, accidents_handled)
            VALUES (?, 0, 0, 0, 0, 0)
        ''', (num_lanes,))
        self.conn.commit()
        return cursor.lastrowid
    
    def end_session(self, session_id, stats):
        """End a session and update final statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions
            SET end_time = CURRENT_TIMESTAMP,
                total_vehicles = ?,
                total_passed = ?,
                avg_wait_time = ?,
                emergencies_handled = ?,
                accidents_handled = ?
            WHERE id = ?
        ''', (
            stats.get('total_vehicles', 0),
            stats.get('total_passed', 0),
            stats.get('avg_wait_time', 0),
            stats.get('emergencies_handled', 0),
            stats.get('accidents_handled', 0),
            session_id
        ))
        self.conn.commit()
        
    def log_decision(self, session_id, state, action, lane_id, duration, reward):
        """Log an RL agent decision"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO decisions (session_id, state_json, action, lane_id, duration, reward)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, json.dumps(state.tolist() if hasattr(state, 'tolist') else state),
              action, lane_id, duration, reward))
        self.conn.commit()
        
    def log_pattern(self, session_id, lane_data, total_weight, emergency, accident):
        """Log current traffic pattern"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO patterns (session_id, lane_data_json, total_weight,
                                emergency_active, accident_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, json.dumps(lane_data), total_weight, emergency, accident))
        self.conn.commit()
        
    def log_event(self, session_id, event_type, lane_id):
        """Log an emergency or accident event"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO events (session_id, event_type, lane_id)
            VALUES (?, ?, ?)
        ''', (session_id, event_type, lane_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def clear_event(self, event_id, response_time):
        """Mark an event as cleared"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE events
            SET cleared = TRUE, response_time = ?
            WHERE id = ?
        ''', (response_time, event_id))
        self.conn.commit()
        
    def save_checkpoint(self, filepath, episodes, avg_reward, epsilon):
        """Save model checkpoint reference"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO checkpoints (filepath, episodes, avg_reward, epsilon)
            VALUES (?, ?, ?, ?)
        ''', (filepath, episodes, avg_reward, epsilon))
        self.conn.commit()
        
    def get_latest_checkpoint(self):
        """Get the most recent model checkpoint"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM checkpoints ORDER BY id DESC LIMIT 1
        ''')
        return cursor.fetchone()
    
    def get_historical_patterns(self, limit=100):
        """Get recent traffic patterns for analysis"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM patterns ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_decision_history(self, session_id=None, limit=50):
        """Get decision history"""
        cursor = self.conn.cursor()
        if session_id:
            cursor.execute('''
                SELECT * FROM decisions WHERE session_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (session_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
        return cursor.fetchall()
    
    def get_session_stats(self, session_id):
        """Get statistics for a specific session"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        return cursor.fetchone()
    
    def get_all_sessions(self, limit=20):
        """Get recent sessions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_analytics_summary(self):
        """Get analytics summary"""
        cursor = self.conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(total_vehicles) as total_vehicles,
                SUM(total_passed) as total_passed,
                AVG(avg_wait_time) as avg_wait_time,
                SUM(emergencies_handled) as total_emergencies,
                SUM(accidents_handled) as total_accidents
            FROM sessions
        ''')
        overall = cursor.fetchone()
        
        # Recent decisions performance
        cursor.execute('''
            SELECT AVG(reward) as avg_reward
            FROM decisions
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        recent = cursor.fetchone()
        
        return {
            'total_sessions': overall['total_sessions'] or 0,
            'total_vehicles': overall['total_vehicles'] or 0,
            'total_passed': overall['total_passed'] or 0,
            'avg_wait_time': overall['avg_wait_time'] or 0,
            'total_emergencies': overall['total_emergencies'] or 0,
            'total_accidents': overall['total_accidents'] or 0,
            'recent_avg_reward': recent['avg_reward'] or 0
        }
    
    def get_lane_performance(self, session_id=None):
        """Get performance metrics per lane"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT lane_id, 
                   COUNT(*) as times_served,
                   AVG(duration) as avg_duration,
                   AVG(reward) as avg_reward
            FROM decisions
        '''
        
        if session_id:
            query += ' WHERE session_id = ?'
            cursor.execute(query + ' GROUP BY lane_id', (session_id,))
        else:
            cursor.execute(query + ' GROUP BY lane_id')
            
        return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
