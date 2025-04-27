# Discord GenAI Study Companion Bot

The Discord GenAI Study Companion Bot is a personalized tutoring assistant built using Python and the Discord.py library. It leverages a mock GenAI model (simulating xAI's Grok 3) to provide real-time tutoring, interactive quizzes, and progress tracking for subjects like math and programming, all within a Discord server.

## Features
- **Tutoring**: Solves math problems (e.g., `!math 2x + 3 = 7`).
- **Quizzes**: Generates and evaluates quizzes (e.g., `!quiz math` with `!answer`).
- **Progress Tracking**: Monitors user stats (e.g., `!progress`).
- **Scalable Design**: Uses MongoDB for storing user data and Docker for deployment.

## Prerequisites
- Docker and Docker Compose installed.
- A MongoDB Atlas cluster (free tier works).
- A Discord bot token from the Discord Developer Portal.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/deepakbhagatiitr/GenStudy.git
cd GenStudy
```

### 2. Configure Environment Variables
- Create a `.env` file in the project root:
  ```bash
  nano .env
  ```
- Add the following (replace with your values):
  ```
  MONGODB_URI="mongodb+srv://your-username:your-password@cluster0.mongodb.net/"
  DISCORD_TOKEN="your-discord-bot-token"
  PORT=5000
  ```
- Save and exit (`Ctrl+O`, Enter, `Ctrl+X`).

### 3. Enable Intents
- Go to [https://discord.com/developers/applications](https://discord.com/developers/applications).
- Select your application, go to the **Bot** tab.
- Enable **Presence Intent**, **Server Members Intent**, and **Message Content Intent** under **Privileged Gateway Intents**.
- Save changes.

### 4. Invite the Bot to Your Server
- In the Developer Portal, go to **OAuth2 > URL Generator**.
- Select `bot` scope and permissions (`Send Messages`, `Read Message History`, `Use Slash Commands`).
- Copy the generated URL, open it, and add the bot to your server.

### 5. Run the Bot
- Build and start the services:
  ```bash
  docker-compose up --build
  ```
- Look for `Bot is ready as StudyBot#1234` in the logs to confirm activation.

## Usage
- **!math <problem>**: Get a solution (e.g., `!math 2x + 3 = 7`).
- **!quiz <subject>**: Start a quiz (e.g., `!quiz math`).
- **!answer <response>**: Submit a quiz answer (e.g., `!answer 5`).
- **!progress**: View your learning stats.

## Screenshots
- **Bot Interaction**: Example of `!math` command and response.
- **Quiz Interface**: Example of `!quiz` and `!answer` sequence.
- (Screenshots are stored in the `screenshots/` folder after capture.)

## Development
- **Dependencies**: Listed in `requirements.txt` (discord.py, pymongo).
- **Structure**: Uses Docker for containerization and MongoDB for data storage.
- **Mock GenAI**: Simulates xAI's Grok 3 for responses (replace with real API calls if available).

## Contributing
- Fork the repository.
- Create a feature branch (`git checkout -b feature-name`).
- Commit changes (`git commit -m "Add feature"`).
- Push and open a pull request.
- Improvements to the bot (e.g., real GenAI integration) are welcome!

## Troubleshooting
- **Bot Not Starting**: Check `.env` for correct token and URI; ensure intents are enabled.
- **MongoDB Errors**: Verify Atlas cluster connection and port 27017.
- **Intent Issues**: Re-enable intents in the Developer Portal and restart.

## License
MIT License.

## Acknowledgements
- Built as part of a project exploring GenAI in the SDLC.