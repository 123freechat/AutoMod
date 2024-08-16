import socket
import re
import sqlite3
import config
import db_config
from flood_protection import FloodProtection
from filtered_nicks import BAD_NICKNAMES
from filtered_words import FILTERED_WORDS

# Function to strip IRC control codes (color codes, bold, underline, etc.)
def strip_control_codes(message):
    control_code_regex = re.compile(r'(\x03\d{0,2}(,\d{1,2})?)|[\x02\x1F\x16\x0F]')
    return control_code_regex.sub('', message)

class IRCBot:
    def __init__(self):
        self.server = config.IRC_SERVER
        self.port = config.IRC_PORT
        self.default_channel = config.DEFAULT_CHANNEL
        self.nickname = config.NICKNAME
        self.realname = config.REALNAME
        self.ident = config.IDENT
        self.password = config.PASSWORD
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flood_protection_enabled = config.FLOOD_PROTECTION_ENABLED.get(self.default_channel, True)
        self.flood_protection = FloodProtection()

        # Tracking flood offenses and operator statuses
        self.user_offenses = {}
        self.operators = set()

        # Connect to the SQLite database
        self.conn = sqlite3.connect(db_config.DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Create tables if they don't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT UNIQUE,
                join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                messages_sent INTEGER DEFAULT 0,
                joins INTEGER DEFAULT 0,
                parts INTEGER DEFAULT 0,
                quits INTEGER DEFAULT 0,
                reputation REAL DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                violation_type TEXT,
                violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def connect(self):
        self.irc.connect((self.server, self.port))
        if self.password:
            self.send_command(f"PASS {self.password}")
        self.send_command(f"NICK {self.nickname}")
        self.send_command(f"USER {self.ident} 0 * :{self.realname}")
        self.send_command(f"JOIN {self.default_channel}")
    
    def send_command(self, command):
        self.irc.send(f"{command}\r\n".encode())
    
    def send_message(self, target, message):
        self.send_command(f"PRIVMSG {target} :{message}")
    
    def listen(self):
        while True:
            response = self.irc.recv(2048).decode()
            print(response)

            if response.startswith("PING"):
                self.send_command(f"PONG {response.split()[1]}")
            if "PRIVMSG" in response:
                user = response.split('!')[0][1:]
                message = response.split('PRIVMSG')[1].split(':')[1].strip()

                # Strip control codes from the message
                sanitized_message = strip_control_codes(message)

                # Track user stats
                self.track_user_stats(user, sanitized_message, action="message")

                if self.flood_protection_enabled:
                    if self.flood_protection.check_flood(user, self.default_channel):
                        self.handle_flood(user)

                # Check if the user is an operator in the channel
                if f"@{self.default_channel}" in response:
                    self.operators.add(user)
                elif f"+{self.default_channel}" in response:
                    self.operators.discard(user)

                # Commands for ops (moderators)
                if user in self.operators:
                    if sanitized_message.startswith(":op"):
                        self.op_user(sanitized_message.split()[1])
                    elif sanitized_message.startswith(":deop"):
                        self.deop_user(sanitized_message.split()[1])
                    elif sanitized_message.startswith(":voice"):
                        self.voice_user(sanitized_message.split()[1])
                    elif sanitized_message.startswith(":devoice"):
                        self.devoice_user(sanitized_message.split()[1])
                    elif sanitized_message.startswith(":kick"):
                        self.kick_user(user, sanitized_message.split()[1], "[auto] You've been kicked for flooding.")
                        self.track_user_stats(sanitized_message.split()[1], action="kick")
                    elif sanitized_message.startswith(":ban"):
                        self.ban_user(user, sanitized_message.split()[1])
                        self.track_user_stats(sanitized_message.split()[1], action="ban")
                    elif sanitized_message.startswith(":shun"):
                        self.shun_user(user, sanitized_message.split()[1])
                    elif sanitized_message.startswith(":join"):
                        self.join_channel(sanitized_message.split()[1])
                        self.track_user_stats(sanitized_message.split()[1], action="join")
                    elif sanitized_message.startswith(":part"):
                        self.part_channel(sanitized_message.split()[1])
                        self.track_user_stats(sanitized_message.split()[1], action="part")

            # Check for bad nicknames on user join
            if "JOIN" in response:
                user_nick = response.split('!')[0][1:]
                if user_nick in BAD_NICKNAMES:
                    self.kick_user(self.nickname, user_nick, "[auto] Bad nickname detected.")
                    self.send_message(user_nick, "Your nickname is not allowed. Please choose a different one.")
                else:
                    self.track_user_stats(user_nick, action="join")

            # Handle user quitting the channel
            if "QUIT" in response:
                user_nick = response.split('!')[0][1:]
                self.track_user_stats(user_nick, action="quit")

    def track_user_stats(self, nickname, message=None, action="message"):
        # Check if the user exists in the database
        self.cursor.execute('SELECT id, messages_sent, reputation FROM users WHERE nickname = ?', (nickname,))
        user = self.cursor.fetchone()

        if user:
            # Update stats based on the action
            if action == "message":
                self.cursor.execute('UPDATE users SET messages_sent = messages_sent + 1, reputation = reputation + 1 WHERE nickname = ?', (nickname,))
            elif action == "join":
                self.cursor.execute('UPDATE users SET joins = joins + 1, reputation = reputation + 1 WHERE nickname = ?', (nickname,))
            elif action == "part":
                self.cursor.execute('UPDATE users SET parts = parts + 1, reputation = reputation + 2 WHERE nickname = ?', (nickname,))
            elif action == "quit":
                self.cursor.execute('UPDATE users SET quits = quits + 1, reputation = reputation + 0.2 WHERE nickname = ?', (nickname,))
            elif action == "kick":
                self.cursor.execute('UPDATE users SET reputation = reputation - 1 WHERE nickname = ?', (nickname,))
            elif action == "ban":
                self.cursor.execute('UPDATE users SET reputation = reputation - 2 WHERE nickname = ?', (nickname,))
            elif action == "kill":
                self.cursor.execute('UPDATE users SET reputation = reputation - 5 WHERE nickname = ?', (nickname,))
            elif action == "gline":
                self.cursor.execute('UPDATE users SET reputation = reputation - 10 WHERE nickname = ?', (nickname,))
        else:
            # Insert new user
            if action in ["message", "join"]:
                reputation = 1
            elif action == "part":
                reputation = 2
            elif action == "quit":
                reputation = 0.2
            else:
                reputation = 0

            self.cursor.execute('INSERT INTO users (nickname, messages_sent, joins, parts, quits, reputation) VALUES (?, 1, 0, 0, 0, ?)', (nickname, reputation))

        self.conn.commit()

        # Check if user is disruptive (negative reputation)
        self.check_disruptive_user(nickname)

    def check_disruptive_user(self, nickname):
        # Get the user's reputation
        self.cursor.execute('SELECT reputation FROM users WHERE nickname = ?', (nickname,))
        reputation = self.cursor.fetchone()[0]

        if reputation < 0:
            # User is disruptive
            self.send_message(self.default_channel, f"[auto] {nickname} has been flagged as a disruptive chatter due to negative reputation.")
            # Additional actions for disruptive users can be implemented here

    def handle_flood(self, user):
        # Handle flood violations
        self.cursor.execute('SELECT id FROM users WHERE nickname = ?', (user,))
        user_id = self.cursor.fetchone()[0]

        if user not in self.user_offenses:
            self.user_offenses[user] = 1
            self.send_message(self.default_channel, f"[auto] {user}: Warning! You are sending messages too quickly.")
            # Insert violation
            self.cursor.execute('INSERT INTO violations (user_id, violation_type) VALUES (?, ?)', (user_id, 'flood'))
            self.track_user_stats(user, action="kick")  # Deduct points for flood warnings
        elif self.user_offenses[user] == 1:
            self.kick_user(self.nickname, user, "[auto] You've been kicked for flooding.")
            self.user_offenses[user] += 1
            # Insert violation
            self.cursor.execute('INSERT INTO violations (user_id, violation_type) VALUES (?, ?)', (user_id, 'flood'))
            self.track_user_stats(user, action="kick")
        elif self.user_offenses[user] == 2:
            self.ban_user(self.nickname, user)
            # Insert violation
            self.cursor.execute('INSERT INTO violations (user_id, violation_type) VALUES (?, ?)', (user_id, 'flood'))
            self.track_user_stats(user, action="ban")

        self.conn.commit()

    def op_user(self, user):
        self.send_command(f"MODE {self.default_channel} +o {user}")

    def deop_user(self, user):
        self.send_command(f"MODE {self.default_channel} -o {user}")

    def voice_user(self, user):
        self.send_command(f"MODE {self.default_channel} +v {user}")

    def devoice_user(self, user):
        self.send_command(f"MODE {self.default_channel} -v {user}")

    def kick_user(self, user, target, reason):
        self.send_command(f"KICK {self.default_channel} {target} :{reason}")

    def ban_user(self, user, target):
        self.send_command(f"MODE {self.default_channel} +b {target}")
        self.kick_user(user, target, "[auto] You've been banned for repeated offenses.")

    def shun_user(self, user, target):
        self.send_command(f"MODE {self.default_channel} +q {target}")

    def join_channel(self, channel):
        self.send_command(f"JOIN {channel}")

    def part_channel(self, channel):
        self.send_command(f"PART {channel}")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    bot = IRCBot()
    bot.connect()
    bot.listen()
    bot.close()
