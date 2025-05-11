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
intents.message_content = True  # Required for reading command messages
bot = commands.Bot(command_prefix='!', intents=intents)

pending_emails = {}


# Resume selection based on role
def get_resume_path(role):
    if "software" in role.lower():
        return "resumes/software_dev_resume.pdf"
    elif "data science" in role.lower() or "machine learning" in role.lower():
        return "resumes/data_science_resume.pdf"
    return None


client = MongoClient(os.getenv('MONGODB_URI'))
db = client['studybot']
users = db['users']

async def cleanup_pending_emails():
    while True:
        current_time = asyncio.get_event_loop().time()
        expired = [user_id for user_id, data in pending_emails.items() if current_time - data['timestamp'] > 300]
        for user_id in expired:
            del pending_emails[user_id]
        await asyncio.sleep(60) 

@bot.event
async def on_ready():
    print(f'Bot is ready as {bot.user}')
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
    print(f'Message received: {message.content} from {message.author.name} in {message.channel}')  
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
        await ctx.send("Could not find resume. Please specify 'software' or 'data science' in role and ensure resumes are uploaded.")
        return

    pending_emails[user_id] = {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "resume_path": resume_path,
        "channel_id": ctx.channel.id,
        "timestamp": asyncio.get_event_loop().time()
    }


    preview = (
        f"**Email Preview**\n"
        f"**To**: {to_email}\n"
        f"**Subject**: {subject}\n"
        f"**Body**:\n{body}\n"
        f"**Attachment**: {resume_path.split('/')[-1]}\n"
        f"Send this email? Reply with `!confirm` to send or `!cancel` to cancel."
    )
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
        await ctx.send(f"Email sent to {email_data['to_email']} for {email_data['subject'].split(' at ')[0]} at {email_data['subject'].split(' at ')[-1]}!")
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