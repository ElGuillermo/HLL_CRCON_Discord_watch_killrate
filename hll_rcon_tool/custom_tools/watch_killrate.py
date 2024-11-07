"""
watch_killrate.py

A plugin for HLL CRCON (https://github.com/MarechJ/hll_rcon_tool)
that watches and report players who get "too much" kills per minute.
(some strings are hardcoded in french, feel free to adapt them to your language)

Source : https://github.com/ElGuillermo

Feel free to use/modify/distribute, as long as you keep this note in your code
"""

from datetime import datetime, timedelta, timezone
import logging
from time import sleep
import discord
from rcon.game_logs import get_recent_logs
from rcon.rcon import Rcon
from rcon.player_history import get_player_profile, player_has_flag
from rcon.settings import SERVER_INFO
from rcon.utils import get_server_number
from custom_tools.custom_common import (
    DISCORD_EMBED_AUTHOR_URL,
    DISCORD_EMBED_AUTHOR_ICON_URL,
    WEAPONS_ARTILLERY,
    discord_embed_send,
    get_avatar_url,
    get_external_profile_url,
    green_to_red,
    team_view_stats
)
from custom_tools.custom_translations import TRANSL


# Configuration (you must review/change these !)
# -----------------------------------------------------------------------------

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
# Recommended : not less than 180 secs (3 mins)
# Default : 300
WATCH_INTERVAL_SECS = 300

# Bot name that will be displayed in CRCON "audit logs" and Discord embeds
BOT_NAME = "CRCON_watch_killrate"


# (End of configuration)
# -----------------------------------------------------------------------------


def watch_killrate_loop():
    """
    Calls the function that gathers data,
    then calls the function to analyze it.
    """
    rcon = Rcon(SERVER_INFO)
    (
        _,
        _,
        _,
        all_infantry_players,
        _,
        _,
        _
    ) = team_view_stats(rcon)

    if len(all_infantry_players) > 1:
        watch_killrate(all_infantry_players)
    else:
        logger.info("Less than 2 players ingame, waiting for %s mins", WATCH_INTERVAL_SECS / 60)


