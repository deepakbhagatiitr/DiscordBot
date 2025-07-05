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
from email import encodersP
import asyncio
import pymongo.errors
from emailsend import send_emailCustom
from linkedin_outreach_email_generator import generate_email

load_dotenv()

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global dictionary to track pending emails
pending_emails = {}

def get_resume_path(role):
    if "software" in role.lower() and "machine learning" not in role.lower():
        return "resumes/software_dev_resume.pdf"
    elif "data science" in role.lower() or "machine learning" in role.lower() or "intern" in role.lower():
        return "resumes/data_science_resume.pdf"
    return None

def infer_role(message):
    message_lower = message.lower()
    software_keywords = [
        "software", "developer", "engineer", "programmer", "backend", "frontend", "fullstack",
        "java", "python", "c++", "rust", "go", "node", "react", "spring", "django", "flask",
        "docker", "kubernetes", "microservices", "api", "cloud", "aws", "gcp", "sql", "async"
    ]
    data_science_keywords = [
        "data science", "data scientist", "machine learning", "deep learning", "artificial intelligence",
        "llm", "nlp", "computer vision", "pytorch", "tensorflow", "sklearn", "pandas", "sql",
        "data analysis", "model training", "ml engineer", "research", "intern", "internship"
    ]
    
    software_score = sum(2 if keyword in ["software", "developer", "backend", "rust", "engineer"] else 1 for keyword in software_keywords if keyword in message_lower)
    data_science_score = sum(2 if keyword in ["machine learning", "data science", "llm"] else 1 for keyword in data_science_keywords if keyword in message_lower)
    
    if data_science_score > software_score and any(keyword in message_lower for keyword in ["machine learning", "data science", "llm", "nlp", "computer vision", "pytorch", "tensorflow"]):
        return "machine learning"
    elif software_score >= data_science_score:
        return "software developer"
    return "unknown"

