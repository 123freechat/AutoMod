# flood_protection.py
import time

class FloodProtection:
    def __init__(self, limit=7, interval=5):
        self.limit = limit
        self.interval = interval
        self.user_messages = {}

    def check_flood(self, user, channel):
        current_time = time.time()

        if user not in self.user_messages:
            self.user_messages[user] = []

        # Remove messages older than interval
        self.user_messages[user] = [timestamp for timestamp in self.user_messages[user] if current_time - timestamp < self.interval]

        # Add the current message timestamp
        self.user_messages[user].append(current_time)

        if len(self.user_messages[user]) > self.limit:
            return True
        return False

    def reset_user(self, user):
        if user in self.user_messages:
            del self.user_messages[user]
