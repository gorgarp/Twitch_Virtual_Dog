# Twitch Virtual Dog Bot

## Introduction

The Twitch Virtual Dog Bot is an interactive bot designed for Twitch streams. It allows users to adopt, interact with, and train virtual dogs. The bot provides a variety of commands to enhance user engagement and create a fun, interactive experience in the chat.

## Features

- Adopt and name a virtual dog.
- Interact with your dog using various commands to earn experience points (XP) and bones (in-chat currency).
- Train your dog to learn new tricks.
- Dogs can evolve into different breeds as they level up.
- Daily login bonuses for users.
- Random events that reward XP.
- Leaderboard displaying the top 10 dogs.
- Inactivity messages for users who have been away.
- Earn bones for each minute spent watching the stream while it is live.

## Setup

### Prerequisites

- Python 3.7+
- Twitch account
- Twitch application for OAuth token

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/gorgarp/Twitch_Virtual_Dog.git
    cd Twitch_Virtual_Dog
    ```

2. Install required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory with the following content:
    ```plaintext
    # .env file

    # Twitch Bot OAuth Token
    IRC_TOKEN=your_twitch_bot_oauth_token

    # Twitch Application Client ID
    CLIENT_ID=your_twitch_app_client_id

    # Bot's Twitch Username
    BOT_NICK=your_bot_username

    # Channel to join
    CHANNEL=your_channel_name
    ```

4. Replace the placeholder values with your actual Twitch bot credentials.

5. Initialize the SQLite database:
    ```sh
    python database.py
    ```

6. Run the bot:
    ```sh
    python bot.py
    ```

## Usage

### Commands

#### General Commands

- `!help`: Provides a link to the bot's user guide.
- `!leaderboard`: Displays the top 10 dogs by level and XP.

#### Dog Adoption and Management

- `!adopt`: Adopt a new dog. Each user can only have one dog at a time.
- `!name <new_name>`: Rename your dog.
- `!status`: Check your dog's status, including name, breed, level, XP, and origin story.
- `!newstory`: Generate a new origin story for your dog.

#### Interaction Commands

- `!pet`: Pet your dog to earn XP.
- `!walk`: Walk your dog to earn XP.
- `!treat`: Give your dog a treat to earn XP.
- `!snuggle`: Snuggle with your dog to earn XP.
- `!play`: Play with your dog to earn XP.
- `!fetch`: Play fetch with your dog to earn XP. Occasionally, your dog may find bones in addition to earning XP.
- `!bones`: Check how many bones you have.

#### Training and Tricks

- `!train`: Teach your dog a new trick. Dogs can learn multiple tricks of varying difficulty.
- `!trick`: Perform a random trick that your dog knows. There is a chance the trick might fail.

#### Events and Bonuses

- `!party`: Participate in a group event where all dogs earn XP.

#### Moderation Commands

- `!nodog <username>`: Moderators can use this command to blacklist a user from adopting or interacting with a dog.

## Economy

- **Bones**: The in-chat currency earned at a rate of 5 bones per minute of watching the stream.
- **XP**: Experience points earned by interacting with your dog. Higher XP gain costs more bones.

### Leveling System

- Dogs level up as they earn XP.
- Each level corresponds to a unique breed, with 50 levels in total.
- The XP required to level up increases exponentially.

### Daily Bonus

- Users receive a daily bonus of bones for logging in each day.
- The bonus increases with consecutive daily logins and caps at 30 days.

### Random Events

- Random events occur every 15-20 minutes, rewarding XP.
- Events include interactions between dogs, finding new toys, competing in races, and more.

### Inactivity Messages

- If a user hasn't chatted in more than 12 hours, the bot sends a message about what their dog did while they were away.

### Group Events

- Occasionally, group events pop up in chat where users can type `!party` to attend a group outing to the dog park, gaining XP and listing the dogs that played together.

## Contributions

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please open an issue on the GitHub repository.

Enjoy playing with your virtual dog!
