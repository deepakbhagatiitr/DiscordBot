import discord
from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
import asyncio
from emailsend import send_emailCustom
from linkedin_outreach_email_generator import generate_email

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

pending_emails = {}

# Resume selection based on role
def get_resume_path(role):
    if "software" in role.lower():
        return "resumes/software_dev_resume.pdf"
    elif "data science" in role.lower() or "machine learning" in role.lower():
        return "resumes/data_science_resume.pdf"
    return None

# MongoDB setup
try:
    client = MongoClient("mongodb+srv://deepak988088:deepak123@cluster0.nnepi5n.mongodb.net/")
    client.server_info()
    db = client['studybot']
    users = db['users']
except Exception as e:
    print(f"Failed to connect to MongoDB: {str(e)}")
    raise SystemExit("Exiting due to MongoDB connection failure.")

async def cleanup_pending_emails():
    while True:
        current_time = asyncio.get_event_loop().time()
        expired = [user_id for user_id, data in pending_emails.items() if current_time - data['timestamp'] > 300]
        for user_id in expired:
            del pending_emails[user_id]
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user} at {discord.utils.utcnow().strftime("%I:%M %p IST, %B %d, %Y")}')
    print(f"MongoDB connected: {client is not None}")
    print(f'Connected to {len(bot.guilds)} servers')
    for guild in bot.guilds:
        print(f' - {guild.name} (ID: {guild.id})')
    try:
        client.server_info()
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    bot.loop.create_task(cleanup_pending_emails())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith('!'):
        command_name = message.content.split()[0][1:].lower()
        if command_name not in [cmd.name for cmd in bot.commands]:
            await message.channel.send("Please use correct command")
            return
    print(f'Message received: {message.content} from {message.author.name} in {message.channel} at {discord.utils.utcnow().strftime("%I:%M %p IST")}')
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    await ctx.send(f"An error occurred: {error}")

@bot.command()
async def hello(ctx):
    print(f"Received !hello from {ctx.author.name}")
    await ctx.send(f"Hello, {ctx.author.name}! I'm ready to send LinkedIn emails!")

@bot.command()
async def email(ctx, *, text):
    user_id = str(ctx.author.id)

    email_match = re.search(r'to:(\S+@\S+)', text)
    role_match = re.search(r'role:([\w\s]+)', text, re.IGNORECASE)
    message_match = re.search(r'message:([\w\s,.!🚨🎯✉️📭:–-]+)', text, re.IGNORECASE)

    if not email_match:
        await ctx.send("Please provide a valid email (e.g., to:recipient@example.com).")
        return

    to_email = email_match.group(1)
    role = role_match.group(1).strip() if role_match else "unknown"
    message = message_match.group(1).strip() if message_match else "your work"

    software_keywords = ["software", "developer", "development", "engineer"]
    data_science_keywords = ["data science", "machine learning", "ai", "artificial intelligence"]
    
    skills = ""
    projects = ""
    
    if any(keyword in role.lower() for keyword in software_keywords):
        skills = "JavaScript, Python, ReactJS, Node.js, MongoDB"
        projects = (
            "1. Enquiry-Based Learning App for IIT JEE Mathematics: Full-stack app with React, Node.js, MongoDB for IIT JEE preparation, mentored by Prof. Vishal Vaibhav, IIT Delhi\n"
            "2. IPR Website for IIT Roorkee: Built with Next.js, Node.js, MongoDB, integrated email (Nodemailer) and file uploads (Multer)"
        )
    elif any(keyword in role.lower() for keyword in data_science_keywords):
        skills = "TensorFlow, Scikit-learn, Rasa, LLaMA, RAG"
        projects = (
            "1. RAG Model with Interactive UI: Combined retrieval and generation for real-time fact-based Q&A with a seamless UI\n"
            "2. Skin Disease Prediction with Chatbot: Deep learning model for image-based skin disease classification, integrated with a LLaMA-based chatbot"
        )
    else:
        skills = "Python, AI/ML expertise"
        projects = (
            "1. NutriBot – AI-Powered Nutrition Chatbot: Built with Rasa, Flask, Docker for personalized diet plans using Nutritionix API\n"
            "2. Enquiry-Based Learning App for IIT JEE Mathematics: Full-stack app with React, Node.js, MongoDB for IIT JEE preparation"
        )

    try:
        email_content = generate_email(to_email, role, message, skills, projects)
        subject = email_content.split('\n')[0].replace("Subject: ", "")
        body = '\n'.join(email_content.split('\n')[1:])
    except Exception as e:
        await ctx.send(f"Failed to generate email: {str(e)}")
        return

    resume_path = get_resume_path(role)
    if not resume_path or not os.path.exists(resume_path):
        await ctx.send("Please specify 'software' or 'data science' in role and ensure resumes are uploaded.")
        return

    pending_emails[user_id] = {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "resume_path": resume_path,
        "role": role,
        "channel_id": ctx.channel.id,
        "timestamp": asyncio.get_event_loop().time()
    }

    preview = (
        f"**Email Preview**\n"
        f"**To**: {to_email}\n"
        f"**Subject**: {subject}\n"
        f"**Body**:\n{body}\n"
        f"**Attachment**: {resume_path.split('/')[-1]}\n"
        f"Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
    )
    if len(preview) > 2000:
        metadata = (
            f"**Email Preview**\n"
            f"**To**: {to_email}\n"
            f"**Subject**: {subject}\n"
            f"**Attachment**: {resume_path.split('/')[-1]}\n"
        )
        body_part = f"**Body**:\n{body}\n"
        options = "Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
        await ctx.send(metadata)
        await ctx.send(body_part)
        await ctx.send(options)
    else:
        await ctx.send(preview)

