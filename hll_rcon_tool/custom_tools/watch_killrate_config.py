"""
watch_killrate_config.py

A plugin for Hell Let Loose (HLL) CRCON
(see : https://github.com/MarechJ/hll_rcon_tool)
that watches and report players who get "too much" kills per minute. 

Source : https://github.com/ElGuillermo

Feel free to use/modify/distribute, as long as you keep this note in your code
"""

# Discord embeds strings translations
# Available : 0 for english, 1 for french, 2 for german
LANG = 0

# Send a Discord message if the player gets more kills/minute than this number
# 1.0+ = "good" (legit) new players
# 1.5+ = artillery and machinegun players
# 2.0+ = "good" (legit) veterans players
# 2.5+ = competitive (legit) players
# 3.0+ = consider this is almost a cheat proof if sustained for 15+ minutes
# Default : 2.5
KILLRATE_THRESHOLD = 2.5

# Dedicated Discord's channel webhook
# ServerNumber, Webhook, Enabled
SERVER_CONFIG = [
    ["https://discord.com/api/webhooks/...", True],  # Server 1
    ["https://discord.com/api/webhooks/...", False],  # Server 2
    ["https://discord.com/api/webhooks/...", False],  # Server 3
    ["https://discord.com/api/webhooks/...", False],  # Server 4
    ["https://discord.com/api/webhooks/...", False],  # Server 5
    ["https://discord.com/api/webhooks/...", False],  # Server 6
    ["https://discord.com/api/webhooks/...", False],  # Server 7
    ["https://discord.com/api/webhooks/...", False],  # Server 8
    ["https://discord.com/api/webhooks/...", False],  # Server 9
    ["https://discord.com/api/webhooks/...", False]  # Server 10
]

# Don't log/send Discord message if the player has less than X kills
# Avoids to get any false alert
# (2 kills in 1 min could easily happen if the player enters the map midgame)
# Disable : 0
# Default : 10
MINIMUM_KILLS = 10

# You won't get Discord entries for the players having this flag(s) set on profile
# (they'll still be noted in logs)
# Use https://emojipedia.org/ to find the emoji that suits your needs
WHITELIST_FLAGS = ["🔕"]

# Some players can get a lot of kills in no time
# Set these to 'True' to disable warnings
# (they'll still be noted in logs)
WHITELIST_ARMOR = True
WHITELIST_ARTILLERY = True
WHITELIST_MG = False

# Avoid to trigger a Discord entry if no weapon has been used since last check
# Thus, it avoids being notified for artillery chargers
# (they'll still be noted in logs)
# Default : True
WHITELIST_NOWEAPON = True

# Miscellaneous (you don't have to change these)
# ----------------------------------------------

# The interval between watch turns (in seconds)
# Recommended : as the stats are to be gathered for all the players,
#               requiring a big amount of data from the game server,
#               you may encounter slowdowns if done too frequently.
# Recommended : not less than 120 secs (2 mins)
# Default : 180
WATCH_INTERVAL_SECS = 180

# Bot name that will be displayed in CRCON "audit logs" and Discord embeds
BOT_NAME = "CRCON_watch_killrate"
