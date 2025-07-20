import esl
import time
import os
import logging
from threading import Thread

# --- Configuration ---
# Get connection details from environment variables for Docker best practices
FS_HOST = os.environ.get("FS_HOST", "127.0.0.1")
FS_PORT = int(os.environ.get("FS_PORT", 8021))
FS_PASSWORD = os.environ.get("FS_PASSWORD", "ClueCon")

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "call_log.txt")

# --- Setup Logging ---
# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Also print to console
    ]
)

# --- Call State Tracker ---
# This dictionary will hold information about active calls
active_calls = {}

def process_events(connection):
    """
    Subscribes to events and processes them in a loop.
    This function runs in a separate thread.
    """
    # Subscribe to all events. We will filter for the ones we need.
    connection.events("plain", "all")
    
    logging.info("Successfully connected to FreeSWITCH ESL and subscribed to events.")

    while True:
        try:
            # Receive an event
            event = connection.recvEvent()
            if not event:
                continue

            event_name = event.getHeader("Event-Name")
            unique_id = event.getHeader("Channel-Unique-ID")
            
            if not unique_id:
                continue

            # --- Event Handling Logic ---

            if event_name == "CHANNEL_CREATE":
                # A new call leg is created. This is our start time.
                caller = event.getHeader("Caller-Caller-ID-Number")
                callee = event.getHeader("Caller-Destination-Number")
                
                if callee: # We only care about outbound call legs initially
                    active_calls[unique_id] = {
                        "start_time": time.time(),
                        "from": caller,
                        "to": callee
                    }
                    logging.info(f"Call Initiated: {unique_id} | From: {caller} | To: {callee}")

            elif event_name == "CHANNEL_ANSWER":
                # The call has been answered.
                if unique_id in active_calls:
                    active_calls[unique_id]["answer_time"] = time.time()
                    logging.info(f"Call Answered: {unique_id}")

            elif event_name == "CHANNEL_HANGUP_COMPLETE":
                # The call has ended.
                if unique_id in active_calls:
                    active_calls[unique_id]["end_time"] = time.time()
                    logging.info(f"Call Ended: {unique_id}")
                    # Clean up the completed call from our tracker
                    del active_calls[unique_id]
        
        except (esl.eslNotConnectedError, BrokenPipeError, AttributeError):
            logging.error("Lost connection to FreeSWITCH ESL. Exiting thread.")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in event processor: {e}")


def main():
    """
    Main function to handle connection and reconnection logic.
    """
    while True:
        con = esl.ESLconnection(FS_HOST, FS_PORT, FS_PASSWORD)
        logging.info(f"Attempting to connect to FreeSWITCH at {FS_HOST}:{FS_PORT}...")

        if con.connected():
            # Start the event processing in a separate thread
            event_thread = Thread(target=process_events, args=(con,))
            event_thread.daemon = True
            event_thread.start()
            
            # Keep the main thread alive to monitor the connection
            while event_thread.is_alive():
                time.sleep(1)
        else:
            logging.error("Connection failed. Retrying in 5 seconds...")
        
        del con
        time.sleep(5)

if __name__ == "__main__":
    main()
