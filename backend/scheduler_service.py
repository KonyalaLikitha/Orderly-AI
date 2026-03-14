"""
Scheduler Service
Handles scheduled order execution using background tasks.
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .order_manager import order_manager


class SchedulerService:
    """
    Background scheduler that executes scheduled orders when their time arrives.
    Uses a simple polling mechanism for reliability.
    """
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize scheduler.
        
        Args:
            check_interval: How often to check for due orders (seconds)
        """
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list = []
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"Scheduler started - checking every {self.check_interval} seconds")
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("Scheduler stopped")
    
    def _run(self):
        """Main scheduler loop."""
        while self._running:
            try:
                self._check_and_execute()
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_and_execute(self):
        """Check for due orders and execute them."""
        now = datetime.now()
        
        # Check each scheduled order
        for scheduled_order in order_manager.scheduled_orders[:]:  # Copy list
            scheduled_time = datetime.fromisoformat(scheduled_order['scheduled_datetime'])
            
            if scheduled_time <= now:
                # Order is due - execute it
                order_id = scheduled_order['id']
                result = order_manager.execute_scheduled_order(order_id)
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(scheduled_order, result)
                    except Exception as e:
                        print(f"Callback error: {e}")
    
    def add_callback(self, callback):
        """Add a callback function to be called when an order executes."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove a callback function."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "scheduled_orders": len(order_manager.scheduled_orders),
            "check_interval": self.check_interval
        }


# Global scheduler instance
scheduler = SchedulerService()


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()


def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    return scheduler.get_status()
