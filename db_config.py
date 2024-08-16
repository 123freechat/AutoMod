# db_config.py

# SQLite Configuration (for simplicity)
DB_PATH = 'irc_bot.db'  # Path to your SQLite database file

# If you want to switch to MySQL or PostgreSQL, you can configure the following options:
DB_TYPE = 'sqlite'  # Options: 'sqlite', 'mysql', 'postgresql'

# For MySQL/PostgreSQL (ignored if using SQLite)
DB_HOST = 'localhost'   # Database host
DB_USER = 'yourusername'  # Database username
DB_PASSWORD = 'yourpassword'  # Database password
DB_NAME = 'yourdatabase'  # Database name
