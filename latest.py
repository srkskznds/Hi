import os
import json
import time
import random
import telebot
import qrcode
from telebot import types
from datetime import datetime, timedelta

# Initialize bot with token
TOKEN = '7864639854:AAGmrCNMVPPOAebSvll6Teq67sDqU2KQ_dw'
bot = telebot.TeleBot(TOKEN)

# Admin ID
ADMIN_ID = 6696347739

# UPI ID for payments
UPI_ID = "6376302899@superyes"

# Initialize files if they don't exist
if not os.path.exists('users.json'):
    with open('users.json', 'w') as f:
        json.dump({}, f)
    print("Created users.json file")

if not os.path.exists('names.json'):
    with open('names.json', 'w') as f:
        json.dump({}, f)
    print("Created names.json file")

if not os.path.exists('quizzes.json'):
    with open('quizzes.json', 'w') as f:
        json.dump({
            "Agriculture": {"all_questions": [], "new_questions": []},
            "GK": {"all_questions": [], "new_questions": []},
            "Hindi": {"all_questions": [], "new_questions": []}
        }, f)
    print("Created quizzes.json file")

# Data handling functions
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_names():
    try:
        with open('names.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_names(names):
    with open('names.json', 'w') as f:
        json.dump(names, f, indent=4)

def load_quizzes():
    try:
        with open('quizzes.json', 'r') as f:
            data = json.load(f)
            # Convert old format to new format if needed
            for subject in ["Agriculture", "GK", "Hindi"]:
                if subject in data and isinstance(data[subject], list):
                    data[subject] = {"all_questions": data[subject], "new_questions": []}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "Agriculture": {"all_questions": [], "new_questions": []},
            "GK": {"all_questions": [], "new_questions": []},
            "Hindi": {"all_questions": [], "new_questions": []}
        }

def save_quizzes(quizzes):
    with open('quizzes.json', 'w') as f:
        json.dump(quizzes, f, indent=4)

# User state tracking
user_state = {}
user_captcha = {}
user_quiz = {}
user_data = {}

# Function to generate a simple math CAPTCHA
def generate_captcha():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])

    if operation == '+':
        result = num1 + num2
    elif operation == '-':
        result = num1 - num2
    else:
        result = num1 * num2

    question = f"{num1} {operation} {num2} = ?"
    return question, str(result)

# Function to create payment QR code
def create_qr_code(amount):
    try:
        # Use the provided static QR code that works with all amounts
        # The user can specify the amount in their payment app
        img_path = "attached_assets/IMG-20250228-WA0008.jpg"

        # Check if file exists
        if not os.path.exists(img_path):
            print(f"QR image not found at {img_path}, trying to create dynamic QR")
            # Fallback to dynamic generation
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Create UPI payment string
            upi_string = f"upi://pay?pa={UPI_ID}&cu=INR&pn=Quiz%20Master%20Bot"
            qr.add_data(upi_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Save the QR code
            img_path = f"payment_qr_{int(time.time())}.png"
            img.save(img_path)
            print(f"Generated dynamic QR code: {img_path}")
        else:
            print(f"Using static QR code: {img_path}")

        return img_path
    except Exception as e:
        print(f"Error with QR code: {e}")
        return None

# Function to generate subscription keyboard
def get_subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1 Day Free Trial (Only Once)", callback_data="trial_1day"),
        types.InlineKeyboardButton("1 Day ₹10", callback_data="pay_1day"),
        types.InlineKeyboardButton("7 Days ₹50", callback_data="pay_7days"),
        types.InlineKeyboardButton("1 Month ₹200", callback_data="pay_1month"),
        types.InlineKeyboardButton("6 Months ₹500", callback_data="pay_6months"),
        types.InlineKeyboardButton("1 Year ₹1000", callback_data="pay_1year")
    )

    # Add contact information as a separate button
    markup.add(types.InlineKeyboardButton("📞 Contact Admin", url="https://t.me/Mukeshchh999"))

    return markup

# Function to check if user is approved
def is_user_approved(user_id):
    users = load_users()
    str_user_id = str(user_id)

    if str_user_id in users and "approved" in users[str_user_id]:
        # First check if the approved flag is set to False
        if not users[str_user_id]["approved"]:
            return False
            
        # Then check if subscription has expired
        expiry_time = users[str_user_id].get("expiry_time", 0)
        if expiry_time > time.time():
            return True
        else:
            # Subscription expired
            users[str_user_id]["approved"] = False
            save_users(users)
            return False
    return False

# Function to check if the user has used free trial
def has_used_free_trial(user_id):
    users = load_users()
    str_user_id = str(user_id)

    if str_user_id in users and "used_free_trial" in users[str_user_id]:
        return users[str_user_id]["used_free_trial"]
    return False

# Function to check if user has completed captcha verification
def has_verified_captcha(user_id):
    users = load_users()
    str_user_id = str(user_id)

    if str_user_id in users and "captcha_verified" in users[str_user_id]:
        return users[str_user_id]["captcha_verified"]
    return False

# Function to get user name from names.json
def get_user_name(user_id):
    names = load_names()
    str_user_id = str(user_id)

    if str_user_id in names:
        return names[str_user_id]["name"]
    return None

# Function to generate subject selection keyboard
def get_subject_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Agriculture", callback_data="subject_Agriculture"),
        types.InlineKeyboardButton("GK", callback_data="subject_GK"),
        types.InlineKeyboardButton("Hindi", callback_data="subject_Hindi"),
        types.InlineKeyboardButton("Mix", callback_data="subject_Mix")
    )
    return markup

# Add handler for quiz version selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_version_"))
def handle_quiz_version_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    # Check if user is still approved
    if not is_user_approved(user_id):
        subscription_text = (
            "❌ Your subscription has expired or been revoked.\n\n"
            "Please purchase a subscription to continue."
        )
        safe_send_message(chat_id, subscription_text, reply_markup=get_subscription_keyboard())
        return

    # Initialize user_quiz for this user if it doesn't exist
    if user_id not in user_quiz:
        user_quiz[user_id] = {}
        safe_send_message(chat_id, "❌ Session expired. Please start again with /quiz")
        return

    # Get version type (old or new)
    quiz_version = call.data.replace("quiz_version_", "")
    user_quiz[user_id]["quiz_version"] = quiz_version

    # Ask for question count
    subject = user_quiz[user_id].get("subject", "Unknown")
    count_text = f"🔢 *Select Number of Questions*\n\nHow many questions would you like for {subject}?"
    safe_send_message(chat_id, count_text, parse_mode="Markdown", reply_markup=get_quiz_count_keyboard())

