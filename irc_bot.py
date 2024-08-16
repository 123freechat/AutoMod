import socket
import config
from flood_protection import FloodProtection

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
    
    def send_message(self, message):
        self.send_command(f"PRIVMSG {self.channel} :{message}")
    
    def listen(self):
        while True:
            response = self.irc.recv(2048).decode()
            print(response)

            if response.startswith("PING"):
                self.send_command(f"PONG {response.split()[1]}")
            if "PRIVMSG" in response:
                user = response.split('!')[0][1:]
                message = response.split('PRIVMSG')[1].split(':')[1].strip()

                if self.flood_protection_enabled:
                    if self.flood_protection.check_flood(user, self.channel):
                        self.handle_flood(user)

                # Parse commands
                if message.startswith(":op"):
                    self.op_user(user)
                elif message.startswith(":deop"):
                    self.deop_user(user)
                elif message.startswith(":voice"):
                    self.voice_user(user)
                elif message.startswith(":devoice"):
                    self.devoice_user(user)
                elif message.startswith(":kick"):
                    self.kick_user(user, message.split()[1])
                elif message.startswith(":ban"):
                    self.ban_user(user, message.split()[1])
                elif message.startswith(":shun"):
                    self.shun_user(user, message.split()[1])

    def handle_flood(self, user):
        if user not in self.user_offenses:
            self.user_offenses[user] = 1
            self.send_message(f"{user}: Warning! You are sending messages too quickly.")
        elif self.user_offenses[user] == 1:
            self.kick_user(self.nickname, user)
            self.user_offenses[user] += 1
        elif self.user_offenses[user] == 2:
            self.ban_user(self.nickname, user)
            self.user_offenses[user] = 0  # Reset after ban

    def op_user(self, user):
        self.send_command(f"MODE {self.channel} +o {user}")

    def deop_user(self, user):
        self.send_command(f"MODE {self.channel} -o {user}")

    def voice_user(self, user):
        self.send_command(f"MODE {self.channel} +v {user}")

    def devoice_user(self, user):
        self.send_command(f"MODE {self.channel} -v {user}")

    def kick_user(self, user, target):
        self.send_command(f"KICK {self.channel} {target} :Requested by {user}")

    def ban_user(self, user, target):
        self.send_command(f"MODE {self.channel} +b {target}")
        self.kick_user(user, target)

    def shun_user(self, user, target):
        self.send_command(f"MODE {self.channel} +q {target}")

if __name__ == "__main__":
    bot = IRCBot()
    bot.connect()
    bot.listen()
