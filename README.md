# DiscordBot

A Discord bot for automating outreach emails with resume attachment, role inference, and MongoDB tracking. The bot interacts with users via Discord commands, generates tailored email content, and sends emails with the appropriate resume attached.

---

## Features

- **Discord Integration:** Interact with the bot using commands (`!email`, `!confirm`, `!cancel`, `!update`, `!hello`).
- **Automated Email Generation:** Generates personalized outreach emails based on user input and inferred job role.
- **Resume Attachment:** Automatically selects and attaches the correct resume (software or data science) based on the inferred role.
- **Role Inference:** Uses keyword scoring to determine if the message is for a software or data science/machine learning role.
- **MongoDB Tracking:** Tracks the number of emails sent by each user.
- **Robust Error Handling:** Handles invalid input, missing environment variables, and database errors gracefully.
- **Email Preview and Editing:** Allows users to preview, confirm, update, or cancel emails before sending.

---

## Setup

### 1. Clone the Repository

```sh
git clone https://github.com/deepakbhagatiitr/DiscordBot.git
cd DiscordBot
```

### 2. Install Dependencies

```sh
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory and set the following variables:

```
DISCORD_TOKENNew=your_discord_bot_token
SMTP_EMAIL=your_gmail_address@gmail.com
SMTP_PASSWORD=your_gmail_app_password
MONGODB_URI=your_mongodb_connection_string
```

- `DISCORD_TOKENNew`: Your Discord bot token.
- `SMTP_EMAIL`: Gmail address used to send emails.
- `SMTP_PASSWORD`: Gmail app password (not your main password).
- `MONGODB_URI`: MongoDB connection string (e.g., from MongoDB Atlas).

### 4. Prepare Resumes

Place your resumes in the `resumes/` directory:
- `resumes/software_dev_resume.pdf`
- `resumes/data_science_resume.pdf`

---

## Usage

1. **Start the Bot:**

   ```sh
   python main.py
   ```

2. **Discord Commands:**
   - `!hello` — Check if the bot is running.
   - `!email` — Start the email sending process.
   - Paste your message as instructed (the bot will guide you).
   - `!confirm` — Confirm and send the email.
   - `!cancel` — Cancel the pending email.
   - `!update` — Edit the email before sending.

3. **Email Format:**
   - The bot will extract recipient, subject, and message from your input.
   - Example:
     ```
     to:recipient@example.com subject:Application for ML Role message:Hello, I am interested in...
     ```

---

## Project Structure

```
DiscordBot/
├── main.py                # Main Discord bot logic
├── emailsend.py           # Email sending utility
├── linkedin_outreach_email_generator.py # Email content generator
├── requirements.txt       # Python dependencies
├── resumes/
│   ├── software_dev_resume.pdf
│   └── data_science_resume.pdf
└── .env                   # Environment variables (not committed)
```

---

## Dependencies

- discord.py
- pymongo
- python-dotenv

Install all dependencies with:

```sh
pip install -r requirements.txt
```

---

## Notes

- Make sure to enable "Less secure app access" or use an App Password for Gmail SMTP.
- The bot uses MongoDB to track user activity; ensure your database is accessible.
- Only one pending email per user is tracked at a time.


---

## Contact

For questions or support, open an issue or contact