# Function to generate quiz question count keyboard
def get_quiz_count_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=5)
    markup.add(
        types.InlineKeyboardButton("10", callback_data="count_10"),
        types.InlineKeyboardButton("20", callback_data="count_20"),
        types.InlineKeyboardButton("30", callback_data="count_30"),
        types.InlineKeyboardButton("40", callback_data="count_40"),
        types.InlineKeyboardButton("50", callback_data="count_50")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_subjects"))
    return markup

# Function to generate MCQ options keyboard
def get_mcq_keyboard(question_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("A", callback_data=f"answer_{question_id}_A"),
        types.InlineKeyboardButton("B", callback_data=f"answer_{question_id}_B"),
        types.InlineKeyboardButton("C", callback_data=f"answer_{question_id}_C"),
        types.InlineKeyboardButton("D", callback_data=f"answer_{question_id}_D")
    )
    return markup

# Function to safely send messages (with error handling)
def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

# Start Command - Initial bot interaction
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    str_user_id = str(user_id)

    # Check if user has already verified CAPTCHA and provided name
    if has_verified_captcha(user_id) and get_user_name(user_id):
        # User is already registered, show subscription plans
        subscription_text = (
            "📌 *Subscription Plans* 📌\n\n"
            "Please select a subscription plan:\n\n"
            "📞 Contact: +917410810528\n\n"
            "For Free Trial → Contact Admin (@Mukeshchh999)"
        )

        safe_send_message(chat_id, subscription_text, parse_mode="Markdown", reply_markup=get_subscription_keyboard())
        return

    # New user flow - first CAPTCHA verification
    if not has_verified_captcha(user_id):
        # Generate CAPTCHA
        captcha_question, captcha_answer = generate_captcha()
        user_captcha[user_id] = captcha_answer
        user_state[user_id] = "verify_captcha"

        # Send welcome message with CAPTCHA
        welcome_text = "🎓 *Welcome to Quiz Master Bot* 🎓\n\nPlease solve this verification problem first:\n\n" + captcha_question
        safe_send_message(chat_id, welcome_text, parse_mode="Markdown")
    else:
        # Ask for name if CAPTCHA already verified but name not provided
        user_state[user_id] = "input_name"
        safe_send_message(chat_id, "Please enter your name to continue:")

# Handle CAPTCHA verification
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "verify_captcha")
def verify_captcha(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    answer = message.text.strip()

    if answer == user_captcha.get(user_id):
        # CAPTCHA verified, save verification status
        users = load_users()
        str_user_id = str(user_id)

        if str_user_id not in users:
            users[str_user_id] = {}

        users[str_user_id]["captcha_verified"] = True
        users[str_user_id]["username"] = message.from_user.username or "None"
        users[str_user_id]["join_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_users(users)

        # Ask for name
        user_state[user_id] = "input_name"
        safe_send_message(chat_id, "Verification successful! Please enter your name to continue:")
    else:
        safe_send_message(chat_id, "❌ Incorrect answer. Please try again.")

# Handle user name input
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "input_name")
def process_name(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    name = message.text.strip()

    if len(name) < 2:
        safe_send_message(chat_id, "Please enter a valid name (at least 2 characters).")
        return

    # Store user name in names.json
    names = load_names()
    str_user_id = str(user_id)

    if str_user_id not in names:
        names[str_user_id] = {}

    names[str_user_id]["name"] = name
    names[str_user_id]["username"] = message.from_user.username or "None"
    names[str_user_id]["join_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_names(names)

    # Update user state
    user_state[user_id] = "subscription"

    # Show subscription plans
    subscription_text = (
        "📌 *Subscription Plans* 📌\n\n"
        "Please select a subscription plan:\n\n"
        "📞 Contact: +917410810528\n\n"
        "For Free Trial → Contact Admin (@Mukeshchh999)"
    )

    safe_send_message(chat_id, subscription_text, parse_mode="Markdown", reply_markup=get_subscription_keyboard())

    # Notify admin about new user
    admin_message = f"🔔 *New User Registration*\n\nName: {name}\nUsername: @{message.from_user.username or 'None'}\nUser ID: `{user_id}`"
    safe_send_message(ADMIN_ID, admin_message, parse_mode="Markdown")

# Handle subscription selection
@bot.callback_query_handler(func=lambda call: call.data.startswith(("trial_", "pay_")))
def handle_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    if call.data == "trial_1day":
        # Check if user already used free trial
        if has_used_free_trial(user_id):
            safe_send_message(chat_id, "❌ You have already used your free trial. Please select a paid plan.", reply_markup=get_subscription_keyboard())
        else:
            # Activate free trial
            users = load_users()
            str_user_id = str(user_id)

            users[str_user_id]["used_free_trial"] = True
            users[str_user_id]["approved"] = True
            users[str_user_id]["subscription"] = "1 Day Free Trial"
            users[str_user_id]["expiry_time"] = time.time() + 86400  # 1 day in seconds
            save_users(users)

            confirmation = (
                "✅ *Free Trial Activated!*\n\n"
                "You now have access to quizzes for 1 day.\n"
                "Use /quiz to start practicing."
            )
            safe_send_message(chat_id, confirmation, parse_mode="Markdown")
    else:
        # Handle paid subscriptions
        plan = call.data.replace("pay_", "")
        amount = {
            "1day": 10,
            "7days": 50,
            "1month": 200,
            "6months": 500,
            "1year": 1000
        }.get(plan, 0)

        days = {
            "1day": 1,
            "7days": 7,
            "1month": 30,
            "6months": 180,
            "1year": 365
        }.get(plan, 0)

        # Store subscription details for later verification
        user_data[user_id] = {
            "plan": plan,
            "amount": amount,
            "days": days
        }

        try:
            # Get QR code (either static or dynamically generated)
            qr_path = create_qr_code(amount)

            # Prepare payment text with clear instructions
            payment_text = (
                f"💰 *Payment: ₹{amount}*\n\n"
                f"1. Scan the QR code or pay to UPI ID: `{UPI_ID}`\n"
                f"2. *Enter amount: ₹{amount}* manually if needed\n"
                "3. After payment, upload the screenshot\n"
                "4. Provide the UTR/Reference number\n\n"
                "Your subscription will be activated after verification.\n\n"
                f"*UPI ID:* `{UPI_ID}`\n"
                "*Bank:* PNB 4060"
            )

            if not qr_path or not os.path.exists(qr_path):
                # If QR not available, send text-only instructions
                safe_send_message(chat_id, payment_text, parse_mode="Markdown")
            else:
                # Send QR code with instructions
                try:
                    with open(qr_path, 'rb') as qr_file:
                        bot.send_photo(chat_id, qr_file, caption=payment_text, parse_mode="Markdown")

                    # Don't delete the static QR file if it's our saved one
                    if not qr_path.startswith("attached_assets"):
                        try:
                            os.remove(qr_path)
                        except:
                            pass
                except Exception as e:
                    print(f"Error sending QR photo: {e}")
                    # Fallback to text-only if sending photo fails
                    safe_send_message(chat_id, payment_text, parse_mode="Markdown")

            # Update user state
            user_state[user_id] = "awaiting_screenshot"

        except Exception as e:
            print(f"Error in payment handling: {e}")
            # Fallback to text-only payment instructions if anything fails
            payment_text = (
                f"💰 *Payment: ₹{amount}*\n\n"
                f"Please pay to UPI ID: `{UPI_ID}`\n"
                "After payment, upload the screenshot and provide the UTR/Reference number.\n\n"
                f"*UPI ID:* `{UPI_ID}`"
            )
            safe_send_message(chat_id, payment_text, parse_mode="Markdown")
            user_state[user_id] = "awaiting_screenshot"

# Handle payment screenshot upload
@bot.message_handler(content_types=['photo'], func=lambda message: user_state.get(message.from_user.id) == "awaiting_screenshot")
def process_screenshot(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Save the photo ID for verification
    user_data[user_id]["screenshot_id"] = message.photo[-1].file_id

    # Update state and ask for UTR
    user_state[user_id] = "awaiting_utr"
    safe_send_message(chat_id, "Please enter the UTR/Reference number of your payment:")

# Handle UTR input
@bot.message_handler(func=lambda message: user_state.get(message.from_user.id) == "awaiting_utr")
def process_utr(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    utr = message.text.strip()
    
    # Validate UTR format - must be exactly 12 digits
    if not (utr.isdigit() and len(utr) == 12):
        safe_send_message(chat_id, "❌ Invalid UTR/Reference number. Please enter a valid 12-digit number.")
        return
    
    # Store UTR
    user_data[user_id]["utr"] = utr

    # Update state
    user_state[user_id] = "awaiting_verification"

    # Send wait message
    wait_message = safe_send_message(chat_id, "⏳ Please wait while your payment is being verified...")

    # Get user name for admin notification
    name = get_user_name(user_id) or "Unknown"

    # Send verification request to admin
    admin_text = (
        f"🔔 *Payment Verification Required*\n\n"
        f"Name: {name}\n"
        f"User: @{message.from_user.username or 'None'}\n"
        f"User ID: `{user_id}`\n"
        f"Plan: {user_data[user_id]['plan']}\n"
        f"Amount: ₹{user_data[user_id]['amount']}\n"
        f"UTR: {utr}"
    )

    # Create admin verification keyboard
    verify_markup = types.InlineKeyboardMarkup(row_width=2)
    verify_markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    # Send screenshot to admin
    bot.send_photo(ADMIN_ID, user_data[user_id]["screenshot_id"], caption=admin_text, parse_mode="Markdown", reply_markup=verify_markup)

# Handle admin verification
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_verification(call):
    admin_id = call.from_user.id

    if admin_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "You are not authorized to perform this action.")
        return

    parts = call.data.split("_", 1)  # Split at first underscore only
    action = parts[0]
    user_id = int(parts[1]) if len(parts) > 1 else 0

    if action == "approve":
        # Approve the payment
        users = load_users()
        str_user_id = str(user_id)

        if str_user_id not in users:
            users[str_user_id] = {}

        # Calculate expiry time
        days = user_data[user_id]["days"]
        expiry_time = time.time() + (days * 86400)  # Convert days to seconds

        # Update user information
        users[str_user_id]["approved"] = True
        users[str_user_id]["subscription"] = user_data[user_id]["plan"]
        users[str_user_id]["payment_amount"] = user_data[user_id]["amount"]
        users[str_user_id]["payment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[str_user_id]["expiry_time"] = expiry_time
        users[str_user_id]["payment_utr"] = user_data[user_id]["utr"]
        save_users(users)

        # Send confirmation to user
        confirmation = (
            "✅ *Payment Verified Successfully!*\n\n"
            f"Your subscription has been activated for {days} day(s).\n"
            "Use /quiz to start practicing."
        )
        safe_send_message(user_id, confirmation, parse_mode="Markdown")

        # Notify admin about successful approval
        bot.answer_callback_query(call.id, "Payment approved successfully.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif action == "reject":
        # Reject the payment
        safe_send_message(user_id, "❌ Your payment could not be verified. Please try again or contact the admin.", reply_markup=get_subscription_keyboard())

        # Notify admin about rejection
        bot.answer_callback_query(call.id, "Payment rejected.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    # Clean up user data
    if user_id in user_state:
        del user_state[user_id]
    if user_id in user_data:
        del user_data[user_id]

# Quiz Command - Start a quiz
@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if user is approved
    if not is_user_approved(user_id):
        safe_send_message(chat_id, "❌ You don't have an active subscription. Please subscribe to access quizzes.", reply_markup=get_subscription_keyboard())
        return

    # Ask for subject selection
    subject_text = "📚 *Choose a Subject*\n\nSelect a subject for your quiz:"
    safe_send_message(chat_id, subject_text, parse_mode="Markdown", reply_markup=get_subject_keyboard())

# Handle subject selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("subject_"))
def handle_subject_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    # Check if user is still approved
    if not is_user_approved(user_id):
        subscription_text = (
            "❌ Your subscription has expired or been revoked.\n\n"
            "Please purchase a subscription to continue."
        )
        safe_send_message(chat_id, subscription_text, reply_markup=get_subscription_keyboard())
        return

    subject = call.data.replace("subject_", "")

    # Store subject selection
    if user_id not in user_quiz:
        user_quiz[user_id] = {}

    user_quiz[user_id]["subject"] = subject
    # Set default quiz type - only MCQ is supported for now
    user_quiz[user_id]["quiz_type"] = "mcq"

    # Ask for quiz version (old or new)
    quiz_version_text = f"📚 *Select Quiz Version*\n\nWhich version of {subject} quiz would you like?"
    quiz_version_markup = types.InlineKeyboardMarkup(row_width=1)
    quiz_version_markup.add(
        types.InlineKeyboardButton("Old Quiz (All Questions)", callback_data="quiz_version_old"),
        types.InlineKeyboardButton("New Quiz (Recent Questions)", callback_data="quiz_version_new"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_subjects")
    )
    safe_send_message(chat_id, quiz_version_text, parse_mode="Markdown", reply_markup=quiz_version_markup)

# Handle quiz type selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_type_"))
def handle_quiz_type_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    # Check if user is still approved
    if not is_user_approved(user_id):
        subscription_text = (
            "❌ Your subscription has expired or been revoked.\n\n"
            "Please purchase a subscription to continue."
        )
        safe_send_message(chat_id, subscription_text, reply_markup=get_subscription_keyboard())
        return

    # Initialize user_quiz for this user if it doesn't exist
    if user_id not in user_quiz:
        user_quiz[user_id] = {}

    quiz_type = call.data.replace("quiz_type_", "")
    user_quiz[user_id]["quiz_type"] = quiz_type

    # Get the subject from user_quiz
    subject = user_quiz[user_id].get("subject", "Unknown")

    # Ask for quiz version (old or new)
    quiz_version_text = f"📚 *Select Quiz Version*\n\nWhich version of {subject} quiz would you like?"
    quiz_version_markup = types.InlineKeyboardMarkup(row_width=2)
    quiz_version_markup.add(
        types.InlineKeyboardButton("Old Quiz (All Questions)", callback_data="quiz_version_old"),
        types.InlineKeyboardButton("New Quiz (Recent Questions)", callback_data="quiz_version_new"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_subjects")
    )
    safe_send_message(chat_id, quiz_version_text, parse_mode="Markdown", reply_markup=quiz_version_markup)

# Handle back to subjects
@bot.callback_query_handler(func=lambda call: call.data == "back_to_subjects")
def back_to_subjects(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    # Ask for subject selection again
    subject_text = "📚 *Choose a Subject*\n\nSelect a subject for your quiz:"
    safe_send_message(chat_id, subject_text, parse_mode="Markdown", reply_markup=get_subject_keyboard())

# Handle question count selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("count_"))
def handle_count_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete previousmessage
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    if not is_user_approved(user_id):
        subscription_text = (
            "❌ Your subscription has expired or been revoked.\n\n"
            "Please purchase a subscription to continue."
        )
        safe_send_message(chat_id, subscription_text, reply_markup=get_subscription_keyboard())
        return

    # Initialize user_quiz if needed
    if user_id not in user_quiz:
        user_quiz[user_id] = {}
        safe_send_message(chat_id, "❌ Session expired. Please start again with /quiz")
        return

    # Make sure subject is set
    if "subject" not in user_quiz[user_id]:
        safe_send_message(chat_id, "❌ Session expired. Please start again with /quiz")
        return

    count = int(call.data.replace("count_", ""))
    subject = user_quiz[user_id]["subject"]
    quiz_version = user_quiz[user_id].get("quiz_version", "old")  # Default to old if not specified

    # Load questions
    quizzes = load_quizzes()

    if subject == "Mix":
        # Combine questions from all subjects based on version
        all_questions = []
        for sub in ["Agriculture", "GK", "Hindi"]:
            if quiz_version == "old":
                # Get all questions for old quiz
                if "all_questions" in quizzes[sub] and quizzes[sub]["all_questions"]:
                    all_questions.extend(quizzes[sub]["all_questions"])
            else:
                # Get only new questions for new quiz
                if "new_questions" in quizzes[sub] and quizzes[sub]["new_questions"]:
                    all_questions.extend(quizzes[sub]["new_questions"])

        if not all_questions:
            version_text = "new" if quiz_version == "new" else "old"
            safe_send_message(chat_id, f"❌ No {version_text} questions available in any subject. Please try again later.", reply_markup=get_subject_keyboard())
            return

        # Shuffle and select questions
        selected_questions = random.sample(all_questions, min(count, len(all_questions)))
    else:
        # Get the right question set based on version
        if quiz_version == "old":
            subject_questions = quizzes[subject].get("all_questions", [])
            version_text = "old"
        else:
            subject_questions = quizzes[subject].get("new_questions", [])
            version_text = "new"

        if not subject_questions:
            safe_send_message(chat_id, f"❌ No {version_text} questions available for {subject}. Please try another option.", reply_markup=get_subject_keyboard())
            return

        # Check if there are enough questions
        if len(subject_questions) < count:
            safe_send_message(chat_id, f"⚠️ Only {len(subject_questions)} {version_text} questions available for {subject}. Proceeding with available questions.", parse_mode="Markdown")

        # Shuffle and select questions
        selected_questions = random.sample(subject_questions, min(count, len(subject_questions)))

    # Store quiz data
    user_quiz[user_id]["questions"] = selected_questions
    user_quiz[user_id]["current_question"] = 0
    user_quiz[user_id]["correct_answers"] = 0
    user_quiz[user_id]["answers"] = []  # Track all answers, not showing results immediately
    user_quiz[user_id]["start_time"] = time.time()  # Record start time
    user_quiz[user_id]["time_limit"] = calculate_quiz_time(len(selected_questions))  # Set time limit based on question count
    
    # Display time limit info
    time_limit_minutes = user_quiz[user_id]["time_limit"] // 60
    time_info = f"⏱️ *Quiz Timer Started*\n\nYou have {time_limit_minutes} minutes to complete {len(selected_questions)} questions."
    safe_send_message(chat_id, time_info, parse_mode="Markdown")
    
    # Start the quiz
    send_quiz_question(user_id, chat_id)

# Function to calculate quiz time based on question count
def calculate_quiz_time(question_count):
    if question_count <= 10:
        return 5 * 60  # 5 minutes in seconds
    elif question_count <= 20:
        return 10 * 60  # 10 minutes in seconds
    elif question_count <= 30:
        return 15 * 60  # 15 minutes in seconds
    elif question_count <= 40:
        return 20 * 60  # 20 minutes in seconds
    else:
        return 30 * 60  # 30 minutes in seconds

# Function to format time remaining
def format_time_remaining(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

# Function to send a quiz question
def send_quiz_question(user_id, chat_id):
    try:
        # Check if user is still approved before proceeding
        if not is_user_approved(user_id):
            safe_send_message(chat_id, "❌ Your subscription has been revoked by the admin. Your quiz session has ended.", parse_mode="Markdown")
            # Clean up quiz data
            if user_id in user_quiz:
                del user_quiz[user_id]
            return
            
        quiz_data = user_quiz[user_id]
        current_index = quiz_data["current_question"]
        total_questions = len(quiz_data["questions"])
        
        # Check if quiz timer is expired
        if "start_time" in quiz_data and "time_limit" in quiz_data:
            time_elapsed = int(time.time() - quiz_data["start_time"])
            time_remaining = max(0, quiz_data["time_limit"] - time_elapsed)
            
            if time_remaining <= 0:
                safe_send_message(chat_id, "⏱️ *Time's up!* Your quiz session has expired.", parse_mode="Markdown")
                show_quiz_results(user_id, chat_id)
                return

        if current_index < total_questions:
            question_data = quiz_data["questions"][current_index]

            # Ensure all options exist
            for option in ['A', 'B', 'C', 'D']:
                if option not in question_data['options']:
                    question_data['options'][option] = f"Option {option} (Missing)"
            
            # Calculate time remaining if timer exists
            timer_text = ""
            if "start_time" in quiz_data and "time_limit" in quiz_data:
                time_elapsed = int(time.time() - quiz_data["start_time"])
                time_remaining = max(0, quiz_data["time_limit"] - time_elapsed)
                timer_text = f"⏱️ Time remaining: {format_time_remaining(time_remaining)}\n\n"

            # Format the question with options
            question_text = (
                f"*Question {current_index + 1}/{total_questions}*\n\n"
                f"{timer_text}"
                f"{question_data['question']}\n\n"
                f"A. {question_data['options']['A']}\n"
                f"B. {question_data['options']['B']}\n"
                f"C. {question_data['options']['C']}\n"
                f"D. {question_data['options']['D']}"
            )

            # Send question with options
            safe_send_message(chat_id, question_text, parse_mode="Markdown", reply_markup=get_mcq_keyboard(current_index))
        else:
            # All questions answered, show results
            show_quiz_results(user_id, chat_id)
    except Exception as e:
        print(f"Error in send_quiz_question: {e}")
        safe_send_message(chat_id, "❌ An error occurred while displaying the question. Please try again with /quiz.")

        # Reset user quiz state
        if user_id in user_quiz:
            del user_quiz[user_id]

# Handle user answer selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    try:
        parts = call.data.split("_")
        if len(parts) < 3:
            raise ValueError(f"Invalid callback data format: {call.data}")

        question_id = int(parts[1])
        selected_option = parts[2]

        # Check if user has quiz data
        if user_id not in user_quiz or "questions" not in user_quiz[user_id]:
            safe_send_message(chat_id, "❌ Session expired. Please start again with /quiz")
            return

        # Check if user is still approved
        if not is_user_approved(user_id):
            safe_send_message(chat_id, "❌ Your subscription has been revoked by the admin. Your quiz session has ended.", parse_mode="Markdown")
            # Clean up quiz data
            if user_id in user_quiz:
                del user_quiz[user_id]
            return
            
        # Check answer
        quiz_data = user_quiz[user_id]
        
        # Check if quiz timer is expired
        if "start_time" in quiz_data and "time_limit" in quiz_data:
            time_elapsed = int(time.time() - quiz_data["start_time"])
            time_remaining = max(0, quiz_data["time_limit"] - time_elapsed)
            
            if time_remaining <= 0:
                safe_send_message(chat_id, "⏱️ *Time's up!* Your quiz session has expired.", parse_mode="Markdown")
                show_quiz_results(user_id, chat_id)
                return

        # Validate indices
        if question_id >= len(quiz_data["questions"]):
            safe_send_message(chat_id, "❌ Invalid question. Please start again with /quiz")
            return

        question_data = quiz_data["questions"][question_id]
        correct_option = question_data["correct"]
        current_index = quiz_data["current_question"]
        total_questions = len(quiz_data["questions"])

        # Store the answer (don't show result yet)
        quiz_data["answers"].append({
            "question": question_data["question"],
            "selected": selected_option,
            "correct": correct_option,
            "options": question_data["options"],
            "is_correct": selected_option == correct_option
        })

        # Update correct answer count
        if selected_option == correct_option:
            quiz_data["correct_answers"] += 1

        # Move to next question directly without showing "Answer recorded" message
        quiz_data["current_question"] += 1
        send_quiz_question(user_id, chat_id)
    except Exception as e:
        print(f"Error in handle_answer: {e}")
        safe_send_message(chat_id, "❌ An error occurred while processing your answer. Please try again with /quiz")

        # Reset user quiz state if there was an error
        if user_id in user_quiz:
            del user_quiz[user_id]

# Function to show quiz results
def show_quiz_results(user_id, chat_id):
    try:
        quiz_data = user_quiz[user_id]
        total_questions = len(quiz_data["questions"])
        correct_answers = quiz_data["correct_answers"]
        wrong_answers = total_questions - correct_answers

        # Calculate percentage (avoid division by zero)
        if total_questions > 0:
            percentage = (correct_answers / total_questions) * 100
        else:
            percentage = 0

        # Format result message
        quiz_version = quiz_data.get("quiz_version", "old")
        version_text = "Old Quiz (All Questions)" if quiz_version == "old" else "New Quiz (Recent Questions)"

        # Calculate time used if timer was active
        time_info = ""
        if "start_time" in quiz_data and "time_limit" in quiz_data:
            time_used = int(time.time() - quiz_data["start_time"])
            time_limit = quiz_data["time_limit"]
            
            # Check if time expired
            if time_used >= time_limit:
                time_info = f"Time: Expired (Time's up!)\n"
            else:
                minutes_used = time_used // 60
                seconds_used = time_used % 60
                time_info = f"Time used: {minutes_used:02d}:{seconds_used:02d}\n"

        result_text = (
            f"📊 *Quiz Results*\n\n"
            f"Subject: {quiz_data['subject']}\n"
            f"Version: {version_text}\n"
            f"Total Questions: {total_questions}\n"
            f"Correct Answers: {correct_answers}\n"
            f"Wrong Answers: {wrong_answers}\n"
            f"Score: {correct_answers}/{total_questions}\n"
            f"Percentage: {percentage:.2f}%\n"
            f"{time_info}\n"
        )

        # Add wrong answers with corrections
        if wrong_answers > 0:
            result_text += "*Wrong Answers:*\n\n"

            wrong_count = 0
            for i, answer in enumerate(quiz_data["answers"]):
                if not answer["is_correct"]:
                    wrong_count += 1
                    result_text += (
                        f"❌ *Question {i+1}:* {answer['question']}\n"
                        f"Your Answer: {answer['selected']} ({answer['options'][answer['selected']]})\n"
                        f"Correct Answer: {answer['correct']} ({answer['options'][answer['correct']]})\n\n"
                    )

        # Create result keyboard
        result_markup = types.InlineKeyboardMarkup(row_width=2)
        result_markup.add(
            types.InlineKeyboardButton("🔄 Reattempt", callback_data="reattempt"),
            types.InlineKeyboardButton("📚 New Quiz", callback_data="new_quiz"),
            types.InlineKeyboardButton("🔙 Back", callback_data="back_to_subjects")
        )

        # Send results
        safe_send_message(chat_id, result_text, parse_mode="Markdown", reply_markup=result_markup)

        # Get user name
        name = get_user_name(user_id) or "Unknown"

        # Update user history
        users = load_users()
        str_user_id = str(user_id)

        if str_user_id in users:
            if "quiz_history" not in users[str_user_id]:
                users[str_user_id]["quiz_history"] = []

            # Add quiz result to history
            users[str_user_id]["quiz_history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "subject": quiz_data["subject"],
                "total": total_questions,
                "correct": correct_answers,
                "percentage": f"{percentage:.2f}%"
            })

            save_users(users)

        # Send result to admin
        admin_result = (
            f"🔔 *Quiz Completed*\n\n"
            f"Name: {name}\n"
            f"User: @{users[str_user_id].get('username', 'None')}\n"
            f"User ID: `{user_id}`\n"
            f"Subject: {quiz_data['subject']}\n"
            f"Score: {correct_answers}/{total_questions}\n"
            f"Percentage: {percentage:.2f}%"
        )

        safe_send_message(ADMIN_ID, admin_result, parse_mode="Markdown")

    except Exception as e:
        print(f"Error in show_quiz_results: {e}")
        safe_send_message(chat_id, "❌ An error occurred while displaying quiz results. Please try again with /quiz.")

        # Reset user quiz state
        if user_id in user_quiz:
            del user_quiz[user_id]

# Handle reattempt or new quiz
@bot.callback_query_handler(func=lambda call: call.data in ["reattempt", "new_quiz"])
def handle_quiz_action(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Delete previous message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    if call.data == "reattempt":
        # Reset quiz progress for reattempt
        if user_id in user_quiz and "questions" in user_quiz[user_id]:
            user_quiz[user_id]["current_question"] = 0
            user_quiz[user_id]["correct_answers"] = 0
            user_quiz[user_id]["answers"] = []
            
            # Reset timer
            user_quiz[user_id]["start_time"] = time.time()
            question_count = len(user_quiz[user_id]["questions"])
            user_quiz[user_id]["time_limit"] = calculate_quiz_time(question_count)
            
            # Display time limit info
            time_limit_minutes = user_quiz[user_id]["time_limit"] // 60
            time_info = f"⏱️ *Quiz Timer Restarted*\n\nYou have {time_limit_minutes} minutes to complete {question_count} questions."
            safe_send_message(chat_id, time_info, parse_mode="Markdown")

            # Start the quiz again
            send_quiz_question(user_id, chat_id)
        else:
            safe_send_message(chat_id, "❌ Session expired. Please start again with /quiz")
    else:
        # Start a new quiz
        subject_text = "📚 *Choose a Subject*\n\nSelect a subject for your quiz:"
        safe_send_message(chat_id, subject_text, parse_mode="Markdown", reply_markup=get_subject_keyboard())

# Handle admin confirmation callbacks
@bot.callback_query_handler(func=lambda call: call.data.startswith(("confirm_", "cancel_")))
def handle_admin_confirmation(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Only admin can perform these actions
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "You are not authorized to perform this action.")
        return

    # Acknowledge the callback query first to prevent timeouts
    bot.answer_callback_query(call.id)

    # Delete confirmation message
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

    # Handle different confirmation actions
    if call.data == "confirm_alldisapprove":
        # Disapprove all users
        users = load_users()
        disapproved_count = 0
        
        for user_id in users:
            if users[user_id].get("approved", False):
                users[user_id]["approved"] = False
                disapproved_count += 1
        
        save_users(users)
        safe_send_message(chat_id, f"✅ Successfully disapproved {disapproved_count} users.")
        
    elif call.data == "cancel_alldisapprove":
        safe_send_message(chat_id, "⚠️ Operation cancelled. No users were disapproved.")
        
    elif call.data == "confirm_allreset":
        # Full system reset
        try:
            # Backup everything first
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup users.json
            if os.path.exists('users.json'):
                os.rename('users.json', f'users_backup_{backup_timestamp}.json')
                
            # Backup names.json
            if os.path.exists('names.json'):
                os.rename('names.json', f'names_backup_{backup_timestamp}.json')
            
            # Create empty files
            with open('users.json', 'w') as f:
                json.dump({}, f)
                
            with open('names.json', 'w') as f:
                json.dump({}, f)
            
            # Keep question data but reset new_questions
            quizzes = load_quizzes()
            for subject in quizzes:
                if isinstance(quizzes[subject], dict) and "new_questions" in quizzes[subject]:
                    quizzes[subject]["new_questions"] = []
            save_quizzes(quizzes)
            
            # Clear any runtime quiz data
            global user_quiz, user_state, user_captcha, user_data
            user_quiz = {}
            user_state = {}
            user_captcha = {}
            user_data = {}
            
            safe_send_message(chat_id, "✅ Full system reset completed. All user data has been wiped. Old data backed up with timestamp.")
            
            # Add admin back with approval
            users = load_users()
            str_admin_id = str(ADMIN_ID)
            users[str_admin_id] = {
                "approved": True,
                "subscription": "Admin Account",
                "captcha_verified": True,
                "username": "Admin",
                "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "expiry_time": time.time() + (365 * 86400)  # 1 year approval
            }
            save_users(users)
            
        except Exception as e:
            print(f"Reset error: {e}")
            safe_send_message(chat_id, f"❌ Error during system reset: {str(e)}")
        
    elif call.data == "cancel_allreset":
        safe_send_message(chat_id, "⚠️ System reset cancelled. All data remains intact.")

# Reattempt command
@bot.message_handler(commands=['reattempt'])
def reattempt_quiz(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in user_quiz and "questions" in user_quiz[user_id]:
        # Reset quiz progress
        user_quiz[user_id]["current_question"] = 0
        user_quiz[user_id]["correct_answers"] = 0
        user_quiz[user_id]["answers"] = []
        
        # Reset timer
        user_quiz[user_id]["start_time"] = time.time()
        question_count = len(user_quiz[user_id]["questions"])
        user_quiz[user_id]["time_limit"] = calculate_quiz_time(question_count)
        
        # Display time limit info
        time_limit_minutes = user_quiz[user_id]["time_limit"] // 60
        time_info = f"⏱️ *Quiz Timer Restarted*\n\nYou have {time_limit_minutes} minutes to complete {question_count} questions."
        safe_send_message(chat_id, time_info, parse_mode="Markdown")

        # Start the quiz again
        send_quiz_question(user_id, chat_id)
    else:
        safe_send_message(chat_id, "❌ No recent quiz found to reattempt. Please use /quiz to start a new quiz.")

# Admin Commands
# View user logs
@bot.message_handler(commands=['logs'], func=lambda message: message.from_user.id == ADMIN_ID)
def view_logs(message):
    chat_id = message.chat.id

    try:
        # Extract user_id from command
        user_id = message.text.split()[1]
        users = load_users()
        names = load_names()

        if user_id in users:
            user_data = users[user_id]
            name = names.get(user_id, {}).get("name", "Not available")

            # Format user logs
            log_text = (
                f"📋 *User Logs*\n\n"
                f"*User ID:* `{user_id}`\n"
                f"*Name:* {name}\n"
                f"*Username:* @{user_data.get('username', 'None')}\n"
                f"*Join Date:* {user_data.get('join_date', 'Not available')}\n"
                f"*Subscription:* {user_data.get('subscription', 'None')}\n"
                f"*Approved:* {'Yes' if user_data.get('approved', False) else 'No'}\n"
                f"*Used Free Trial:* {'Yes' if user_data.get('used_free_trial', False) else 'No'}\n"
            )

            # Add payment info if available
            if "payment_date" in user_data:
                log_text += (
                    f"*Payment Date:* {user_data['payment_date']}\n"
                    f"*Payment Amount:* ₹{user_data.get('payment_amount', 'N/A')}\n"
                    f"*UTR:* {user_data.get('payment_utr', 'N/A')}\n"
                )

            # Add expiry time if available
            if "expiry_time" in user_data:
                expiry_date = datetime.fromtimestamp(user_data["expiry_time"]).strftime("%Y-%m-%d %H:%M:%S")
                log_text += f"*Expiry Date:* {expiry_date}\n\n"

            # Add quiz history if available
            if "quiz_history" in user_data and user_data["quiz_history"]:
                log_text += "*Quiz History:*\n\n"

                for i, quiz in enumerate(user_data["quiz_history"][-5:], 1):  # Show last 5 quizzes
                    log_text += (
                        f"{i}. Date: {quiz['date']}\n"
                        f"   Subject: {quiz['subject']}\n"
                        f"   Score: {quiz['correct']}/{quiz['total']} ({quiz['percentage']})\n\n"
                    )

            safe_send_message(chat_id, log_text, parse_mode="Markdown")
        else:
            safe_send_message(chat_id, "❌ User not found.")
    except IndexError:
        safe_send_message(chat_id, "❌ Please provide a user ID. Usage: /logs <user_id>")

# Approve user with custom duration
@bot.message_handler(commands=['approve'], func=lambda message: message.from_user.id == ADMIN_ID)
def approve_user(message):
    chat_id = message.chat.id

    try:
        # Extract user_id and days from command
        parts = message.text.split()
        if len(parts) != 3:
            safe_send_message(chat_id, "❌ Incorrect format. Usage: /approve <user_id> <days>")
            return

        user_id = parts[1]
        days = int(parts[2])

        if days <= 0:
            safe_send_message(chat_id, "❌ Days must be a positive number.")
            return

        users = load_users()

        if user_id in users:
            # Calculate expiry time
            expiry_time = time.time() + (days * 86400)  # Convert days to seconds

            # Update user information
            users[user_id]["approved"] = True
            users[user_id]["subscription"] = f"{days} Day(s) Admin Approval"
            users[user_id]["payment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users[user_id]["expiry_time"] = expiry_time
            save_users(users)

            safe_send_message(chat_id, f"✅ User {user_id} has been approved for {days} day(s).")

            # Notify user
            try:
                safe_send_message(int(user_id), f"✅ Your subscription has been approved for {days} day(s). Use /quiz to start practicing.")
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            safe_send_message(chat_id, "❌ User not found.")
    except IndexError:
        safe_send_message(chat_id, "❌ Please provide a user ID and days. Usage: /approve <user_id> <days>")
    except ValueError:
        safe_send_message(chat_id, "❌ Days must be a valid number. Usage: /approve <user_id> <days>")

# Disapprove user
@bot.message_handler(commands=['disapprove'], func=lambda message: message.from_user.id == ADMIN_ID)
def disapprove_user(message):
    chat_id = message.chat.id

    try:
        # Extract user_id from command
        user_id_str = message.text.split()[1]
        user_id_int = int(user_id_str)
        users = load_users()

        if user_id_str in users:
            # Disapprove user
            users[user_id_str]["approved"] = False
            save_users(users)

            # Check if user is in active quiz and clear their session
            if user_id_int in user_quiz:
                # Clean up active quiz session
                if "current_question" in user_quiz[user_id_int]:
                    del user_quiz[user_id_int]

            safe_send_message(chat_id, f"✅ User {user_id_str} has been disapproved and any active quiz sessions terminated.")

            # Notify user
            try:
                safe_send_message(user_id_int, "❌ Your subscription has been revoked by the admin. Please contact support for more information.")
            except Exception as e:
                print(f"Error notifying user: {e}")
        else:
            safe_send_message(chat_id, "❌ User not found.")
    except IndexError:
        safe_send_message(chat_id, "❌ Please provide a user ID. Usage: /disapprove <user_id>")
    except ValueError:
        safe_send_message(chat_id, "❌ Invalid user ID format. Please provide a numeric user ID.")

# Disapprove all users
@bot.message_handler(commands=['alldisapprove'], func=lambda message: message.from_user.id == ADMIN_ID)
def disapprove_all_users(message):
    chat_id = message.chat.id
    
    # Confirm before proceeding
    confirm_markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_markup.add(
        types.InlineKeyboardButton("✅ Yes, Disapprove All", callback_data="confirm_alldisapprove"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_alldisapprove")
    )
    
    safe_send_message(chat_id, "⚠️ *WARNING*: This will disapprove ALL users. Are you sure?", parse_mode="Markdown", reply_markup=confirm_markup)

# Reset a user's data
@bot.message_handler(commands=['reset'], func=lambda message: message.from_user.id == ADMIN_ID)
def reset_user_data(message):
    chat_id = message.chat.id

    try:
        # Extract user_id from command
        user_id = message.text.split()[1]
        users = load_users()

        if user_id in users:
            # Preserve subscription status
            approved_status = users[user_id].get("approved", False)
            subscription = users[user_id].get("subscription", "None")
            expiry_time = users[user_id].get("expiry_time", 0)
            used_free_trial = users[user_id].get("used_free_trial", False)
            
            # Reset quiz history
            if "quiz_history" in users[user_id]:
                del users[user_id]["quiz_history"]
            
            # Keep only essential data
            users[user_id] = {
                "approved": approved_status,
                "subscription": subscription,
                "expiry_time": expiry_time,
                "used_free_trial": used_free_trial,
                "username": users[user_id].get("username", "None"),
                "join_date": users[user_id].get("join_date", "Unknown"),
                "captcha_verified": users[user_id].get("captcha_verified", True)
            }
            
            save_users(users)
            safe_send_message(chat_id, f"✅ User {user_id}'s quiz data has been reset. Subscription status remains unchanged.")
        else:
            safe_send_message(chat_id, "❌ User not found.")
    except IndexError:
        safe_send_message(chat_id, "❌ Please provide a user ID. Usage: /reset <user_id>")

# Full system reset
@bot.message_handler(commands=['allreset'], func=lambda message: message.from_user.id == ADMIN_ID)
def full_system_reset(message):
    chat_id = message.chat.id
    
    # Confirm before proceeding
    confirm_markup = types.InlineKeyboardMarkup(row_width=2)
    confirm_markup.add(
        types.InlineKeyboardButton("✅ Yes, Reset Everything", callback_data="confirm_allreset"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_allreset")
    )
    
    warning_text = (
        "⚠️ *CRITICAL WARNING* ⚠️\n\n"
        "This will delete *ALL* user data including:\n"
        "• User accounts\n"
        "• Payment history\n"
        "• Quiz results\n"
        "• Subscription information\n\n"
        "This action *CANNOT* be undone!\n\n"
        "Are you absolutely sure?"
    )
    
    safe_send_message(chat_id, warning_text, parse_mode="Markdown", reply_markup=confirm_markup)

# Backup system
@bot.message_handler(commands=['backup'], func=lambda message: message.from_user.id == ADMIN_ID)
def create_backup(message):
    chat_id = message.chat.id
    
    try:
        # Create backup directory if it doesn't exist
        backup_dir = "backup"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Payment history backup
        payment_history = []
        users = load_users()
        
        for user_id, user_data in users.items():
            if "payment_date" in user_data:
                payment_info = {
                    "user_id": user_id,
                    "username": user_data.get("username", "None"),
                    "name": get_user_name(int(user_id)) or "Unknown",
                    "payment_date": user_data.get("payment_date", "Unknown"),
                    "payment_amount": user_data.get("payment_amount", "Unknown"),
                    "payment_utr": user_data.get("payment_utr", "Unknown"),
                    "subscription": user_data.get("subscription", "Unknown")
                }
                payment_history.append(payment_info)
        
        payment_file = f"{backup_dir}/payment_history_{timestamp}.txt"
        with open(payment_file, "w") as f:
            f.write("PAYMENT HISTORY BACKUP\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for payment in payment_history:
                f.write(f"User ID: {payment['user_id']}\n")
                f.write(f"Username: @{payment['username']}\n")
                f.write(f"Name: {payment['name']}\n")
                f.write(f"Payment Date: {payment['payment_date']}\n")
                f.write(f"Amount: ₹{payment['payment_amount']}\n")
                f.write(f"UTR: {payment['payment_utr']}\n")
                f.write(f"Subscription: {payment['subscription']}\n")
                f.write("-" * 40 + "\n")
        
        # 2. Quiz scores backup
        quiz_scores = []
        
        for user_id, user_data in users.items():
            if "quiz_history" in user_data:
                for quiz in user_data["quiz_history"]:
                    quiz_info = {
                        "user_id": user_id,
                        "username": user_data.get("username", "None"),
                        "name": get_user_name(int(user_id)) or "Unknown",
                        "date": quiz.get("date", "Unknown"),
                        "subject": quiz.get("subject", "Unknown"),
                        "total": quiz.get("total", 0),
                        "correct": quiz.get("correct", 0),
                        "percentage": quiz.get("percentage", "0%")
                    }
                    quiz_scores.append(quiz_info)
        
        scores_file = f"{backup_dir}/quiz_scores_{timestamp}.txt"
        with open(scores_file, "w") as f:
            f.write("QUIZ SCORES BACKUP\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for score in quiz_scores:
                f.write(f"User ID: {score['user_id']}\n")
                f.write(f"Username: @{score['username']}\n")
                f.write(f"Name: {score['name']}\n")
                f.write(f"Date: {score['date']}\n")
                f.write(f"Subject: {score['subject']}\n")
                f.write(f"Score: {score['correct']}/{score['total']} ({score['percentage']})\n")
                f.write("-" * 40 + "\n")
        
        # 3. Users data backup
        users_file = f"{backup_dir}/users_data_{timestamp}.txt"
        with open(users_file, "w") as f:
            f.write("USERS DATA BACKUP\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for user_id, user_data in users.items():
                name = get_user_name(int(user_id)) or "Unknown"
                f.write(f"User ID: {user_id}\n")
                f.write(f"Username: @{user_data.get('username', 'None')}\n")
                f.write(f"Name: {name}\n")
                f.write(f"Join Date: {user_data.get('join_date', 'Unknown')}\n")
                f.write(f"Approved: {user_data.get('approved', False)}\n")
                f.write(f"Subscription: {user_data.get('subscription', 'None')}\n")
                f.write(f"Expiry: {datetime.fromtimestamp(user_data.get('expiry_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if user_data.get('expiry_time', 0) > 0 else 'Unknown'}\n")
                f.write(f"Used Free Trial: {user_data.get('used_free_trial', False)}\n")
                f.write("-" * 40 + "\n")
        
        # 4. Subject-wise question backup
        quizzes = load_quizzes()
        
        for subject in ["Agriculture", "GK", "Hindi"]:
            # Backup all questions
            questions = quizzes[subject].get("all_questions", [])
            if questions:
                question_file = f"{backup_dir}/{subject.lower()}_{timestamp}.txt"
                with open(question_file, "w") as f:
                    f.write(f"{subject.upper()} QUESTIONS BACKUP\n")
                    f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Questions: {len(questions)}\n\n")
                    
                    for q in questions:
                        f.write(f"Q: {q['question']}\n")
                        f.write(f"A: {q['options']['A']}\n")
                        f.write(f"B: {q['options']['B']}\n")
                        f.write(f"C: {q['options']['C']}\n")
                        f.write(f"D: {q['options']['D']}\n")
                        f.write(f"ANS: {q['correct']}\n\n")
        
        # Create a zip file with all backups
        import zipfile
        zip_file = f"backup_{timestamp}.zip"
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    zipf.write(os.path.join(root, file))
        
        # Send the zip file to admin
        with open(zip_file, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"📦 Complete backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(backup_dir)
            os.remove(zip_file)
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        safe_send_message(chat_id, "✅ Backup completed successfully!")
        
    except Exception as e:
        print(f"Backup error: {e}")
        safe_send_message(chat_id, f"❌ Error creating backup: {str(e)}")

# View all approved users
@bot.message_handler(commands=['view'], func=lambda message: message.from_user.id == ADMIN_ID)
def view_approved_users(message):
    chat_id = message.chat.id
    users = load_users()
    names = load_names()

    approved_users = []

    for user_id, user_data in users.items():
        if user_data.get("approved", False):
            username = user_data.get("username", "None")
            name = names.get(user_id, {}).get("name", "Unknown")
            expiry_time = user_data.get("expiry_time", 0)
            expiry_date = datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d") if expiry_time > 0 else "N/A"

            approved_users.append(f"👤 ID: `{user_id}`\n   Name: {name}\n   Username: @{username}\n   Expiry: {expiry_date}\n")

    if approved_users:
        # Split into chunks if there are many users
        chunk_size = 20
        for i in range(0, len(approved_users), chunk_size):
            chunk = approved_users[i:i + chunk_size]
            text = f"📋 *Approved Users ({i+1}-{min(i+chunk_size, len(approved_users))} of {len(approved_users)})*\n\n" + "\n".join(chunk)
            safe_send_message(chat_id, text, parse_mode="Markdown")
    else:
        safe_send_message(chat_id, "❌ No approved users found.")

# Broadcast message to all users
@bot.message_handler(commands=['broadcast'], func=lambda message: message.from_user.id == ADMIN_ID)
def broadcast_message(message):
    chat_id = message.chat.id

    try:
        # Extract broadcast message
        broadcast_text = message.text.replace("/broadcast", "", 1).strip()

        if not broadcast_text:
            safe_send_message(chat_id, "❌ Please provide a message to broadcast. Usage: /broadcast <message>")
            return

        # Get all users
        users = load_users()
        success_count = 0
        failed_count = 0

        # Send confirmation
        confirm_msg = safe_send_message(chat_id, f"Broadcasting message to {len(users)} users...")

        # Send broadcast
        for user_id in users:
            try:
                safe_send_message(int(user_id), f"📢 *Announcement*\n\n{broadcast_text}", parse_mode="Markdown")
                success_count += 1
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                failed_count += 1

        # Update confirmation message
        if confirm_msg:
            bot.edit_message_text(f"✅ Broadcast completed:\n• Sent to {success_count} users\n• Failed: {failed_count} users", chat_id, confirm_msg.message_id)
        else:
            safe_send_message(chat_id, f"✅ Broadcast completed:\n• Sent to {success_count} users\n• Failed: {failed_count} users")
    except Exception as e:
        safe_send_message(chat_id, f"❌ Error broadcasting message: {str(e)}")

# Add questions
@bot.message_handler(commands=['add'], func=lambda message: message.from_user.id == ADMIN_ID)
def request_quiz_file(message):
    chat_id = message.chat.id

    instruction = (
        "📝 *Upload Quiz Questions*\n\n"
        "Please upload a text file with questions for one of the following subjects:\n"
        "• Agriculture\n"
        "• GK\n"
        "• Hindi\n\n"
        "File should be named as <subject>.txt (e.g., agriculture.txt)\n\n"
        "Format for each question:\n"
        "Q: Question text\n"
        "A: Option A\n"
        "B: Option B\n"
        "C: Option C\n"
        "D: Option D\n"
        "ANS: Correct option (A/B/C/D)\n\n"
        "Separate questions with a blank line."
    )

    safe_send_message(chat_id, instruction, parse_mode="Markdown")

# Handle quiz file upload
@bot.message_handler(content_types=['document'], func=lambda message: message.from_user.id == ADMIN_ID)
def process_quiz_file(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name.lower()

    # Check if file is for a valid subject
    valid_subjects = ["agriculture.txt", "gk.txt", "hindi.txt"]

    if file_name not in valid_subjects:
        safe_send_message(chat_id, "❌ Invalid file name. Please name your file as agriculture.txt, gk.txt, or hindi.txt.")
        return

    # Download file
    downloaded_file = bot.download_file(file_info.file_path)

    # Process file content
    content = downloaded_file.decode('utf-8')
    questions = parse_questions(content)

    if not questions:
        safe_send_message(chat_id, "❌ No valid questions found in the file. Please check the format.")
        return

    # Get subject name
    subject = file_name.replace(".txt", "").capitalize()
    if subject == "Gk":
        subject = "GK"

    # Add questions to the database
    quizzes = load_quizzes()

    # Check for duplicates and add new questions
    all_questions = quizzes[subject].get("all_questions", [])
    new_questions = []  # Create a fresh new_questions list

    added_count = 0
    duplicate_count = 0

    for new_question in questions:
        # Check if question already exists in all_questions
        if not any(q["question"] == new_question["question"] for q in all_questions):
            all_questions.append(new_question)
            new_questions.append(new_question)
            added_count += 1
        else:
            duplicate_count += 1

    # Save updated questions
    quizzes[subject]["all_questions"] = all_questions
    quizzes[subject]["new_questions"] = new_questions  # Replace with just the newly added questions
    save_quizzes(quizzes)

    # Send confirmation
    confirmation = (
        f"✅ *File Processed Successfully*\n\n"
        f"Subject: {subject}\n"
        f"Total questions in file: {len(questions)}\n"
        f"New questions added: {added_count}\n"
        f"Duplicates skipped: {duplicate_count}\n"
        f"Total questions now: {len(all_questions)}" # Corrected this line
    )

    safe_send_message(chat_id, confirmation, parse_mode="Markdown")

    # Create two updated files - one for all questions, one for new questions
    all_file_content = ""
    for q in quizzes[subject]["all_questions"]:
        all_file_content += f"Q: {q['question']}\n"
        all_file_content += f"A: {q['options']['A']}\n"
        all_file_content += f"B: {q['options']['B']}\n"
        all_file_content += f"C: {q['options']['C']}\n"
        all_file_content += f"D: {q['options']['D']}\n"
        all_file_content += f"ANS: {q['correct']}\n\n"

    new_file_content = ""
    for q in quizzes[subject]["new_questions"]:
        new_file_content += f"Q: {q['question']}\n"
        new_file_content += f"A: {q['options']['A']}\n"
        new_file_content += f"B: {q['options']['B']}\n"
        new_file_content += f"C: {q['options']['C']}\n"
        new_file_content += f"D: {q['options']['D']}\n"
        new_file_content += f"ANS: {q['correct']}\n\n"

    # Send updated files
    with open(f"all_{file_name}", "w") as f:
        f.write(all_file_content)

    with open(f"new_{file_name}", "w") as f:
        f.write(new_file_content)

    # Send both files to admin
    with open(f"all_{file_name}", "rb") as f:
        bot.send_document(chat_id, f, caption=f"📄 All {subject} questions: {len(quizzes[subject]['all_questions'])} total questions")

    with open(f"new_{file_name}", "rb") as f:
        bot.send_document(chat_id, f, caption=f"📄 New {subject} questions: {len(quizzes[subject]['new_questions'])} newly added questions")

    # Clean up
    os.remove(f"all_{file_name}")
    os.remove(f"new_{file_name}")


# Function to parse questions from file
def parse_questions(content):
    questions = []
    current_question = None

    # Split content by lines
    lines = content.split('\n')

    for line in lines:
        line = line.strip()

        if not line:
            # Empty line, finish current question if exists
            if current_question and all(key in current_question for key in ["question", "options", "correct"]):
                questions.append(current_question)
            current_question = None
        elif line.startswith("Q:"):
            # Start new question
            current_question = {
                "question": line[2:].strip(),
                "options": {}
            }
        elif current_question and line.startswith("A:"):
            if "options" not in current_question:
                current_question["options"] = {}
            current_question["options"]["A"] = line[2:].strip()
        elif current_question and line.startswith("B:"):
            if "options" not in current_question:
                current_question["options"] = {}
            current_question["options"]["B"] = line[2:].strip()
        elif current_question and line.startswith("C:"):
            if "options" not in current_question:
                current_question["options"] = {}
            current_question["options"]["C"] = line[2:].strip()
        elif current_question and line.startswith("D:"):
            if "options" not in current_question:
                current_question["options"] = {}
            current_question["options"]["D"] = line[2:].strip()
        elif current_question and line.startswith("ANS:"):
            correct = line[4:].strip()
            if correct in ["A", "B", "C", "D"]:
                current_question["correct"] = correct

    # Add the last question if exists
    if current_question and all(key in current_question for key in ["question", "options", "correct"]):
        questions.append(current_question)

    return questions

# Error handling
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in user_state:
        if user_state[user_id] == "awaiting_utr":
            process_utr(message)
        elif user_state[user_id] == "input_name":
            process_name(message)
        elif user_state[user_id] == "verify_captcha":
            verify_captcha(message)
    else:
        # Check if user has already verified captcha and provided name
        if has_verified_captcha(user_id) and get_user_name(user_id):
            safe_send_message(chat_id, "Please use /start to access subscription options or /quiz to practice questions.")
        else:
            # Redirect to start
            start(message)

# Start the bot
if __name__ == "__main__":
    print("Starting Quiz Master Bot...")
    try:
        # Make sure all required files exist
        if not os.path.exists('users.json'):
            with open('users.json', 'w') as f:
                json.dump({}, f)
            print("Created users.json file")

        if not os.path.exists('names.json'):
            with open('names.json', 'w') as f:
                json.dump({}, f)
            print("Created names.json file")

        if not os.path.exists('quizzes.json'):
            with open('quizzes.json', 'w') as f:
                json.dump({
                    "Agriculture": {"all_questions":[], "new_questions": []},
                    "GK": {"all_questions": [], "new_questions": []},
                    "Hindi": {"all_questions": [], "new_questions": []}
                }, f)
            print("Created quizzes.json file")

        # Make sure the assets directory exists
        os.makedirs("attached_assets", exist_ok=True)

        print("Bot is running...")
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        print(f"Error in first polling attempt: {e}")
        # Try one more time with different polling parameters
        try:
            print("Retrying with different polling parameters...")
            bot.polling(none_stop=True, interval=2, timeout=60)
        except Exception as e2:
            print(f"Critical error starting bot: {e2}")