def watch_killrate(
        watched_players: list
    ):
    """
    Find the players whose kills per minute is over threshold
    Send a report to Discord if found
    """
    # Get elapsed match time
    mins_since_match_start = 1  # Default value
    logs_match_start = get_recent_logs(
        action_filter=["MATCH START"],
        exact_action=True  # Default : False
    )
    match_start_timestamp = logs_match_start["logs"][0]["timestamp_ms"] / 1000
    mins_since_match_start = (
        datetime.now() - datetime.fromtimestamp(match_start_timestamp)
    ).total_seconds() / 60

    # Test the infantry players (armor won't be tested)
    if mins_since_match_start > 2:  # Avoids inconsistent scores at the beginning of the game

        for player in watched_players:

            # Don't test player if (s)he has connected less than WATCH_INTERVAL_SECS ago
            mins_since_connected = player["profile"]["current_playtime_seconds"] / 60
            if mins_since_connected < (WATCH_INTERVAL_SECS / 60) :
                continue  # Avoids inconsistent scores

            # Calculate killrate
            kills_per_minute = round(
                (player["kills"] / min(mins_since_match_start, mins_since_connected)), 2
            )

            if kills_per_minute > KILLRATE_THRESHOLD:

                # latest kills weapons (since last watch iteration)
                time_now_minus_interval = (
                    datetime.now(timezone.utc) - timedelta(seconds=WATCH_INTERVAL_SECS)
                )
                time_now_minus_interval_int = int(time_now_minus_interval.timestamp())
                logs = get_recent_logs(
                    # start=0,  # Default : 0
                    end=500,  # Default : 100000
                    player_search=player["name"],
                    action_filter=["KILL"],
                    min_timestamp=time_now_minus_interval_int,
                    exact_player_match=True,  # Default : False
                    exact_action=True,  # Default : False
                    # inclusive_filter=True,  # Default : True
                )
                weapons = []
                for log in logs["logs"]:
                    if (
                        log["player_name_1"] == player["name"]
                        and not log["weapon"] in weapons
                    ):
                        weapons.append(log["weapon"])

                # Log (whitelisted flag on player's profile)
                whitelist_flag_present = False
                try:
                    profile = get_player_profile(player["player_id"], 0)
                    for flag in WHITELIST_FLAGS:
                        if player_has_flag(profile, flag):
                            whitelist_flag_present = True
                except :
                    logger.warning("Unable to check player profile for flags")

                if whitelist_flag_present:
                    logger.info(
                        "(whitelist flag) '%s' - %s/%s/%s "
                        "- Level : %s - %s kills in %s minutes (%s kill/min). "
                        "Last used weapon(s) : %s",
                        player["name"],
                        TRANSL[player["team"]][LANG],
                        player["unit_name"],
                        TRANSL[player["role"]][LANG],
                        player["level"],
                        player["kills"],
                        round(min(mins_since_match_start, mins_since_connected), 2),
                        kills_per_minute,
                        ', '.join(weapons)
                    )
                    continue

                # Log (whitelisted artillery player)
                if WHITELIST_ARTILLERY:
                    if any(weapon in weapons for weapon in WEAPONS_ARTILLERY):
                        logger.info(
                            "(whitelisted - artillery) '%s' - %s/%s/%s "
                            "- Level : %s - %s kills in %s minutes (%s kill/min). "
                            "Last used weapon(s) : %s",
                            player["name"],
                            TRANSL[player["team"]][LANG],
                            player["unit_name"],
                            TRANSL[player["role"]][LANG],
                            player["level"],
                            player["kills"],
                            round(min(mins_since_match_start, mins_since_connected), 2),
                            kills_per_minute,
                            ', '.join(weapons)
                        )
                        continue

                # Log (non-whitelisted player)
                logger.info(
                    "'%s' - %s/%s/%s "
                    "- Level : %s - %s kills in %s minutes (%s kill/min). "
                    "Last used weapon(s) : %s",
                    player["name"],
                    TRANSL[player["team"]][LANG],
                    player["unit_name"],
                    TRANSL[player["role"]][LANG],
                    player["level"],
                    player["kills"],
                    round(min(mins_since_match_start, mins_since_connected), 2),
                    kills_per_minute,
                    ', '.join(weapons)
                )

                # TODO : Flag the player

                # Discord
                # Check if enabled
                server_number = int(get_server_number())
                if not SERVER_CONFIG[server_number - 1][1]:
                    return
                discord_webhook = SERVER_CONFIG[server_number - 1][0]

                if player["team"] == "axis":
                    team_symbol = "🟥"
                elif player["team"] == "allies":
                    team_symbol = "🟦"

                embed_desc_txt = (
                    f"{team_symbol} {TRANSL[player['team']][LANG]} "
                    f"/ {player['unit_name']} "
                    f"/ {TRANSL[player['role']][LANG]}\n"
                    f"{player['kills']} kills "
                    f"/ {round(min(mins_since_match_start, mins_since_connected), 2)} min. "
                    f"(**{kills_per_minute} kill/min**)\n"
                    f"**{TRANSL['level'][LANG]} :** {player['level']}\n"
                    f"**{TRANSL['lastusedweapons'][LANG]} :\n** {', '.join(weapons)}"
                )

                embed_color = green_to_red(
                    kills_per_minute, min_value=KILLRATE_THRESHOLD, max_value=2
                )

                # Create and send Discord embed
                webhook = discord.SyncWebhook.from_url(discord_webhook)
                embed = discord.Embed(
                    title=player["name"],
                    url=get_external_profile_url(player["player_id"], player["name"]),
                    description=embed_desc_txt,
                    color=embed_color
                )
                embed.set_author(
                    name=BOT_NAME,
                    url=DISCORD_EMBED_AUTHOR_URL,
                    icon_url=DISCORD_EMBED_AUTHOR_ICON_URL
                )
                embed.set_thumbnail(url=get_avatar_url(player["player_id"]),)

                discord_embed_send(embed, webhook)


# Launching - initial pause : wait to be sure the CRCON is fully started
sleep(60)

logger = logging.getLogger('rcon')

logger.info(
    "\n-------------------------------------------------------------------------------\n"
    "%s (started)\n"
    "-------------------------------------------------------------------------------",
    BOT_NAME
)

# Launching and running (infinite loop)
if __name__ == "__main__":
    while True:
        watch_killrate_loop()
        sleep(WATCH_INTERVAL_SECS)
