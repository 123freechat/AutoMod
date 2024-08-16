# config.py

IRC_SERVER = "irc.example.com"
IRC_PORT = 6667
DEFAULT_CHANNEL = "#yourchannel"  # Replace with the default channel you want the bot to join
NICKNAME = "YourBot"
REALNAME = "Your Realname"
IDENT = "yourbot"
PASSWORD = "yourpassword"  # If required, otherwise leave as None

# Flood protection configuration
FLOOD_PROTECTION_ENABLED = {
    "#yourchannel": True,  # Set to False if you want to disable flood protection for this channel
}
