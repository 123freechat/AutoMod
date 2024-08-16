AutoMod IRC Bot with Flood Protection
-
This IRC bot is written in Python and includes flood protection features. It allows each channel to toggle flood protection on or off, warning users after 7 messages in under 5 seconds, kicking them on the second offense, and banning them on the third offense.

Features
Basic IRC commands: Supports :op, :deop, :voice, :devoice, :kick, :ban, and :shun.
Flood protection: Configurable for each channel. Warns, kicks, and bans users who exceed the message limit.

Prerequisites
Python 3.x installed on your system.
A code editor or IDE (e.g., Visual Studio Code, PyCharm) is recommended but not necessary.


Installation
-
Step 1: Clone the Repository

git clone https://github.com/123freechat/AutoMod.git
cd AutoMod

Configuration
-
Step 2: Configure the Bot
Edit the config.py file with your IRC server information:

# config.py

IRC_SERVER = "irc.example.com"  # Replace with your IRC server
IRC_PORT = 6667  # Replace with your IRC port if different
IRC_CHANNEL = "#yourchannel"  # Replace with your IRC channel
NICKNAME = "YourBot"  # Replace with your desired bot nickname
REALNAME = "Your Realname"  # Replace with your real name
IDENT = "yourbot"  # Replace with your bot ident
PASSWORD = "yourpassword"  # Replace with your password if needed, otherwise leave as None

# Flood protection configuration
FLOOD_PROTECTION_ENABLED = {
    "#yourchannel": True,  # Set to False if you want to disable flood protection for this channel
}

Step 3: Run the Bot
Navigate to the directory where the bot is located and run the following command:

python3 irc_bot.py
The bot will connect to the IRC server and begin listening for commands.

Usage
-
Once the bot is running, you can use the following commands in the IRC channel:

:op <user>: Give operator status to a user.
:deop <user>: Remove operator status from a user.
:voice <user>: Give voice status to a user.
:devoice <user>: Remove voice status from a user.
:kick <user>: Kick a user from the channel.
:ban <user>: Ban a user from the channel.
:shun <user>: Shun (silence) a user in the channel.

Flood Protection
Flood protection is enabled by default for each channel listed in config.py. If a user sends more than 7 messages within 5 seconds:

They will receive a warning.
On a second offense, they will be kicked from the channel.
On a third offense, they will be banned.
You can toggle flood protection on or off for specific channels by editing the FLOOD_PROTECTION_ENABLED dictionary in config.py.

Troubleshooting
-
Ensure you have Python 3.x installed.
Check that your IRC server information in config.py is correct.
If the bot doesn't connect, ensure your network allows outbound connections to the IRC server.
Contributing
Feel free to contribute to this project by submitting issues or pull requests on GitHub.

<a href="https://www.123freechat.com">123FreeChat.com</a> is where you can see the bot in full action. For IRC irc.123freechat.com:+6697 or standard 6667 for non-SSL connections. 

License
-
This project is licensed under the MIT License.
