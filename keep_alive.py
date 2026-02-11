import requests
import time
import threading
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RenderPingService:
    def __init__(self, app_url, ping_interval=14*60):  # 14 minutes (less than 15 min sleep time)
        self.app_url = app_url.rstrip('/')
        self.ping_interval = ping_interval
        self.running = False
        self.thread = None
        
    def ping_server(self):
        """Send a GET request to keep the server awake"""
        try:
            # Ping the main endpoint
            response = requests.get(f"{self.app_url}/", timeout=30)
            logger.info(f"✅ Server ping successful - Status: {response.status_code} - Time: {datetime.now().strftime('%H:%M:%S')}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Server ping failed: {e}")
            return False
    
    def _ping_loop(self):
        """Internal method that runs in the background thread"""
        logger.info(f"🚀 Ping service started - Pinging every {self.ping_interval//60} minutes")
        
        while self.running:
            try:
                self.ping_server()
                # Wait for the specified interval
                for _ in range(self.ping_interval):
                    if not self.running:  # Check if we should stop
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error in ping loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def start(self):
        """Start the ping service in a background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._ping_loop, daemon=True)
            self.thread.start()
            logger.info("🔄 Ping service thread started")
    
    def stop(self):
        """Stop the ping service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ Ping service stopped")

# Global instance
ping_service = None

def start_ping_service(app_url):
    """Start the ping service with the given app URL"""
    global ping_service
    if ping_service:
        ping_service.stop()
    
    ping_service = RenderPingService(app_url)
    ping_service.start()
    return ping_service

def stop_ping_service():
    """Stop the ping service"""
    global ping_service
    if ping_service:
        ping_service.stop()
        ping_service = None

if __name__ == "__main__":
    # For testing standalone
    SERVICE_URL = "https://dhi-lms-lk64.onrender.com"
    service = RenderPingService(SERVICE_URL)
    
    try:
        service.start()
        # Keep the main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping ping service...")
        service.stop()
        print("✅ Ping service stopped")