@bot.command()
async def update(ctx, *, text=None):
    user_id = str(ctx.author.id)
    if user_id not in pending_emails:
        await ctx.send("No pending email to update. Use `!email` first.")
        return
    if pending_emails[user_id]['channel_id'] != ctx.channel.id:
        await ctx.send("Please update in the same channel where you sent `!email`.")
        return

    email_data = pending_emails[user_id]

    # If no text provided, show current email as copyable template
    if not text:
        header = "**Edit Your Email**\nClick to copy, paste into the input box, edit, and press Enter:\n"
        template = f"```plaintext\n!update to:{email_data['to_email']} subject:{email_data['subject']} message:{email_data['body']}\n```"
        
        if len(header + template) <= 2000:
            await ctx.send(header + template)
        else:
            await ctx.send(header)
            await ctx.send(template)
        return

    # Validate input length
    if len(text) > 4000:
        await ctx.send("Input is too long. Please shorten the subject or message.")
        return

    # Parse input for updates
    email_match = re.search(r'to:(\S+@\S+)', text)
    subject_match = re.search(r'subject:((?:(?!message:).)+)', text, re.IGNORECASE)
    message_match = re.search(r'message:([\s\S]+)', text, re.IGNORECASE)

    if not subject_match and not message_match:
        await ctx.send("Please provide at least a new subject (subject:...) or message (message:...) to update.")
        return

    # Validate to_email
    if email_match:
        if email_match.group(1) != email_data['to_email']:
            await ctx.send("The 'to' email cannot be changed. Use the original email address.")
            return
    else:
        await ctx.send("Please include the original 'to' email (e.g., to:recruiter@google.com).")
        return

    # Update pending email
    if subject_match:
        email_data['subject'] = subject_match.group(1).strip()
    if message_match:
        email_data['body'] = message_match.group(1).strip()

    # Send updated preview
    preview = (
        f"**Updated Email Preview**\n"
        f"**To**: {email_data['to_email']}\n"
        f"**Subject**: {email_data['subject']}\n"
        f"**Body**:\n{email_data['body']}\n"
        f"**Attachment**: {email_data['resume_path'].split('/')[-1]}\n"
        f"Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit again (run `!update` to get a copyable template)."
    )
    if len(preview) > 2000:
        metadata = (
            f"**Updated Email Preview**\n"
            f"**To**: {email_data['to_email']}\n"
            f"**Subject**: {email_data['subject']}\n"
            f"**Attachment**: {email_data['resume_path'].split('/')[-1]}\n"
        )
        body_part = f"**Body**:\n{email_data['body']}\n"
        options = "Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
        await ctx.send(metadata)
        await ctx.send(body_part)
        await ctx.send(options)
    else:
        await ctx.send(preview)

@bot.command()
async def confirm(ctx):
    user_id = str(ctx.author.id)
    if user_id not in pending_emails:
        await ctx.send("No pending email to confirm. Use `!email` first.")
        return
    if pending_emails[user_id]['channel_id'] != ctx.channel.id:
        await ctx.send("Please confirm in the same channel where you sent `!email`.")
        return

    email_data = pending_emails[user_id]
    try:
        send_emailCustom(
            email_data['to_email'],
            email_data['subject'],
            email_data['body'],
            email_data['resume_path']
        )
        users.update_one(
            {'_id': user_id},
            {'$inc': {'emails_sent': 1}},
            upsert=True
        )
        await ctx.send(f"Email sent to {email_data['to_email']} for {email_data['role']}!")
        del pending_emails[user_id]
    except Exception as e:
        await ctx.send(f"Failed to send email: {str(e)}")

@bot.command()
async def cancel(ctx):
    user_id = str(ctx.author.id)
    if user_id not in pending_emails:
        await ctx.send("No pending email to cancel. Use `!email` first.")
        return
    if pending_emails[user_id]['channel_id'] != ctx.channel.id:
        await ctx.send("Please cancel in the same channel where you sent `!email`.")
        return

    del pending_emails[user_id]
    await ctx.send("Email sending cancelled.")

token = os.getenv('DISCORD_TOKENNew')
if token:
    token = token.strip()
print(f"Loaded DISCORD_TOKEN: {token}")
bot.run(token)