import socket
import ssl
import re
import sqlite3
import pymysql
import psycopg2
import config
import db_config
from flood_protection import FloodProtection
from filtered_nicks import BAD_NICKNAMES
from filtered_words import FILTERED_WORDS
import commands  # Import the command handling functions

# Function to strip IRC control codes (color codes, bold, underline, etc.)
def strip_control_codes(message):
    control_code_regex = re.compile(r'(\x03\d{0,2}(,\d{1,2})?)|[\x02\x1F\x16\x0F]')
    return control_code_regex.sub('', message)

class IRCBot:
    def __init__(self):
        self.server = config.IRC_SERVER
        self.port = config.IRC_PORT
        self.nickname = config.NICKNAME
        self.realname = config.REALNAME
        self.ident = config.IDENT
        self.password = config.PASSWORD
        self.help_channel = config.HELP_CHANNEL  # Help channel defined in the config
        self.use_ssl = config.USE_SSL  # Check if SSL should be used
        self.flood_protection_status = {}  # Track flood protection status per channel
        self.flood_protection = FloodProtection()

        # Tracking flood offenses and operator statuses
        self.user_offenses = {}
        self.operators = set()
        self.verification_queue = {}  # Queue for storing actions during NickServ verification
        self.privileges_confirmed = False  # Ensure privileges are confirmed before tracking

        # Connect to the appropriate database
        if db_config.DB_TYPE == 'sqlite':
            self.conn = sqlite3.connect(db_config.DB_PATH)
        elif db_config.DB_TYPE == 'mysql':
            self.conn = pymysql.connect(
                host=db_config.DB_HOST,
                user=db_config.DB_USER,
                password=db_config.DB_PASSWORD,
                database=db_config.DB_NAME
            )
        elif db_config.DB_TYPE == 'postgresql':
            self.conn = psycopg2.connect(
                host=db_config.DB_HOST,
                user=db_config.DB_USER,
                password=db_config.DB_PASSWORD,
                dbname=db_config.DB_NAME
            )
        else:
            raise ValueError("Unsupported DB_TYPE in db_config.py")

        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Create tables if they don't exist (Adjust syntax if not using SQLite)
        if db_config.DB_TYPE == 'sqlite':
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT UNIQUE,
                    join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    messages_sent INTEGER DEFAULT 0,
                    joins INTEGER DEFAULT 0,
                    parts INTEGER DEFAULT 0,
                    quits INTEGER DEFAULT 0,
                    reputation REAL DEFAULT 0,
                    ip_address TEXT
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
        else:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    nickname VARCHAR(255) UNIQUE,
                    join_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    messages_sent INTEGER DEFAULT 0,
                    joins INTEGER DEFAULT 0,
                    parts INTEGER DEFAULT 0,
                    quits INTEGER DEFAULT 0,
                    reputation REAL DEFAULT 0,
                    ip_address VARCHAR(255)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    violation_type VARCHAR(255),
                    violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

        self.conn.commit()

    def connect(self):
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.use_ssl:
            context = ssl.create_default_context()
            self.irc = context.wrap_socket(raw_socket, server_hostname=self.server)
        else:
            self.irc = raw_socket

        self.irc.connect((self.server, self.port))
        
        if self.password:
            self.send_command(f"PASS {self.password}")
        self.send_command(f"NICK {self.nickname}")
        self.send_command(f"USER {self.ident} 0 * :{self.realname}")
        self.send_command(f"JOIN {self.help_channel}")  # Join the help channel
    
    def send_command(self, command):
        self.irc.send(f"{command}\r\n".encode())
    
    def send_message(self, target, message):
        self.send_command(f"PRIVMSG {target} :{message}")
    
    def check_privileges(self):
        # Send a WHOIS or IDENT command to verify the bot's privileges
        self.send_command(f"WHOIS {self.nickname}")
    
    def listen(self):
        while True:
            response = self.irc.recv(2048).decode()
            print(response)

            if response.startswith("PING"):
                self.send_command(f"PONG {response.split()[1]}")
            if "PRIVMSG" in response:
                user = response.split('!')[0][1:]
                channel = response.split('PRIVMSG')[1].split(':')[0].strip()  # Get the channel
                message = response.split('PRIVMSG')[1].split(':')[1].strip()

                # Strip control codes from the message
                sanitized_message = strip_control_codes(message)

                # If privileges are confirmed, start tracking user stats
                if self.privileges_confirmed:
                    if user in self.verification_queue:
                        self.verification_queue[user].append((channel, sanitized_message))
                    else:
                        self.track_user_stats(user, sanitized_message, action="message")

                # Handle commands
                command = sanitized_message.split()
                if sanitized_message.startswith(":op"):
                    commands.handle_op(self, channel, user, command[1])
                elif sanitized_message.startswith(":deop"):
                    commands.handle_deop(self, channel, user, command[1])
                elif sanitized_message.startswith(":voice"):
                    commands.handle_voice(self, channel, user, command[1])
                elif sanitized_message.startswith(":devoice"):
                    commands.handle_devoice(self, channel, user, command[1])
                elif sanitized_message.startswith(":kick"):
                    commands.handle_kick(self, channel, user, command[1])
                elif sanitized_message.startswith(":ban"):
                    commands.handle_ban(self, channel, user, command[1])
                elif sanitized_message.startswith(":shun"):
                    commands.handle_shun(self, channel, user, command[1])
                elif sanitized_message.startswith(":join"):
                    commands.handle_join(self, channel, user, command[1])
                elif sanitized_message.startswith(":part"):
                    commands.handle_part(self, channel, user, command[1])
                elif sanitized_message.startswith(":floodpro"):
                    commands.handle_floodpro(self, channel, user, command)
                elif sanitized_message.startswith(":userstat"):
                    commands.handle_userstat(self, channel, user, command)

            # Check for bad nicknames on user join
            if "JOIN" in response:
                user_nick = response.split('!')[0][1:]
                channel = response.split('JOIN :')[1].strip()  # Get the channel
                if self.privileges_confirmed:
                    self.send_command(f"WHOIS {user_nick}")

            # Handle user quitting the channel
            if "QUIT" in response:
                user_nick = response.split('!')[0][1:]
                if self.privileges_confirmed:
                    self.track_user_stats(user_nick, action="quit")

            # Handle WHOIS and NickServ identification check
            if "NOTICE" in response and "NickServ" in response:
                nickserv_response = response.split(":")[2].strip()
                user_nick = response.split('!')[0][1:]
                if "is not registered" in nickserv_response:
                    self.send_message(self.help_channel, f"[auto] Notice: Unregistered users must register to track stats for prizes and rewards.")
                elif "has identified" in nickserv_response:
                    # User is verified, process queued actions
                    if user_nick in self.verification_queue:
                        for channel, action in self.verification_queue[user_nick]:
                            self.track_user_stats(user_nick, action=action)
                        del self.verification_queue[user_nick]  # Clear the queue
                elif "End of WHOIS" in response:
                    # Once WHOIS confirms bot's identity, start tracking and syncing
                    if user_nick == self.nickname:
                        self.privileges_confirmed = True
                        self.sync_database()

    def sync_database(self):
        # Perform a sync with the database to ensure consistency
        self.cursor.execute('SELECT nickname FROM users')
        stored_nicknames = {row[0] for row in self.cursor.fetchall()}

        # Fetch the list of users currently in the channel (this is just an example)
        # This would require an additional IRC command to fetch the list of users
        # For now, let's assume we have a function that fetches this
        current_users = self.get_current_channel_users()

        # Add any missing users to the database
        for user in current_users:
            if user not in stored_nicknames:
                self.cursor.execute('INSERT INTO users (nickname) VALUES (?)', (user,))
                self.conn.commit()

        print("Database sync complete.")

    def get_current_channel_users(self):
        # This function should return a list of users currently in the channel
        # In reality, you'd need to issue an IRC command to get this list
        # For simplicity, returning a static list here
        return ["user1", "user2", "user3"]

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    bot = IRCBot()
    bot.connect()
    bot.listen()
    bot.close()
