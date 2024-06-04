import os
import random
import sqlite3
from twitchio.ext import commands, routines
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Load environment variables
IRC_TOKEN = os.getenv('IRC_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
BOT_NICK = os.getenv('BOT_NICK')
CHANNEL = os.getenv('CHANNEL')

breeds = ["Chihuahua", "Pomeranian", "Yorkshire Terrier", "Maltese", "Dachshund", "Shih Tzu", "Toy Poodle",
          "Boston Terrier", "French Bulldog", "Miniature Pinscher", "Cavalier King Charles Spaniel", "Miniature Schnauzer",
          "Bichon Frise", "Shetland Sheepdog", "Beagle", "Cocker Spaniel", "Border Terrier", "West Highland White Terrier",
          "Pembroke Welsh Corgi", "Jack Russell Terrier", "Bulldog", "American Pit Bull Terrier", "Whippet",
          "Australian Cattle Dog", "Bull Terrier", "Samoyed", "Siberian Husky", "Boxer", "Dalmatian", "Standard Schnauzer",
          "Shar Pei", "Australian Shepherd", "Border Collie", "Shiba Inu", "Labrador Retriever", "Golden Retriever",
          "German Shepherd", "Rottweiler", "Doberman Pinscher", "Bernese Mountain Dog", "Newfoundland", "Saint Bernard",
          "Great Dane", "Irish Wolfhound", "Alaskan Malamute", "Leonberger", "Tibetan Mastiff", "Mastiff", "Great Pyrenees",
          "Scottish Deerhound"]

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
        self.db_conn = sqlite3.connect('twitch_dog_bot.db')
        self.db_cursor = self.db_conn.cursor()
        self.init_db()

    def init_db(self):
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
            last_login DATE,
            last_interaction TIMESTAMP
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
        print(f'Logged in as | {self.nick}')
        self.event_routine.start()

    async def event_message(self, message):
        if not message.author:
            return
        if message.author.name.lower() == self.nick.lower():
            return

        await self.handle_commands(message)

        # Handle inactivity message and daily bonus
        await self.handle_inactivity_and_daily_bonus(message.author.name)

    @commands.command(name='adopt')
    async def adopt(self, ctx):
        user = ctx.author.name

        # Check if the user is blacklisted
        self.db_cursor.execute("SELECT * FROM blacklist WHERE username=?", (user,))
        if self.db_cursor.fetchone():
            await ctx.send(f"{user}, you are blacklisted and cannot adopt a dog.")
            return

        # Check if the user already has a dog
        self.db_cursor.execute("SELECT * FROM dogs WHERE user=?", (user,))
        if self.db_cursor.fetchone():
            await ctx.send(f"{user}, you already have a dog!")
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
                               (user, 0, 0, datetime.now().strftime('%Y-%m-%d'), datetime.now()))
        self.db_conn.commit()

        await ctx.send(f"{user} adopted a dog named {name}! {origin_story}")

    @commands.command(name='name')
    async def name(self, ctx):
        user = ctx.author.name
        new_name = ctx.message.content.split(' ', 1)[1]
        self.db_cursor.execute("UPDATE dogs SET name=? WHERE user=?", (new_name, user))
        self.db_conn.commit()
        await ctx.send(f"{user}, your dog's name has been changed to {new_name}!")

    @commands.command(name='status')
    async def status(self, ctx):
        user = ctx.author.name
        self.db_cursor.execute("SELECT * FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if dog:
            await ctx.send(f"{user}, your dog's name is {dog[2]}, breed: {dog[3]}, level: {dog[4]}, XP: {dog[5]}, origin story: {dog[6]}")
        else:
            await ctx.send(f"{user}, you don't have a dog yet! Use !adopt to get one.")

    @commands.command(name='newstory')
    async def newstory(self, ctx):
        user = ctx.author.name
        origin_story = random.choice(origin_stories)
        self.db_cursor.execute("UPDATE dogs SET origin_story=? WHERE user=?", (origin_story, user))
        self.db_conn.commit()
        await ctx.send(f"{user}, your dog's new origin story is: {origin_story}")

    @commands.command(name='pet')
    async def pet(self, ctx):
        await self.interact(ctx, 'pet')

    @commands.command(name='walk')
    async def walk(self, ctx):
        await self.interact(ctx, 'walk')

    @commands.command(name='treat')
    async def treat(self, ctx):
        await self.interact(ctx, 'treat')

    @commands.command(name='snuggle')
    async def snuggle(self, ctx):
        await self.interact(ctx, 'snuggle')

    @commands.command(name='play')
    async def play(self, ctx):
        await self.interact(ctx, 'play')

    @commands.command(name='fetch')
    async def fetch(self, ctx):
        await self.interact(ctx, 'fetch', is_fetch=True)

    async def interact(self, ctx, interaction_type, is_fetch=False):
        user = ctx.author.name
        self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
        bones = self.db_cursor.fetchone()
        if not bones:
            await ctx.send(f"{user}, you don't have enough bones to {interaction_type} your dog.")
            return

        xp_gain = random.randint(5, 15)
        if is_fetch:
            xp_gain = random.randint(10, 30) if random.random() < 0.1 else xp_gain

        bones_cost = max(1, xp_gain // 5)
        if bones[0] < bones_cost:
            await ctx.send(f"{user}, you don't have enough bones to {interaction_type} your dog. You need {bones_cost} bones.")
            return

        self.db_cursor.execute("UPDATE dogs SET xp = xp + ? WHERE user=?", (xp_gain, user))
        self.db_cursor.execute("UPDATE users SET bones = bones - ? WHERE username=?", (bones_cost, user))
        self.db_conn.commit()

        interaction_message = "play fetch with" if is_fetch else interaction_type
        await ctx.send(f"{user}, you {interaction_message} your dog and earned {xp_gain} XP for {bones_cost} bones!")

        # Check for level up
        await self.check_level_up(user)

    async def check_level_up(self, user):
        self.db_cursor.execute("SELECT level, xp, breed FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if dog:
            level = dog[0]
            xp = dog[1]
            current_breed = dog[2]
            next_level_xp = (level ** 2) * 50  # Example exponential scale
            if xp >= next_level_xp:
                new_level = level + 1
                new_breed = breeds[new_level - 1] if new_level <= len(breeds) else breeds[-1]
                self.db_cursor.execute("UPDATE dogs SET level = ?, breed = ? WHERE user=?", (new_level, new_breed, user))
                self.db_conn.commit()
                await self.send_message(f"{user}, your dog has evolved! They went from a {current_breed} to a {new_breed}! Keep playing with them to keep them evolving!")

    @routines.routine(minutes=15)
    async def event_routine(self):
        await self.handle_events()

    async def handle_events(self):
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
        self.loop.create_task(self.send_message(event))

        # Update XP for both dogs
        self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog1[0],))
        self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog2[0],))
        self.db_conn.commit()

    async def handle_inactivity_and_daily_bonus(self, user):
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
            last_interaction = datetime.strptime(last_interaction[0], '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - last_interaction > timedelta(hours=24):
                daily_streak = self.update_daily_streak(user)
                bones_reward = min(daily_streak, 30)
                self.db_cursor.execute("UPDATE users SET last_interaction = ?, bones = bones + ? WHERE username=?", 
                                       (datetime.now(), bones_reward, user))
                self.db_conn.commit()
                await self.send_message(f"{user}, you received your daily bonus of {bones_reward} bones! Daily streak: {daily_streak} days.")
            if datetime.now() - last_interaction > timedelta(hours=12):
                activity = random.choice(activities)
                await self.send_message(f"{user}, your dog missed you! They {activity} while you were away.")
        else:
            self.db_cursor.execute("INSERT INTO users (username, bones, daily_streak, last_login, last_interaction) VALUES (?, ?, ?, ?, ?)",
                                   (user, 0, 0, datetime.now().strftime('%Y-%m-%d'), datetime.now()))
            self.db_conn.commit()

    def update_daily_streak(self, user):
        self.db_cursor.execute("SELECT daily_streak FROM users WHERE username=?", (user,))
        daily_streak = self.db_cursor.fetchone()[0]
        daily_streak += 1
        self.db_cursor.execute("UPDATE users SET daily_streak = ? WHERE username=?", (daily_streak, user))
        self.db_conn.commit()
        return daily_streak

    @commands.command(name='trick')
    async def trick(self, ctx):
        user = ctx.author.name
        self.db_cursor.execute("SELECT id FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if not dog:
            await ctx.send(f"{user}, you don't have a dog yet! Use !adopt to get one.")
            return

        dog_id = dog[0]
        self.db_cursor.execute("SELECT trick_name, difficulty, xp_reward FROM tricks WHERE dog_id=?", (dog_id,))
        tricks = self.db_cursor.fetchall()
        if not tricks:
            await ctx.send(f"{user}, your dog doesn't know any tricks yet! Use !train to teach some.")
            return

        trick = random.choice(tricks)
        trick_name, difficulty, xp_reward = trick
        bones_cost = max(1, xp_reward // 5)
        self.db_cursor.execute("SELECT bones FROM users WHERE username=?", (user,))
        bones = self.db_cursor.fetchone()[0]
        if bones < bones_cost:
            await ctx.send(f"{user}, you don't have enough bones to perform the trick '{trick_name}'. You need {bones_cost} bones.")
            return

        success = random.random() < (1 - difficulty / 10)
        if success:
            xp_gain = xp_reward
            self.db_cursor.execute("UPDATE dogs SET xp = xp + ? WHERE id=?", (xp_gain, dog_id))
            self.db_cursor.execute("UPDATE users SET bones = bones - ? WHERE username=?", (bones_cost, user))
            self.db_conn.commit()
            await ctx.send(f"{user}, your dog performed the trick '{trick_name}' successfully and earned {xp_gain} XP for {bones_cost} bones!")
            await self.check_level_up(user)
        else:
            await ctx.send(f"{user}, your dog failed the trick '{trick_name}'. Better luck next time!")

    @commands.command(name='train')
    async def train(self, ctx):
        user = ctx.author.name
        self.db_cursor.execute("SELECT id FROM dogs WHERE user=?", (user,))
        dog = self.db_cursor.fetchone()
        if not dog:
            await ctx.send(f"{user}, you don't have a dog yet! Use !adopt to get one.")
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
            await ctx.send(f"{user}, all tricks are known, your doggo is super smart!")
            return

        new_trick = random.choice(unknown_tricks)
        self.db_cursor.execute("INSERT INTO tricks (dog_id, trick_name, difficulty, xp_reward) VALUES (?, ?, ?, ?)", 
                               (dog_id, new_trick[0], new_trick[1], new_trick[2]))
        self.db_conn.commit()
        await ctx.send(f"{user}, your dog learned a new trick: {new_trick[0]}!")

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        self.db_cursor.execute("SELECT user, name, level, xp FROM dogs ORDER BY level DESC, xp DESC LIMIT 10")
        top_dogs = self.db_cursor.fetchall()
        if not top_dogs:
            await ctx.send("No dogs found on the leaderboard.")
            return

        leaderboard_msg = "Top 10 Dogs:\n"
        for idx, dog in enumerate(top_dogs, start=1):
            leaderboard_msg += f"{idx}. {dog[1]} (Owner: {dog[0]}, Level: {dog[2]}, XP: {dog[3]})\n"
        
        await ctx.send(leaderboard_msg)

    @commands.command(name='help')
    async def help_command(self, ctx):
        await ctx.send("For help and command details, visit: https://github.com/gorgarp/Twitch_Virtual_Dog/blob/main/guide.md")

    @commands.command(name='nodog')
    async def nodog(self, ctx):
        if ctx.author.is_mod:
            user_to_ignore = ctx.message.content.split(' ')[1]
            self.db_cursor.execute("DELETE FROM dogs WHERE user=?", (user_to_ignore,))
            self.db_cursor.execute("INSERT INTO blacklist (username) VALUES (?)", (user_to_ignore,))
            self.db_conn.commit()
            await ctx.send(f"{user_to_ignore} has been removed from the dog database and blacklisted.")
        else:
            await ctx.send(f"{ctx.author.name}, you do not have permission to use this command.")

    @commands.command(name='party')
    async def party(self, ctx):
        self.db_cursor.execute("SELECT user, name FROM dogs")
        dogs = self.db_cursor.fetchall()
        if not dogs:
            await ctx.send("No dogs found for the party.")
            return

        attendees = ", ".join([f"{dog[1]} (Owner: {dog[0]})" for dog in dogs])
        await ctx.send(f"Party at the dog park! Attendees: {attendees}")

        for dog in dogs:
            self.db_cursor.execute("UPDATE dogs SET xp = xp + 10 WHERE user=?", (dog[0],))
        
        self.db_conn.commit()

    async def send_message(self, message):
        channel = self.get_channel(CHANNEL)
        if channel:
            await channel.send(message)

bot = Bot()
bot.run()
