"""
Proctor Logger Module
Handles session-based logging for proctoring events and alerts
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
import threading


class AlertTracker:
    """
    Tracks alert streaks based on time continuity.
    A streak continues if the same alert appears within the timeout window.
    Logs only at start and end of streaks (no intermediate updates).
    """
    def __init__(self, streak_timeout=5.0):
        """
        Initialize AlertTracker
        
        Args:
            streak_timeout: Seconds of inactivity before ending a streak (default: 5s)
        """
        # Track each alert type separately: {alert_type: streak_info}
        # streak_info = {
        #   'start_ts': timestamp when streak started,
        #   'last_ts': timestamp of last occurrence,
        #   'count': number of occurrences
        # }
        self.active_streaks = {}
        self.streak_timeout = streak_timeout
    
    def should_log(self, alert_type, message, current_time=None):
        """
        Determine if alert should be logged based on time continuity
        
        Args:
            alert_type: Type of alert
            message: Alert message (not used in tracking, only alert_type matters)
            current_time: Current timestamp (uses time.time() if None)
            
        Returns:
            tuple: (should_log, duration_str, is_new_streak, streak_count, ended_streaks)
                   ended_streaks: list of streaks that timed out
        """
        if current_time is None:
            current_time = time.time()
        
        # First, check all active streaks for timeouts
        ended_streaks = self._check_timeouts(current_time)
        
        # Now handle the current alert
        if alert_type in self.active_streaks:
            streak = self.active_streaks[alert_type]
            time_since_last = current_time - streak['last_ts']
            
            # Check if streak is still active (within timeout window)
            if time_since_last <= self.streak_timeout:
                # Continue streak - NO LOGGING
                streak['count'] += 1
                streak['last_ts'] = current_time
                return False, None, False, streak['count'], ended_streaks
            else:
                # Streak timed out - this was already handled in _check_timeouts
                # Start new streak - LOG
                self.active_streaks[alert_type] = {
                    'start_ts': current_time,
                    'last_ts': current_time,
                    'count': 1
                }
                return True, None, True, 1, ended_streaks
        
        # New streak - LOG
        self.active_streaks[alert_type] = {
            'start_ts': current_time,
            'last_ts': current_time,
            'count': 1
        }
        return True, None, True, 1, ended_streaks
    
    def _check_timeouts(self, current_time):
        """
        Check all active streaks for timeouts and end them if necessary
        
        Args:
            current_time: Current timestamp
            
        Returns:
            list: List of ended streaks with their final info
        """
        ended_streaks = []
        keys_to_remove = []
        
        for alert_type, streak in self.active_streaks.items():
            time_since_last = current_time - streak['last_ts']
            
            # If streak timed out, mark it as ended
            if time_since_last > self.streak_timeout:
                duration = streak['last_ts'] - streak['start_ts']
                ended_streaks.append({
                    'alert_type': alert_type,
                    'duration': duration,
                    'count': streak['count']
                })
                keys_to_remove.append(alert_type)
        
        # Remove ended streaks
        for key in keys_to_remove:
            del self.active_streaks[key]
        
        return ended_streaks
    
    def get_streak_info(self, alert_type):
        """Get info about specific alert streak"""
        if alert_type not in self.active_streaks:
            return None
        
        streak = self.active_streaks[alert_type]
        current_time = time.time()
        duration = current_time - streak['start_ts']
        return {
            'alert_type': alert_type,
            'duration': duration,
            'count': streak['count']
        }
    
    def get_all_active_streaks(self):
        """Get info about all active streaks"""
        active = []
        current_time = time.time()
        
        for alert_type, streak in self.active_streaks.items():
            duration = streak['last_ts'] - streak['start_ts']
            active.append({
                'alert_type': alert_type,
                'duration': duration,
                'count': streak['count'],
                'last_ts': streak['last_ts']
            })
        return active
    
    def clear_streak(self, alert_type):
        """Clear a specific streak"""
        if alert_type in self.active_streaks:
            del self.active_streaks[alert_type]
    
    def clear_all(self):
        """Clear all streaks"""
        self.active_streaks.clear()


class ProctorLogger:
    """
    Session-based logger for proctoring alerts and events
    Uses a single test.log file that is cleared at the start of each session
    """
    
    def __init__(self, log_dir='logs/proctoring', session_id=None):
        """
        Initialize Proctor Logger
        
        Args:
            log_dir: Directory to store log files
            session_id: Optional session identifier (uses timestamp if None)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate session ID from timestamp if not provided
        if session_id is None:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.session_id = session_id
        
        # Use single test.log file (clear it at start of each session)
        self.log_file = self.log_dir / "test.log"
        self.alerts_file = self.log_dir / f"session_{self.session_id}_alerts.json"
        
        # Clear previous logs by removing the file if it exists
        if self.log_file.exists():
            self.log_file.unlink()
        
        # Session data
        self.session_start = datetime.now()
        self.session_data = {
            'session_id': self.session_id,
            'start_time': self.session_start.isoformat(),
            'end_time': None,
            'alerts': [],
            'statistics': {
                'total_frames': 0,
                'total_alerts': 0,
                'alert_types': {}
            }
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Alert tracker for streak-based logging (5s timeout)
        self.alert_tracker = AlertTracker(streak_timeout=5.0)
        
        # Configure file logger
        self.logger = logging.getLogger("ProctorLogger_test")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs (mode='w' to clear on each session)
        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger (no console output)
        self.logger.propagate = False
        
        # Log session start
        self.logger.info("=" * 80)
        self.logger.info(f"PROCTORING SESSION STARTED - ID: {self.session_id}")
        self.logger.info("=" * 80)
    
    def log_alert(self, alert_type, message, severity='warning', metadata=None):
        """
        Log an alert to the session with time-based streak detection
        
        Args:
            alert_type: Type of alert (e.g., 'multiple_faces', 'no_face', 'phone_detected')
            message: Alert message
            severity: Alert severity ('info', 'warning', 'critical')
            metadata: Additional metadata dictionary
        """
        with self.lock:
            current_time = time.time()
            
            # Check if we should log this alert based on time continuity
            should_log_now, duration_str, is_new_streak, streak_count, ended_streaks = self.alert_tracker.should_log(
                alert_type, message, current_time
            )
            
            # First, log any streaks that ended due to timeout
            if ended_streaks:
                for ended in ended_streaks:
                    end_msg = f"{ended['alert_type']}: {message} - ended after {int(ended['duration'])}s"
                    self.logger.warning(end_msg)
            
            timestamp = datetime.now()
            
            alert = {
                'timestamp': timestamp.isoformat(),
                'type': alert_type,
                'message': message,
                'severity': severity,
                'metadata': metadata or {},
                'streak_count': streak_count  # Track streak in data
            }
            
            # Always add to session data for statistics
            self.session_data['alerts'].append(alert)
            self.session_data['statistics']['total_alerts'] += 1
            
            # Update alert type count
            if alert_type not in self.session_data['statistics']['alert_types']:
                self.session_data['statistics']['alert_types'][alert_type] = 0
            self.session_data['statistics']['alert_types'][alert_type] += 1
            
            # Only log to file if should log now (start of new streak)
            if should_log_now and is_new_streak:
                log_message = f"{alert_type}: {message}"
                
                # Log based on severity (no metadata in log message)
                if severity == 'critical':
                    self.logger.critical(log_message)
                elif severity == 'warning':
                    self.logger.warning(log_message)
                else:
                    self.logger.info(log_message)
    
    def log_info(self, message):
        """Log general information"""
        with self.lock:
            self.logger.info(message)
    
    def log_frame_processed(self):
        """Increment frame counter"""
        with self.lock:
            self.session_data['statistics']['total_frames'] += 1
    
    def log_detection(self, detector_name, results):
        """
        Log detection results
        
        Args:
            detector_name: Name of the detector
            results: Detection results dictionary
        """
        with self.lock:
            message = f"Detection [{detector_name}]: {json.dumps(results, default=str)}"
            self.logger.debug(message)
    
    def save_session(self):
        """Save session data to JSON file. Must be called with lock already held!"""
        self.session_data['end_time'] = datetime.now().isoformat()
        
        try:
            
            with open(self.alerts_file, 'w') as f:
                
                json.dump(self.session_data, f, indent=2)
                
            
            
            self.logger.info(f"Session data saved to: {self.alerts_file}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session data: {e}")
            return False
        
    
    def get_session_summary(self):
        """
        Get session summary
        
        Returns:
            dict: Session statistics and summary
        """
        with self.lock:
            duration = (datetime.now() - self.session_start).total_seconds()
            
            return {
                'session_id': self.session_id,
                'duration_seconds': duration,
                'total_frames': self.session_data['statistics']['total_frames'],
                'total_alerts': self.session_data['statistics']['total_alerts'],
                'alert_types': self.session_data['statistics']['alert_types'],
                'log_file': str(self.log_file),
                'alerts_file': str(self.alerts_file)
            }
    
    def close(self):
        """Close logger and save session"""
        with self.lock:
            # Log all active streaks before closing
            active_streaks = self.alert_tracker.get_all_active_streaks()
            if active_streaks:
                self.logger.info("=" * 80)
                self.logger.info("FINAL ACTIVE ALERT STREAKS:")
                for streak_info in active_streaks:
                    log_message = (
                        f"{streak_info['alert_type']}: ended after {int(streak_info['duration'])}s"
                    )
                    self.logger.warning(log_message)
            
            self.logger.info("=" * 80)
            self.logger.info("PROCTORING SESSION ENDED")
            self.logger.info(f"Duration: {(datetime.now() - self.session_start).total_seconds():.2f} seconds")
            self.logger.info(f"Total Frames: {self.session_data['statistics']['total_frames']}")
            self.logger.info(f"Total Alerts: {self.session_data['statistics']['total_alerts']}")
            
            if self.session_data['statistics']['alert_types']:
                self.logger.info("\nAlert Summary:")
                for alert_type, count in self.session_data['statistics']['alert_types'].items():
                    self.logger.info(f"  - {alert_type}: {count}")
            
            self.logger.info("=" * 80)
            
            # Save session data
            self.save_session()
            
            # Remove handlers
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
