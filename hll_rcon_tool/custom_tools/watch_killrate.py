"""
watch_killrate

A plugin for HLL CRCON (https://github.com/MarechJ/hll_rcon_tool)
that watches and reports players who get "too much" kills per minute.

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
    WEAPONS_ARMOR,
    WEAPONS_ARTILLERY,
    WEAPONS_MG,
    discord_embed_send,
    get_avatar_url,
    get_external_profile_url,
    get_match_elapsed_secs,
    green_to_red,
    team_view_stats
)
from custom_tools.common_translations import TRANSL
from custom_tools.watch_killrate_config import (
    BOT_NAME,
    KILLRATE_THRESHOLD,
    LANG,
    MINIMUM_KILLS,
    SERVER_CONFIG,
    WATCH_INTERVAL_SECS,
    WHITELIST_ARMOR,
    WHITELIST_ARTILLERY,
    WHITELIST_MG,
    WHITELIST_FLAGS
)


def watch_killrate_loop():
    """
    Calls the function that gathers data,
    then calls the function to analyze it.
    """
    rcon = Rcon(SERVER_INFO)
    (
        _,
        all_players,  # all_players
        _,
        _,  # all_infantry_players
        _,
        _,
        _
    ) = team_view_stats(rcon)

    if len(all_players) > 1:
        watch_killrate(all_players)
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
    # Avoids weird data returned at the beginning of the game
    if (get_match_elapsed_secs() / 60) < 2:
        logger.info(
            "Match started less than 2 minutes ago, waiting for %s mins",
            round((WATCH_INTERVAL_SECS / 60), 2)
        )
        return

    # Test the players
    for player in watched_players:

        mins_on_map = (int(player["offense"]) + int(player["defense"])) / 20

        # Don't test player : not been on map for at least a minute
        if mins_on_map == 0:
            continue

        # Don't test player : connected since less than WATCH_INTERVAL_SECS ago
        if int(player["profile"]["current_playtime_seconds"]) < WATCH_INTERVAL_SECS:
            continue

        # Don't test player : no(t enough) kills yet
        if int(player["kills"]) == 0 or int(player["kills"]) < MINIMUM_KILLS:
            continue

        kills_per_minute = int(player["kills"]) / mins_on_map

        if kills_per_minute > KILLRATE_THRESHOLD:

            # latest kills weapons (since last watch iteration)
            logs = get_recent_logs(
                end=500,
                player_search=player["name"],
                action_filter=["KILL"],
                min_timestamp=int(
                    (
                        datetime.now(timezone.utc) - timedelta(seconds=WATCH_INTERVAL_SECS)
                    ).timestamp()
                ),
                exact_player_match=True,
                exact_action=True
            )
            weapons = []
            for log in logs["logs"]:
                if log["player_name_1"] == player["name"] and not log["weapon"] in weapons:
                    weapons.append(log["weapon"])

            # Test whitelisted flag
            whitelist_flag_present = False
            for flag in WHITELIST_FLAGS:
                if player_has_flag((get_player_profile(player["player_id"], 0)), flag):
                    whitelist_flag_present = True

            # Logs
            log_txt = (
                f"'{player['name']}'"
                f" - {TRANSL[player['team']][LANG]}"
                f"/{player['unit_name']}"
                f"/{TRANSL[player['role']][LANG]}"
                f" - Level : {player['level']}"
                f" - {player['kills']} kills in"
                f" {round(mins_on_map, 2)} minutes"
                f" ({round(kills_per_minute, 2)} kill/min)."
                f" {TRANSL['lastusedweapons'][LANG]} : {', '.join(weapons)}",
            )

            # Log (player has a whitelist flag)
            if whitelist_flag_present:
                logger.info("(whitelisted - flag) %s", log_txt)
                continue

            # Log (whitelisted armor player)
            if WHITELIST_ARMOR:
                if any(weapon in weapons for weapon in WEAPONS_ARMOR):
                    logger.info("(whitelisted - armor) %s", log_txt)
                    continue

            # Log (whitelisted artillery player)
            if WHITELIST_ARTILLERY:
                if any(weapon in weapons for weapon in WEAPONS_ARTILLERY):
                    logger.info("(whitelisted - artillery) %s", log_txt)
                    continue

            # Log (whitelisted MG player)
            if WHITELIST_MG:
                if any(weapon in weapons for weapon in WEAPONS_MG):
                    logger.info("(whitelisted - MG) %s", log_txt)
                    continue

            # Log (non-whitelisted player)
            logger.info(log_txt)

            # Test Discord webhook
            server_number = int(get_server_number())
            if not SERVER_CONFIG[server_number - 1][1]:
                logger.warning("server %s - Discord webhook is disabled", server_number)
                return

            # Create Discord embed
            if player["team"] == "axis":
                team_symbol = "🟥"
            elif player["team"] == "allies":
                team_symbol = "🟦"
            embed = discord.Embed(
                title=player["name"],
                url=get_external_profile_url(player["player_id"], player["name"]),
                description=(
                    f"{team_symbol} {TRANSL[player['team']][LANG]} "
                    f"/ {player['unit_name']} "
                    f"/ {TRANSL[player['role']][LANG]}\n"
                    f"{player['kills']} kills "
                    f"/ {round(mins_on_map, 2)} min. "
                    f"(**{round(kills_per_minute, 2)} kill/min**)\n"
                    f"**{TRANSL['level'][LANG]} :** {player['level']}\n"
                    f"**{TRANSL['lastusedweapons'][LANG]} :**\n {', '.join(weapons)}"
                ),
                color=int(
                    green_to_red(kills_per_minute, min_value=KILLRATE_THRESHOLD, max_value=2),
                    base=16
                )
            )
            embed.set_author(
                name=BOT_NAME,
                url=DISCORD_EMBED_AUTHOR_URL,
                icon_url=DISCORD_EMBED_AUTHOR_ICON_URL
            )
            embed.set_thumbnail(url=get_avatar_url(player["player_id"]))

            # Send Discord embed
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
