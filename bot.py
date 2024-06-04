import os
import random
import sqlite3
from twitchio.ext import commands, routines
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

load_dotenv()

# Load environment variables from .env file
IRC_TOKEN = os.getenv('IRC_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
BOT_NICK = os.getenv('BOT_NICK')
CHANNEL = os.getenv('CHANNEL')

# Register adapters and converters for datetime
def adapt_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')

def convert_datetime(dt_str):
    return datetime.strptime(dt_str.decode('utf-8'), '%Y-%m-%d %H:%M:%S.%f')

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

# List of dog breeds for leveling up
breeds = ["Chihuahua", "Pomeranian", "Yorkshire Terrier", "Maltese", "Dachshund", "Shih Tzu", "Toy Poodle",
          "Boston Terrier", "French Bulldog", "Miniature Pinscher", "Cavalier King Charles Spaniel", "Miniature Schnauzer",
          "Bichon Frise", "Shetland Sheepdog", "Beagle", "Cocker Spaniel", "Border Terrier", "West Highland White Terrier",
          "Pembroke Welsh Corgi", "Jack Russell Terrier", "Bulldog", "American Pit Bull Terrier", "Whippet",
          "Australian Cattle Dog", "Bull Terrier", "Samoyed", "Siberian Husky", "Boxer", "Dalmatian", "Standard Schnauzer",
          "Shar Pei", "Australian Shepherd", "Border Collie", "Shiba Inu", "Labrador Retriever", "Golden Retriever",
          "German Shepherd", "Rottweiler", "Doberman Pinscher", "Bernese Mountain Dog", "Newfoundland", "Saint Bernard",
          "Great Dane", "Irish Wolfhound", "Alaskan Malamute", "Leonberger", "Tibetan Mastiff", "Mastiff", "Great Pyrenees",
          "Scottish Deerhound"]

# List of happy origin stories for dogs
origin_stories = [
    "Your dog was rescued from a shelter and found a forever home with you.",
    "Your dog was a stray who wandered into your yard and decided to stay.",
    "Your dog was born on a farm and loves to run in open fields.",
    "Your dog was the runt of the litter but has the biggest heart.",
    "Your dog was a gift from a dear friend.",
    "Your dog was adopted during a special event at the local pet store.",
    "Your dog was saved from a difficult situation and has been your loyal companion ever since.",
    "Your dog was the star of a local dog show before retiring to live with you.",
    "Your dog was a beloved pet of an elderly neighbor who passed away.",
    "Your dog was adopted from a rescue organization dedicated to its breed.",
    "Your dog was adopted during a fun pet adoption fair.",
    "Your dog was born in a big city but loves the countryside now.",
    "Your dog was a therapy dog before coming to live with you.",
    "Your dog was a service dog in training that didn't quite make the cut.",
    "Your dog joined your family during a cheerful holiday season.",
    "Your dog was adopted from a loving foster home.",
    "Your dog was found playing joyfully at the park and decided to join your family.",
    "Your dog was the star performer at a local circus before retiring to a cozy home.",
    "Your dog was part of a happy traveling carnival before finding a permanent home with you.",
    "Your dog was the mascot of a friendly local fire department.",
    "Your dog was born in a snowy region and loves cold weather.",
    "Your dog was found playing with other dogs in the mountains and decided to join your family."
]

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=IRC_TOKEN, prefix='!', initial_channels=[CHANNEL])
        self.db_conn = sqlite3.connect('twitch_dog_bot.db', detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_cursor = self.db_conn.cursor()
        self.init_db()
        self.sent_messages = set()
        self.online_status = True
        self.watch_time = {}

    def init_db(self):
        # Initialize the database and create tables if they do not exist
        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogs (
            id INTEGER PRIMARY KEY,
            user TEXT NOT NULL,
            name TEXT NOT NULL,
            breed TEXT NOT NULL,
            level INTEGER NOT NULL,
            xp INTEGER NOT NULL,
            origin_story TEXT NOT NULL
        )
        ''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS tricks (
            id INTEGER PRIMARY KEY,
            dog_id INTEGER,
            trick_name TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            xp_reward INTEGER NOT NULL,
            FOREIGN KEY(dog_id) REFERENCES dogs(id)
        )
        ''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            bones INTEGER NOT NULL,
            daily_streak INTEGER NOT NULL,
            last_login DATETIME,
            last_interaction DATETIME
        )
        ''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY,
            dog1_id INTEGER,
            dog2_id INTEGER,
            interactions INTEGER NOT NULL,
            FOREIGN KEY(dog1_id) REFERENCES dogs(id),
            FOREIGN KEY(dog2_id) REFERENCES dogs(id)
        )
        ''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            frequency INTEGER NOT NULL
        )
        ''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )
        ''')

        self.db_conn.commit()

    async def event_ready(self):
        # Event triggered when the bot is connected and ready
        print(f'Logged in as | {self.nick}')
        self.event_routine.start()
        self.bones_routine.start()
        self.online_check.start()

    async def event_message(self, message):
        # Event triggered on every message received
        if not message.author:
            return
        if message.author.name.lower() == self.nick.lower():
            return

        await self.handle_commands(message)

        if message.content in self.sent_messages:
            self.sent_messages.remove(message.content)

        if self.online_status:
            self.watch_time[message.author.name] = datetime.now()
        await self.handle_inactivity_and_daily_bonus(message.author.name)

    async def event_usernotice_subscription(self, message):
        # Handle new subscriptions
        user = message.author.name
        if self.online_status:
            self.watch_time[user] = datetime.now()

    async def event_usernotice_subgift(self, message):
        # Handle gifted subscriptions
        user = message.tags['msg-param-recipient-display-name']
        if self.online_status:
            self.watch_time[user] = datetime.now()

    async def event_userjoin(self, user):
        # Handle user joining the channel
        if self.online_status:
            self.watch_time[user.name] = datetime.now()

    async def event_userpart(self, user):
        # Handle user leaving the channel
        if user.name in self.watch_time:
            del self.watch_time[user.name]

    @routines.routine(minutes=1)
async def bones_routine(self):
    # Award bones to users every minute while the stream is live
    if self.online_status:
        for user in self.watch_time:
            self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
            bones = self.db_cursor.fetchone()
            if bones:
                new_bones = bones[0] + 1
                self.db_cursor.execute("UPDATE users SET bones=? WHERE username=?", (new_bones, user))
            else:
                self.db_cursor.execute("INSERT INTO users (username, bones, daily_streak, last_login, last_interaction) VALUES (?, ?, ?, ?, ?)",
                                       (user, 1, 0, datetime.now(), datetime.now()))
        self.db_conn.commit()


    @routines.routine(minutes=5)
    async def online_check(self):
        # Check if the stream is online
        stream = await self.fetch_streams(user_logins=[CHANNEL])
        self.online_status = bool(stream)

    @commands.command(name='adopt')
    async def adopt(self, ctx):
        # Command to adopt a new dog
        user = ctx.author.name

        self.db_cursor.execute("SELECT * FROM blacklist WHERE username=?", (user,))
        if self.db_cursor.fetchone():
            await self.retry_send_message(f"{user}, you are blacklisted and cannot adopt a dog.")
            return

        self.db_cursor.execute("SELECT * FROM dogs WHERE user=?", (user,))
        if self.db_cursor.fetchone():
            await self.retry_send_message(f"{user}, you already have a dog!")
            return

        name = f"Dog{random.randint(1000, 9999)}"
        breed = breeds[0]
        level = 1
        xp = 0
        origin_story = random.choice(origin_stories)

        self.db_cursor.execute("INSERT INTO dogs (user, name, breed, level, xp, origin_story) VALUES (?, ?, ?, ?, ?, ?)",
                               (user, name, breed, level, xp, origin_story))
        self.db_conn.commit()

        self.db_cursor.execute("INSERT INTO users (username, bones, daily_streak, last_login, last_interaction) VALUES (?, ?, ?, ?, ?)",
                               (user, 0, 0, datetime.now(), datetime.now()))
        self.db_conn.commit()

        await self.retry_send_message(f"{user} adopted a dog named {name}! {origin_story}")

    @commands.command(name='name')
    async def name(self, ctx):
        # Command to rename the user's dog
        user = ctx.author.name
        new_name = ctx.message.content.split(' ', 1)[1]
        self.db_cursor.execute("UPDATE dogs SET name=? WHERE user=?", (new_name, user))
        self.db_conn.commit()
        await self.retry_send_message(f"{user}, your dog's name has been changed to {new_name}!")

    @commands.command(name='status')
    async def status(self, ctx):
        # Command to check the status of the user's dog
        user = ctx.author.name
        self.db_cursor.execute("SELECT * FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if dog:
            await self.retry_send_message(f"{user}, your dog's name is {dog[2]}, breed: {dog[3]}, level: {dog[4]}, XP: {dog[5]}, origin story: {dog[6]}")
        else:
            await self.retry_send_message(f"{user}, you don't have a dog yet! Use !adopt to get one.")

    @commands.command(name='newstory')
    async def newstory(self, ctx):
        # Command to generate a new origin story for the user's dog
        user = ctx.author.name
        origin_story = random.choice(origin_stories)
        self.db_cursor.execute("UPDATE dogs SET origin_story=? WHERE user=?", (origin_story, user))
        self.db_conn.commit()
        await self.retry_send_message(f"{user}, your dog's new origin story is: {origin_story}")

    @commands.command(name='pet')
    async def pet(self, ctx):
        # Command to pet the user's dog and earn XP
        await self.interact(ctx, 'pet')

    @commands.command(name='walk')
    async def walk(self, ctx):
        # Command to walk the user's dog and earn XP
        await self.interact(ctx, 'walk')

    @commands.command(name='treat')
    async def treat(self, ctx):
        # Command to give the user's dog a treat and earn XP
        await self.interact(ctx, 'treat')

    @commands.command(name='snuggle')
    async def snuggle(self, ctx):
        # Command to snuggle with the user's dog and earn XP
        await self.interact(ctx, 'snuggle')

    @commands.command(name='play')
    async def play(self, ctx):
        # Command to play with the user's dog and earn XP
        await self.interact(ctx, 'play')

    @commands.command(name='fetch')
    async def fetch(self, ctx):
        # Command to play fetch with the user's dog and earn XP and possibly bones
        await self.interact(ctx, 'fetch', is_fetch=True)

    @commands.command(name='bones')
    async def bones(self, ctx):
        # Command to check the number of bones the user has
        user = ctx.author.name
        self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
        bones = self.db_cursor.fetchone()
        if bones:
            await self.retry_send_message(f"{user}, you have {bones[0]} bones.")
        else:
            await self.retry_send_message(f"{user}, you don't have any bones yet!")

    async def interact(self, ctx, interaction_type, is_fetch=False):
        # Function to handle various interactions with the user's dog
        user = ctx.author.name
        self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
        bones = self.db_cursor.fetchone()
        if not bones:
            await self.retry_send_message(f"{user}, you don't have enough bones to {interaction_type} your dog.")
            return

        xp_gain = random.randint(5, 15)
        bones_gain = 0
        if is_fetch:
            if random.random() < 0.1:
                bones_gain = random.randint(5, 15)
            else:
                xp_gain = random.randint(10, 30)

        bones_cost = max(1, xp_gain // 5)
        if bones[0] < bones_cost:
            await self.retry_send_message(f"{user}, you don't have enough bones to {interaction_type} your dog. You need {bones_cost} bones.")
            return

        self.db_cursor.execute("UPDATE dogs SET xp = xp + ? WHERE user=?", (xp_gain, user))
        self.db_cursor.execute("UPDATE users SET bones = bones - ? WHERE username=?", (bones_cost, user))
        if bones_gain > 0:
            self.db_cursor.execute("UPDATE users SET bones = bones + ? WHERE username=?", (bones_gain, user))
        self.db_conn.commit()

        interaction_message = "play fetch with" if is_fetch else interaction_type
        await self.retry_send_message(f"{user}, you {interaction_message} your dog and earned {xp_gain} XP for {bones_cost} bones!")
        if bones_gain > 0:
            await self.retry_send_message(f"{user}, you also found {bones_gain} bones!")

        await self.check_level_up(user)

    async def check_level_up(self, user):
        # Function to check if the user's dog has leveled up
        self.db_cursor.execute("SELECT level, xp, breed FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if dog:
            level = dog[0]
            xp = dog[1]
            current_breed = dog[2]
            next_level_xp = (level ** 2) * 50
            if xp >= next_level_xp:
                new_level = level + 1
                new_breed = breeds[new_level - 1] if new_level <= len(breeds) else breeds[-1]
                self.db_cursor.execute("UPDATE dogs SET level = ?, breed = ? WHERE user=?", (new_level, new_breed, user))
                self.db_conn.commit()
                await self.retry_send_message(f"{user}, your dog has evolved! They went from a {current_breed} to a {new_breed}! Keep playing with them to keep them evolving!")

    @routines.routine(minutes=15)
    async def event_routine(self):
        # Routine to handle random events
        await self.handle_events()

    async def handle_events(self):
        # Function to handle random events between dogs
        self.db_cursor.execute("SELECT user, name FROM dogs")
        dogs = self.db_cursor.fetchall()
        if len(dogs) < 2:
            return

        dog1, dog2 = random.sample(dogs, 2)
        event = random.choice([
            f"{dog1[0]}, your dog {dog1[1]} met {dog2[0]}'s dog {dog2[1]} at the park! They became best of friends +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} found a new toy at the park and shared it with {dog2[0]}'s dog {dog2[1]} +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} competed in a race! They both had fun and earned +XP!",
            f"{dog1[0]}, your dog {dog1[1]} learned a new trick from {dog2[0]}'s dog {dog2[1]} +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} shared a delicious treat at the park +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} played a game of tug-of-war +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} helped {dog2[0]}'s dog {dog2[1]} find a lost ball +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} took a nap together under a tree +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} chased butterflies together +XP for both of you!",
            f"{dog1[0]}, your dog {dog1[1]} and {dog2[0]}'s dog {dog2[1]} went on an adventure through the park +XP for both of you!"
        ])
        self.loop.create_task(self.retry_send_message(event))

        self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog1[0],))
        self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog2[0],))
        self.db_conn.commit()

    async def handle_inactivity_and_daily_bonus(self, user):
        # Function to handle daily bonuses and inactivity messages
        activities = [
            "chased butterflies in the garden",
            "played with a new toy",
            "took a long nap under a tree",
            "dug a small hole in the yard",
            "barked at the mailman",
            "learned a new trick on its own",
            "played fetch with a neighbor",
            "explored a hidden corner of the house",
            "watched squirrels from the window",
            "had a little snack"
        ]
        
        self.db_cursor.execute("SELECT last_interaction FROM users WHERE username=?", (user,))
        last_interaction = self.db_cursor.fetchone()
        if last_interaction:
            last_interaction = last_interaction[0]
            if isinstance(last_interaction, str):
                last_interaction = datetime.strptime(last_interaction, '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - last_interaction > timedelta(hours=24):
                daily_streak = self.update_daily_streak(user)
                bones_reward = min(daily_streak, 30)
                self.db_cursor.execute("UPDATE users SET last_interaction = ?, bones = bones + ? WHERE username=?", 
                                       (datetime.now(), bones_reward, user))
                self.db_conn.commit()
                await self.retry_send_message(f"{user}, you received your daily bonus of {bones_reward} bones! Daily streak: {daily_streak} days.")
            if datetime.now() - last_interaction > timedelta(hours=12):
                activity = random.choice(activities)
                await self.retry_send_message(f"{user}, your dog missed you! They {activity} while you were away.")
        else:
            self.db_cursor.execute("INSERT INTO users (username, bones, daily_streak, last_login, last_interaction) VALUES (?, ?, ?, ?, ?)",
                                   (user, 0, 0, datetime.now(), datetime.now()))
            self.db_conn.commit()

    def update_daily_streak(self, user):
        # Function to update the daily login streak for the user
        self.db_cursor.execute("SELECT daily_streak FROM users WHERE username=?", (user,))
        daily_streak = self.db_cursor.fetchone()[0]
        daily_streak += 1
        self.db_cursor.execute("UPDATE users SET daily_streak = ? WHERE username=?", (daily_streak, user))
        self.db_conn.commit()
        return daily_streak

    @commands.command(name='trick')
    async def trick(self, ctx):
        # Command to perform a random trick that the user's dog knows
        user = ctx.author.name
        self.db_cursor.execute("SELECT id FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if not dog:
            await self.retry_send_message(f"{user}, you don't have a dog yet! Use !adopt to get one.")
            return

        dog_id = dog[0]
        self.db_cursor.execute("SELECT trick_name, difficulty, xp_reward FROM tricks WHERE dog_id=?", (dog_id,))
        tricks = self.db_cursor.fetchall()
        if not tricks:
            await self.retry_send_message(f"{user}, your dog doesn't know any tricks yet! Use !train to teach some.")
            return

        trick = random.choice(tricks)
        trick_name, difficulty, xp_reward = trick
        bones_cost = max(1, xp_reward // 5)
        self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
        bones = self.db_cursor.fetchone()[0]
        if bones < bones_cost:
            await self.retry_send_message(f"{user}, you don't have enough bones to perform the trick '{trick_name}'. You need {bones_cost} bones.")
            return

        success = random.random() < 0.75
        if success:
            xp_gain = xp_reward
            self.db_cursor.execute("UPDATE dogs SET xp = xp + ? WHERE id=?", (xp_gain, dog_id))
            self.db_cursor.execute("UPDATE users SET bones = bones - ? WHERE username=?", (bones_cost, user))
            self.db_conn.commit()
            await self.retry_send_message(f"{user}, your dog performed the trick '{trick_name}' successfully and earned {xp_gain} XP for {bones_cost} bones!")
            await self.check_level_up(user)
        else:
            await self.retry_send_message(f"{user}, your dog failed the trick '{trick_name}'. Better luck next time!")

    @commands.command(name='train')
    async def train(self, ctx):
        # Command to teach the user's dog a new trick
        user = ctx.author.name
        self.db_cursor.execute("SELECT id FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if not dog:
            await self.retry_send_message(f"{user}, you don't have a dog yet! Use !adopt to get one.")
            return

        dog_id = dog[0]
        all_tricks = [
            ("Roll over", 1, 5), ("Play dead", 2, 10), ("Sit", 1, 5), ("Fetch", 2, 10), 
            ("Speak", 3, 15), ("Shake", 2, 10), ("High five", 2, 10), ("Spin", 3, 15), 
            ("Jump", 3, 15), ("Stay", 1, 5), ("Beg", 4, 20), ("Wave", 4, 20),
            ("Backflip", 5, 25), ("Dance", 5, 25), ("Heel", 2, 10), ("Balance treat", 3, 15),
            ("Weave", 4, 20), ("Roll over", 1, 5), ("Fetch", 2, 10)
        ]

        self.db_cursor.execute("SELECT trick_name FROM tricks WHERE dog_id=?", (dog_id,))
        known_tricks = {trick[0] for trick in self.db_cursor.fetchall()}
        unknown_tricks = [trick for trick in all_tricks if trick[0] not in known_tricks]

        if not unknown_tricks:
            await self.retry_send_message(f"{user}, all tricks are known, your doggo is super smart!")
            return

        new_trick = random.choice(unknown_tricks)
        self.db_cursor.execute("INSERT INTO tricks (dog_id, trick_name, difficulty, xp_reward) VALUES (?, ?, ?, ?)", 
                               (dog_id, new_trick[0], new_trick[1], new_trick[2]))
        self.db_conn.commit()
        await self.retry_send_message(f"{user}, your dog learned a new trick: {new_trick[0]}!")

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        # Command to display the top 10 dogs by level and XP
        self.db_cursor.execute("SELECT user, name, level, xp FROM dogs ORDER BY level DESC, xp DESC LIMIT 10")
        top_dogs = self.db_cursor.fetchall()
        if not top_dogs:
            await self.retry_send_message("No dogs found on the leaderboard.")
            return

        leaderboard_msg = "Top 10 Dogs:\n"
        for idx, dog in enumerate(top_dogs, start=1):
            leaderboard_msg += f"{idx}. {dog[1]} (Owner: {dog[0]}, Level: {dog[2]}, XP: {dog[3]})\n"
        
        await self.retry_send_message(leaderboard_msg)

    @commands.command(name='help')
    async def help_command(self, ctx):
        # Command to provide a link to the bot's user guide
        await self.retry_send_message("For help and command details, visit: https://github.com/gorgarp/Twitch_Virtual_Dog/blob/main/guide.md")

    @commands.command(name='nodog')
    async def nodog(self, ctx):
        # Command for moderators to blacklist a user
        if ctx.author.is_mod:
            user_to_ignore = ctx.message.content.split(' ')[1]
            self.db_cursor.execute("DELETE FROM dogs WHERE user=?", (user_to_ignore,))
            self.db_cursor.execute("INSERT INTO blacklist (username) VALUES (?)", (user_to_ignore,))
            self.db_conn.commit()
            await self.retry_send_message(f"{user_to_ignore} has been removed from the dog database and blacklisted.")
        else:
            await self.retry_send_message(f"{ctx.author.name}, you do not have permission to use this command.")

    @commands.command(name='party')
    async def party(self, ctx):
        # Command to initiate a group event where all dogs earn XP
        self.db_cursor.execute("SELECT user, name FROM dogs")
        dogs = self.db_cursor.fetchall()
        if not dogs:
            await self.retry_send_message("No dogs found for the party.")
            return

        attendees = ", ".join([f"{dog[1]} (Owner: {dog[0]})" for dog in dogs])
        await self.retry_send_message(f"Party at the dog park! Attendees: {attendees}")

        for dog in dogs:
            self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog[0],))
        
        self.db_conn.commit()

    async def retry_send_message(self, message, retries=3, delay=2):
        # Function to send a message with retries for confirmation
        channel = self.get_channel(CHANNEL)
        if channel:
            for attempt in range(retries):
                try:
                    if message not in self.sent_messages:
                        await channel.send(message)
                        self.sent_messages.add(message)
                    await asyncio.sleep(delay + 1)
                    if message not in self.sent_messages:
                        break
                except Exception as e:
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                    else:
                        print(f"Failed to send message: {message} after {retries} attempts.")

bot = Bot()
bot.run()
