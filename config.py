# config.py

IRC_SERVER = "irc.example.com"
IRC_PORT = 6667
IRC_CHANNEL = "#yourchannel"
NICKNAME = "YourBot"
REALNAME = "Your Realname"
IDENT = "yourbot"
PASSWORD = "yourpassword"  # If required, otherwise leave it as None

# Flood protection configuration
FLOOD_PROTECTION_ENABLED = {
    "#yourchannel": True,  # You can set this to False to disable flood protection
}
