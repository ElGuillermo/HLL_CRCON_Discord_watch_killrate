"""
watch_killrate

A plugin for HLL CRCON (https://github.com/MarechJ/hll_rcon_tool)
that watches and report players who get "too much" kills per minute.

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
from custom_tools.common_functions import (
    DISCORD_EMBED_AUTHOR_URL,
    DISCORD_EMBED_AUTHOR_ICON_URL,
    WEAPONS_ARTILLERY,
    discord_embed_send,
    get_avatar_url,
    get_external_profile_url,
    green_to_red,
    team_view_stats
)
from custom_tools.common_translations import TRANSL
from custom_tools.watch_killrate_config import *


def watch_killrate_loop():
    """
    Calls the function that gathers data,
    then calls the function to analyze it.
    """
    rcon = Rcon(SERVER_INFO)
    (
        _,
        _,  # all_players
        _,
        all_infantry_players,  # Armor won't be tested
        _,
        _,
        _
    ) = team_view_stats(rcon)

    if len(all_infantry_players) > 1:
        watch_killrate(all_infantry_players)
    else:
        logger.info(
            "Less than 2 players ingame, waiting for %s mins",
            round((WATCH_INTERVAL_SECS / 60), 2)
        )


def watch_killrate(
        watched_players: list
    ):
    """
    Find the players whose kills per minute is over threshold
    Send a report to Discord if found
    """
    # Get elapsed match time
    mins_since_match_start = 1
    logs_match_start = get_recent_logs(
        action_filter=["MATCH START"],
        exact_action=True
    )
    match_start_timestamp = logs_match_start["logs"][0]["timestamp_ms"] / 1000
    mins_since_match_start = (
        datetime.now() - datetime.fromtimestamp(match_start_timestamp)
    ).total_seconds() / 60

    # Avoids weird data returned at the beginning of the game
    if mins_since_match_start < 2:
        return

    # Test the players
    for player in watched_players:

        mins_since_connected = int(player["profile"]["current_playtime_seconds"]) / 60
        mins_from_offdef = (int(player["offense"]) + int(player["defense"])) / 20

        # Don't test player : connected less than WATCH_INTERVAL_SECS ago
        if mins_since_connected < (WATCH_INTERVAL_SECS / 60) :
            continue

        # Don't test player : no kills yet
        if int(player["kills"]) == 0:
            continue

        # Don't test player : not been on map for at least a minute
        if mins_from_offdef == 0:
            continue

        kills_per_minute = int(player["kills"]) / mins_from_offdef

        if kills_per_minute > KILLRATE_THRESHOLD:

            # latest kills weapons (since last watch iteration)
            time_now_minus_interval = (
                datetime.now(timezone.utc) - timedelta(seconds=WATCH_INTERVAL_SECS)
            )
            logs = get_recent_logs(
                end=500,
                player_search=player["name"],
                action_filter=["KILL"],
                min_timestamp=int(time_now_minus_interval.timestamp()),
                exact_player_match=True,
                exact_action=True
            )
            weapons = []
            for log in logs["logs"]:
                if log["player_name_1"] == player["name"] and not log["weapon"] in weapons:
                    weapons.append(log["weapon"])

            # Test whitelisted flag presence on player's profile
            whitelist_flag_present = False
            try:
                profile = get_player_profile(player["player_id"], 0)
                for flag in WHITELIST_FLAGS:
                    if player_has_flag(profile, flag):
                        whitelist_flag_present = True
            except :
                logger.warning("Unable to check player profile for flags")

            # Logs
            log_txt = (
                f"'{player['name']}'"
                f" - {TRANSL[player['team']][LANG]}"
                f"/{player['unit_name']}"
                f"/{TRANSL[player['role']][LANG]}"
                f" - Level : {player['level']}"
                f" - {player['kills']} kills in"
                f" {round(mins_from_offdef, 2)} minutes"
                f" ({round(kills_per_minute, 2)} kill/min)."
                f" {TRANSL['lastusedweapons'][LANG]} : {', '.join(weapons)}",
            )

            # Log (player has a whitelist flag)
            if whitelist_flag_present:
                logger.info(f"(whitelisted - flag) {log_txt}")
                continue

            # Log (whitelisted artillery player)
            if WHITELIST_ARTILLERY:
                if any(weapon in weapons for weapon in WEAPONS_ARTILLERY):
                    logger.info(f"(whitelisted - artillery) {log_txt}")
                    continue

            # Log (non-whitelisted player)
            logger.info(f"{log_txt}")

            # TODO : Flag the player

            # Prepare Discord embed
            if player["team"] == "axis":
                team_symbol = "🟥"
            elif player["team"] == "allies":
                team_symbol = "🟦"
            embed_desc_txt = (
                f"{team_symbol} {TRANSL[player['team']][LANG]} "
                f"/ {player['unit_name']} "
                f"/ {TRANSL[player['role']][LANG]}\n"
                f"{player['kills']} kills "
                f"/ {round(mins_from_offdef, 2)} min. "
                f"(**{round(kills_per_minute, 2)} kill/min**)\n"
                f"**{TRANSL['level'][LANG]} :** {player['level']}\n"
                f"**{TRANSL['lastusedweapons'][LANG]} :**\n {', '.join(weapons)}"
            )

            embed_color = green_to_red(
                kills_per_minute, min_value=KILLRATE_THRESHOLD, max_value=2
            )

            # Create Discord embed
            embed = discord.Embed(
                title=player["name"],
                url=get_external_profile_url(player["player_id"], player["name"]),
                description=embed_desc_txt,
                color=int(embed_color, base=16)
            )
            embed.set_author(
                name=BOT_NAME,
                url=DISCORD_EMBED_AUTHOR_URL,
                icon_url=DISCORD_EMBED_AUTHOR_ICON_URL
            )
            embed.set_thumbnail(url=get_avatar_url(player["player_id"]))

            # Send Discord embed
            server_number = int(get_server_number())
            if not SERVER_CONFIG[server_number - 1][1]:
                logger.warning("server %s - Discord webhook is disabled", server_number)
                return
            discord_webhook = SERVER_CONFIG[server_number - 1][0]
            webhook = discord.SyncWebhook.from_url(discord_webhook)
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
