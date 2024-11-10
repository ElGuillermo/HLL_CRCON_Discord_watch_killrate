"""
watch_killrate_config

A plugin for HLL CRCON (https://github.com/MarechJ/hll_rcon_tool)
that filters (kick) players based upon their language.

Source : https://github.com/ElGuillermo

Feel free to use/modify/distribute, as long as you keep this note in your code
"""

# Discord embeds strings translations
# Available : 0 for english, 1 for french, 2 for german
LANG = 0

# Send a Discord message if the player gets more kills/minute than this number
# 1.0 = "good" (legit) players
# 1.5 = artillery and machinegun players
# 1.5+ = competitive players
# 2.0+ = consider this is almost a cheat proof
# Default : 1.4
KILLRATE_THRESHOLD = 1.4

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

# You won't get Discord entries for the players having this flag(s) set on profile
# (they'll still be noted in logs)
# Use https://emojipedia.org/ to find the emoji that suits your needs
WHITELIST_FLAGS = ["🔕"]

# Artillery players can get a lot of kills in no time
# Set this to 'True' to disable warnings on these
# (they'll still be noted in logs)
# Default : True
WHITELIST_ARTILLERY = True


# Miscellaneous (you don't have to change these)
# ----------------------------------------------

# The interval between watch turns (in seconds)
# Recommended : as the stats are to be gathered for all the players,
#               requiring a big amount of data from the game server,
#               you may encounter slowdowns if done too frequently.
# Recommended : not less than 120 secs (2 mins)
# Default : 120
WATCH_INTERVAL_SECS = 120

# Bot name that will be displayed in CRCON "audit logs" and Discord embeds
BOT_NAME = "CRCON_watch_killrate"
