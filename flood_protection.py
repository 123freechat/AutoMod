# flood_protection.py
import time

class FloodProtection:
    def __init__(self, limit=7, interval=5):
        self.limit = limit
        self.interval = interval
        self.user_messages = {}

    def check_flood(self, user, channel):
        current_time = time.time()

        if channel not in self.user_messages:
            self.user_messages[channel] = {}

        if user not in self.user_messages[channel]:
            self.user_messages[channel][user] = []

        # Remove messages older than interval
        self.user_messages[channel][user] = [timestamp for timestamp in self.user_messages[channel][user] if current_time - timestamp < self.interval]

        # Add the current message timestamp
        self.user_messages[channel][user].append(current_time)

        if len(self.user_messages[channel][user]) > self.limit:
            return True
        return False

    def reset_user(self, user, channel):
        if channel in self.user_messages and user in self.user_messages[channel]:
            del self.user_messages[channel][user]