try:
    client = MongoClient(os.getenv('MONGODB_URI'))  # Fixed: Changed 'MONG_URI' to 'MONGODB_URI'
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
    user_id = str(message.author.id)
    
    if message.content.startswith('!'):
        command_name = message.content.split()[0][1:].lower()
        if command_name not in [cmd.name for cmd in bot.commands]:
            await message.channel.send("Please use correct command")
            return
        print(f'Message received: {message.content} from {message.author.name} in {message.channel} at {discord.utils.utcnow().strftime("%I:%M %p IST")}')
        await bot.process_commands(message)
        return

    if user_id in pending_emails and pending_emails[user_id].get('state') == 'waiting_for_message':
        if len(message.content) > 4000:
            await message.channel.send("Message is too long. Please shorten it.")
            del pending_emails[user_id]
            return

        email_match = re.search(r'to:(\S+@\S+\.\S+)', message.content) or re.search(r'(\S+@\S+\.\S+)', message.content)
        subject_match = re.search(r'subject:((?:(?!message:).)+)', message.content, re.IGNORECASE)
        message_match = re.search(r'message:([\s\S]+)', message.content, re.IGNORECASE)
        sender_email_match = re.search(r'(?:Contact|Email):?\s*(\S+@\S+\.\S+)', message.content, re.IGNORECASE)

        if not email_match:
            pending_emails[user_id] = {
                "state": "waiting_for_email",
                "channel_id": message.channel.id,
                "message_content": message.content,
                "timestamp": asyncio.get_event_loop().time()
            }
            await message.channel.send("Please provide the recipient email (e.g., to:recipient@example.com).")
            return

        to_email = email_match.group(1)
        subject = subject_match.group(1).strip() if subject_match else "LinkedIn Outreach"
        body = message_match.group(1).strip() if message_match else message.content
        from_email = sender_email_match.group(1) if sender_email_match else os.getenv('SMTP_EMAIL')

        if sender_email_match and to_email == sender_email_match.group(1):
            all_emails = re.findall(r'(\S+@\S+\.\S+)', message.content)
            to_email = next((email for email in all_emails if email != sender_email_match.group(1)), None)
            if not to_email:
                pending_emails[user_id] = {
                    "state": "waiting_for_email",
                    "channel_id": message.channel.id,
                    "message_content": message.content,
                    "from_email": from_email,
                    "timestamp": asyncio.get_event_loop().time()
                }
                await message.channel.send("Please provide the recipient email (e.g., to:recipient@example.com).")
                return

        role = infer_role(body)
        print(f"Inferred role: {role} for message: {body[:100]}...")

        software_keywords = [
            "software", "developer", "engineer", "programmer", "backend", "frontend", "fullstack",
            "java", "python", "c++", "rust", "go", "node", "react", "spring", "django", "flask",
            "docker", "kubernetes", "microservices", "api", "cloud", "aws", "gcp", "sql", "async"
        ]
        data_science_keywords = [
            "data science", "data scientist", "machine learning", "deep learning", "artificial intelligence",
            "llm", "nlp", "computer vision", "pytorch", "tensorflow", "sklearn", "pandas", "sql",
            "data analysis", "model training", "ml engineer", "research", "intern", "internship"
        ]
        skills = ""
        projects = ""
        if any(keyword in role.lower() for keyword in software_keywords) and "machine learning" not in role.lower():
            skills = "Python, Node.js, React, Django, Flutter, Docker, WebSockets, MongoDB, SQL, AWS"
            projects = (
                "1. E-Summit Website | E-Cell, IIT Roorkee \n"
                "   • Developed and maintained the E-Summit website for IIT Roorkee, ensuring a seamless and engaging user experience.\n"
                "   • Implemented responsive design, dynamic content, and smooth animations to enhance interactivity and visual appeal.\n"
                "   • Integrated event registrations, schedules, and interactive features in collaboration with the E-Cell team.\n\n"

                "2. Discord Bot for Cold Emailing \n"
                "   • Automated cold email generation and delivery based on LinkedIn job posts using SMTP and resume attachment.\n"
                "   • Used intelligent role inference via keyword scoring for tailored email content and resume selection.\n"
                "   • Integrated MongoDB to track and persist email activity with robust error handling.\n\n"

                "3. Enquiry-Based Learning App for IIT JEE Mathematics | Region Infinity Pvt. Ltd. \n"
                "   • Mentored by Prof. Vishal Vaibhav (IIT Delhi) in building a full-stack educational app with React, Node.js, and MongoDB.\n"
                "   • Developed frontend, backend, and a comprehensive admin panel for content and user management."
            )

        elif any(keyword in role.lower() for keyword in data_science_keywords):
            skills = "PyTorch, TensorFlow, Scikit-learn, Pandas, NLP, LLaMA, RAG, Rasa, Flask"
            projects = (
                "1. Skin Disease Prediction with Chatbot | Syntax Error, SDSLabs \n"
                "   • Built a deep learning model for image-based skin disease prediction.\n"
                "   • Integrated the model into a web interface with a LLaMA-powered AI chatbot for disease-related assistance.\n\n"

                "2. RAG-Based Chatbot with UI | Absolute Dimension Pvt. Ltd. \n"
                "   • Built a Retrieval-Augmented Generation (RAG) system combining IR and LLM for fact-based QA.\n"
                "   • Designed a UI for intuitive, real-time query interactions using external knowledge.\n\n"

                "3. Discord Bot for Cold Emailing \n"
                "   • Automated cold email generation and delivery based on LinkedIn job posts using SMTP and resume attachment.\n"
                "   • Used intelligent role inference via keyword scoring for tailored email content and resume selection.\n"
                "   • Integrated MongoDB to track and persist email activity with robust error handling."
            )

        try:
            email_content = generate_email(to_email, role, body, skills, projects)
            generated_subject = email_content.split('\n')[0].replace("Subject: ", "")
            generated_body = '\n'.join(email_content.split('\n')[1:])
        except Exception as e:
            await message.channel.send(f"Failed to generate email: {str(e)}")
            del pending_emails[user_id]
            return

        resume_path = get_resume_path(role)
        if not resume_path or not os.path.exists(resume_path):
            await message.channel.send("Could not determine role or find resume. Please mention 'software', 'backend', 'machine learning', or 'internship' in the message and ensure resumes are uploaded.")
            del pending_emails[user_id]
            return

        pending_emails[user_id] = {
            "to_email": to_email,
            "subject": subject if subject != "LinkedIn Outreach" else generated_subject,
            "body": generated_body,
            "resume_path": resume_path,
            "role": role,
            "from_email": from_email,
            "channel_id": message.channel.id,
            "timestamp": asyncio.get_event_loop().time()
        }

        preview = (
            f"**Email Preview**\n"
            f"**From**: {from_email}\n"
            f"**To**: {to_email}\n"
            f"**Subject**: {pending_emails[user_id]['subject']}\n"
            f"**Body**:\n{generated_body}\n"
            f"**Attachment**: {resume_path.split('/')[-1]}\n"
            f"Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
        )
        if len(preview) > 2000:
            metadata = (
                f"**Email Preview**\n"
                f"**From**: {from_email}\n"
                f"**To**: {to_email}\n"
                f"**Subject**: {pending_emails[user_id]['subject']}\n"
                f"**Attachment**: {resume_path.split('/')[-1]}\n"
            )
            body_part = f"**Body**:\n{generated_body}\n"
            options = "Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
            await message.channel.send(metadata)
            await message.channel.send(body_part)
            await message.channel.send(options)
        else:
            await message.channel.send(preview)
        return

    if user_id in pending_emails and pending_emails[user_id].get('state') == 'waiting_for_email':
        email_match = re.search(r'to:(\S+@\S+\.\S+)', message.content) or re.search(r'(\S+@\S+\.\S+)', message.content)
        if not email_match:
            await message.channel.send("Invalid email format. Please provide a valid recipient email (e.g., to:recipient@example.com).")
            return

        to_email = email_match.group(1)
        message_content = pending_emails[user_id].get('message_content', '')
        from_email = pending_emails[user_id].get('from_email', os.getenv('SMTP_EMAIL'))

        subject_match = re.search(r'subject:((?:(?!message:).)+)', message_content, re.IGNORECASE)
        message_match = re.search(r'message:([\s\S]+)', message_content, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "LinkedIn Outreach"
        body = message_match.group(1).strip() if message_match else message_content

        role = infer_role(body)
        print(f"Inferred role: {role} for message: {body[:100]}...")

        software_keywords = [
            "software", "developer", "engineer", "programmer", "backend", "frontend", "fullstack",
            "java", "python", "c++", "rust", "go", "node", "react", "spring", "django", "flask",
            "docker", "kubernetes", "microservices", "api", "cloud", "aws", "gcp", "sql", "async"
        ]
        data_science_keywords = [
            "data science", "data scientist", "machine learning", "deep learning", "artificial intelligence",
            "llm", "nlp", "computer vision", "pytorch", "tensorflow", "sklearn", "pandas", "sql",
            "data analysis", "model training", "ml engineer", "research", "intern", "internship"
        ]
        skills = ""
        projects = ""
        if any(keyword in role.lower() for keyword in software_keywords) and "machine learning" not in role.lower():
            skills = "Python, Node.js, React, Django, Flutter, Docker, WebSockets, MongoDB, SQL, AWS"
            projects = (
                "1. E-Summit Website | E-Cell, IIT Roorkee \n"
                "   • Developed and maintained the E-Summit website for IIT Roorkee, ensuring a seamless and engaging user experience.\n"
                "   • Implemented responsive design, dynamic content, and smooth animations to enhance interactivity and visual appeal.\n"
                "   • Integrated event registrations, schedules, and interactive features in collaboration with the E-Cell team.\n\n"

                "2. Discord Bot for Cold Emailing \n"
                "   • Automated cold email generation and delivery based on LinkedIn job posts using SMTP and resume attachment.\n"
                "   • Used intelligent role inference via keyword scoring for tailored email content and resume selection.\n"
                "   • Integrated MongoDB to track and persist email activity with robust error handling.\n\n"

                "3. Enquiry-Based Learning App for IIT JEE Mathematics | Region Infinity Pvt. Ltd. \n"
                "   • Mentored by Prof. Vishal Vaibhav (IIT Delhi) in building a full-stack educational app with React, Node.js, and MongoDB.\n"
                "   • Developed frontend, backend, and a comprehensive admin panel for content and user management."
            )

        elif any(keyword in role.lower() for keyword in data_science_keywords):
            skills = "PyTorch, TensorFlow, Scikit-learn, Pandas, NLP, LLaMA, RAG, Rasa, Flask"
            projects = (
                "1. Skin Disease Prediction with Chatbot | Syntax Error, SDSLabs \n"
                "   • Built a deep learning model for image-based skin disease prediction.\n"
                "   • Integrated the model into a web interface with a LLaMA-powered AI chatbot for disease-related assistance.\n\n"

                "2. RAG-Based Chatbot with UI | Absolute Dimension Pvt. Ltd. \n"
                "   • Built a Retrieval-Augmented Generation (RAG) system combining IR and LLM for fact-based QA.\n"
                "   • Designed a UI for intuitive, real-time query interactions using external knowledge.\n\n"

                "3. Discord Bot for Cold Emailing \n"
                "   • Automated cold email generation and delivery based on LinkedIn job posts using SMTP and resume attachment.\n"
                "   • Used intelligent role inference via keyword scoring for tailored email content and resume selection.\n"
                "   • Integrated MongoDB to track and persist email activity with robust error handling."
            )

        try:
            email_content = generate_email(to_email, role, body, skills, projects)
            generated_subject = email_content.split('\n')[0].replace("Subject: ", "")
            generated_body = '\n'.join(email_content.split('\n')[1:])
        except Exception as e:
            await message.channel.send(f"Failed to generate email: {str(e)}")
            del pending_emails[user_id]
            return

        resume_path = get_resume_path(role)
        if not resume_path or not os.path.exists(resume_path):
            await message.channel.send("Could not determine role or find resume. Please mention 'software', 'backend', 'machine learning', or 'internship' in the message and ensure resumes are uploaded.")
            del pending_emails[user_id]
            return

        pending_emails[user_id] = {
            "to_email": to_email,
            "subject": subject if subject != "LinkedIn Outreach" else generated_subject,
            "body": generated_body,
            "resume_path": resume_path,
            "role": role,
            "from_email": from_email,
            "channel_id": message.channel.id,
            "timestamp": asyncio.get_event_loop().time()
        }

        preview = (
            f"**Email Preview**\n"
            f"**From**: {from_email}\n"
            f"**To**: {to_email}\n"
            f"**Subject**: {pending_emails[user_id]['subject']}\n"
            f"**Body**:\n{generated_body}\n"
            f"**Attachment**: {resume_path.split('/')[-1]}\n"
            f"Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
        )
        if len(preview) > 2000:
            metadata = (
                f"**Email Preview**\n"
                f"**From**: {from_email}\n"
                f"**To**: {to_email}\n"
                f"**Subject**: {pending_emails[user_id]['subject']}\n"
                f"**Attachment**: {resume_path.split('/')[-1]}\n"
            )
            body_part = f"**Body**:\n{generated_body}\n"
            options = "Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit (run `!update` to get a copyable template)."
            await message.channel.send(metadata)
            await message.channel.send(body_part)
            await message.channel.send(options)
        else:
            await message.channel.send(preview)
        return

@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    await ctx.send(f"An error occurred: {error}")

@bot.command()
async def hello(ctx):
    print(f"Received !hello from {ctx.author.name}")
    await ctx.send(f"Hello, {ctx.author.name}! I'm ready to send LinkedIn emails!")

@bot.command()
async def email(ctx):
    user_id = str(ctx.author.id)
    pending_emails[user_id] = {
        "state": "waiting_for_message",
        "channel_id": ctx.channel.id,
        "timestamp": asyncio.get_event_loop().time()
    }
    await ctx.send("Please paste the email message in the input box.")

@bot.command()
async def update(ctx, *, text=None):
    user_id = str(ctx.author.id)
    if user_id not in pending_emails or pending_emails[user_id].get('state') in ['waiting_for_message', 'waiting_for_email']:
        await ctx.send("No pending email to update. Use `!email` first.")
        return
    if pending_emails[user_id]['channel_id'] != ctx.channel.id:
        await ctx.send("Please update in the same channel where you sent `!email`.")
        return

    email_data = pending_emails[user_id]

    if not text:
        header = "**Edit Your Email**\nClick to copy, paste into the input box, edit, and press Enter:\n"
        template = f"```plaintext\n!update to:{email_data['to_email']} subject:{email_data['subject']} message:{email_data['body']}\n```"
        
        if len(header + template) <= 2000:
            await ctx.send(header + template)
        else:
            await ctx.send(header)
            await ctx.send(template)
        return

    if len(text) > 4000:
        await ctx.send("Input is too long. Please shorten the subject or message.")
        return

    email_match = re.search(r'to:(\S+@\S+\.\S+)', text)
    subject_match = re.search(r'subject:((?:(?!message:).)+)', text, re.IGNORECASE)
    message_match = re.search(r'message:([\s\S]+)', text, re.IGNORECASE)

    if email_match:
        email_data['to_email'] = email_match.group(1).strip()
    if subject_match:
        email_data['subject'] = subject_match.group(1).strip()
    if message_match:
        email_data['body'] = message_match.group(1).strip()

    preview = (
        f"**Updated Email Preview**\n"
        f"**From**: {email_data['from_email']}\n"
        f"**To**: {email_data['to_email']}\n"
        f"**Subject**: {email_data['subject']}\n"
        f"**Body**:\n{email_data['body']}\n"
        f"**Attachment**: {email_data['resume_path'].split('/')[-1]}\n"
        f"Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit again (run `!update` to get a copyable template)."
    )
    if len(preview) > 2000:
        metadata = (
            f"**Updated Email Preview**\n"
            f"**From**: {email_data['from_email']}\n"
            f"**To**: {email_data['to_email']}\n"
            f"**Subject**: {email_data['subject']}\n"
            f"**Attachment**: {email_data['resume_path'].split('/')[-1]}\n"
        )
        body_part = f"**Body**:\n{email_data['body']}\n"
        options = "Send this email? Reply with `!confirm` to send, `!cancel` to cancel, or `!update` to edit again (run `!update` to get a copyable template)."
        await ctx.send(metadata)
        await ctx.send(body_part)
        await ctx.send(options)
    else:
        await ctx.send(preview)

@bot.command()
async def confirm(ctx):
    user_id = str(ctx.author.id)
    if user_id not in pending_emails or pending_emails[user_id].get('state') in ['waiting_for_message', 'waiting_for_email']:
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
            email_data['resume_path'],
            from_email=email_data['from_email']
        )
        print(f"Email sent successfully to {email_data['to_email']}")
        try:
            result = users.update_one(
                {'_id': user_id},
                {'$inc': {'emails_sent': 1}},
                upsert=True
            )
            print(f"MongoDB update result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id}")
            doc = users.find_one({'_id': user_id})
            if doc and 'emails_sent' in doc:
                print(f"Verified document: {doc}")
                await ctx.send(f"Email sent to {email_data['to_email']} for {email_data['role']}! Emails sent: {doc['emails_sent']}")
            else:
                print("MongoDB verification failed: Document not found or invalid")
                await ctx.send("Email sent, but failed to verify email count in database.")
        except pymongo.errors.PyMongoError as mongo_err:
            print(f"MongoDB update error: {str(mongo_err)}")
            await ctx.send(f"Email sent, but failed to update database: {str(mongo_err)}")
        del pending_emails[user_id]
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
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

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKENNew')
    if token:
        token = token.strip()
    print(f"Loaded DISCORD_TOKEN: {token}")
    bot.run(token)