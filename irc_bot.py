import socket
import re
import config
from flood_protection import FloodProtection
from filtered_nicks import BAD_NICKNAMES
from filtered_words import FILTERED_WORDS

# Function to strip IRC control codes (color codes, bold, underline, etc.)
def strip_control_codes(message):
    # IRC Control codes regex (covers color, bold, underline, reverse, etc.)
    control_code_regex = re.compile(r'(\x03\d{0,2}(,\d{1,2})?)|[\x02\x1F\x16\x0F]')
    return control_code_regex.sub('', message)

class IRCBot:
    def __init__(self):
        self.server = config.IRC_SERVER
        self.port = config.IRC_PORT
        self.channel = config.IRC_CHANNEL
        self.nickname = config.NICKNAME
        self.realname = config.REALNAME
        self.ident = config.IDENT
        self.password = config.PASSWORD
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flood_protection_enabled = config.FLOOD_PROTECTION_ENABLED.get(self.channel, True)
        self.flood_protection = FloodProtection()

        # Tracking flood offenses
        self.user_offenses = {}

    def connect(self):
        self.irc.connect((self.server, self.port))
        if self.password:
            self.send_command(f"PASS {self.password}")
        self.send_command(f"NICK {self.nickname}")
        self.send_command(f"USER {self.ident} 0 * :{self.realname}")
        self.send_command(f"JOIN {self.channel}")
    
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

                if self.flood_protection_enabled:
                    if self.flood_protection.check_flood(user, self.channel):
                        self.handle_flood(user)

                # Parse commands based on sanitized message
                if sanitized_message.startswith(":op"):
                    self.op_user(user)
                elif sanitized_message.startswith(":deop"):
                    self.deop_user(user)
                elif sanitized_message.startswith(":voice"):
                    self.voice_user(user)
                elif sanitized_message.startswith(":devoice"):
                    self.devoice_user(user)
                elif sanitized_message.startswith(":kick"):
                    self.kick_user(user, sanitized_message.split()[1], "[auto] You've been kicked for flooding.")
                elif sanitized_message.startswith(":ban"):
                    self.ban_user(user, sanitized_message.split()[1])
                elif sanitized_message.startswith(":shun"):
                    self.shun_user(user, sanitized_message.split()[1])

            # Check for bad nicknames on user join
            if "JOIN" in response:
                user_nick = response.split('!')[0][1:]
                if user_nick in BAD_NICKNAMES:
                    self.kick_user(self.nickname, user_nick, "[auto] Bad nickname detected.")
                    self.send_message(user_nick, "Your nickname is not allowed. Please choose a different one.")

    def handle_flood(self, user):
        if user not in self.user_offenses:
            self.user_offenses[user] = 1
            self.send_message(self.channel, f"[auto] {user}: Warning! You are sending messages too quickly.")
        elif self.user_offenses[user] == 1:
            self.kick_user(self.nickname, user, "[auto] You've been kicked for flooding.")
            self.user_offenses[user] += 1
        elif self.user_offenses[user] == 2:
            self.ban_user(self.nickname, user)

    def op_user(self, user):
        self.send_command(f"MODE {self.channel} +o {user}")

    def deop_user(self, user):
        self.send_command(f"MODE {self.channel} -o {user}")

    def voice_user(self, user):
        self.send_command(f"MODE {self.channel} +v {user}")

    def devoice_user(self, user):
        self.send_command(f"MODE {self.channel} -v {user}")

    def kick_user(self, user, target, reason):
        self.send_command(f"KICK {self.channel} {target} :{reason}")

    def ban_user(self, user, target):
        self.send_command(f"MODE {self.channel} +b {target}")
        self.kick_user(user, target, "[auto] You've been banned for repeated offenses.")

    def shun_user(self, user, target):
        self.send_command(f"MODE {self.channel} +q {target}")

if __name__ == "__main__":
    bot = IRCBot()
    bot.connect()
    bot.listen()
