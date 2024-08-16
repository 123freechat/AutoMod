# commands.py

def handle_op(bot, channel, user, target):
    bot.send_command(f"MODE {channel} +o {target}")

def handle_deop(bot, channel, user, target):
    bot.send_command(f"MODE {channel} -o {target}")

def handle_voice(bot, channel, user, target):
    bot.send_command(f"MODE {channel} +v {target}")

def handle_devoice(bot, channel, user, target):
    bot.send_command(f"MODE {channel} -v {target}")

def handle_kick(bot, channel, user, target):
    bot.send_command(f"KICK {channel} {target} :[auto] You've been kicked for flooding.")
    bot.track_user_stats(target, action="kick")

def handle_ban(bot, channel, user, target):
    bot.send_command(f"MODE {channel} +b {target}")
    bot.kick_user(channel, target, "[auto] You've been banned for repeated offenses.")
    bot.track_user_stats(target, action="ban")

def handle_shun(bot, channel, user, target):
    bot.send_command(f"MODE {channel} +q {target}")

def handle_join(bot, channel, user, target):
    bot.send_command(f"JOIN {target}")
    bot.track_user_stats(target, action="join")

def handle_part(bot, channel, user, target):
    bot.send_command(f"PART {target}")
    bot.track_user_stats(target, action="part")

def handle_floodpro(bot, channel, user, command):
    if user in bot.operators:
        if len(command) == 2:
            if command[1] == "on":
                bot.flood_protection_status[channel] = True
                bot.send_message(channel, f"[auto] Flood protection enabled in {channel}.")
            elif command[1] == "off":
                bot.flood_protection_status[channel] = False
                bot.send_message(channel, f"[auto] Flood protection disabled in {channel}.")
            else:
                bot.send_message(channel, "[auto] Invalid flood protection command. Use :floodpro on/off.")
        else:
            bot.send_message(channel, "[auto] Invalid flood protection command. Use :floodpro on/off.")
    else:
        bot.send_message(channel, "[auto] Only operators can use the :floodpro command.")

def handle_userstat(bot, channel, user, command):
    if len(command) == 2:
        nickname = command[1]
        bot.cursor.execute('SELECT reputation FROM users WHERE nickname = ?', (nickname,))
        reputation = bot.cursor.fetchone()[0]
        bot.send_message(channel, f"[stats] {nickname}'s total reputation is {reputation}")
    elif len(command) == 3:
        nickname, stat_type = command[1], command[2]
        bot.cursor.execute(f'SELECT {stat_type} FROM users WHERE nickname = ?', (nickname,))
        stat_value = bot.cursor.fetchone()[0]
        bot.send_message(channel, f"[stats] {nickname}'s {stat_type} stat is {stat_value}")
    else:
        bot.send_message(channel, "[auto] Invalid userstat command. Use :userstat <nickname> [<stat_type>].")
