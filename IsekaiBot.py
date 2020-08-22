# Isekai Tactics
# bot connect
import discord, os
from dotenv import load_dotenv
from discord.ext import commands
# file management
import json
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle
import logging
# generation
import random as rnd
from random import choices
# system control
from os.path import isfile
from time import sleep
from math import ceil, floor, exp
import sys
from sys import exit

# set random generator
rnd.seed()

# constants
# registration
USERS_LIST = "users.json"
SAVE_FILES = "cartridges"
REPORT_FILE = "errorLog.txt"
# command line
PREFIXES = ["..",]
USERNAME = 0
ARGUMENTS = 1
# access levels
USER_TAG = 0
ACCESS_LEVEL = 1
ADMIN = 0
MODERATOR = 1
TRAVELER = 2
# commands
ALL_USERS = ["hello",]
UNREG_USERS_ONLY = ["isekai",]
REG_USERS_ONLY = ["iteminfo", "unequip", "profile", "equip", "bag", "disconnect",]
# bot connection
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix = PREFIXES) # bot instantiation line
# stats
HP = 0
ATK = 1
DEF = 2
SPATK = 3
SPDEF = 4
AGI = 5
# same for every adventurer
BASE_STATS = [40, 12, 10, 12, 10, 8]
# 12 points distributed 
DEV_STATS = {
    "fighter": [4, 2, 2, 1, 1, 2], 
    "magicaster": [4, 1, 1, 3, 2, 1],
    "survivalist": [4, 2, 1, 1, 1, 3]
}
# isekai world
MNST = 0
FIGT = 1
MAGC = 2
SRVL = 3
ALL_CLASSES = ["monster", "fighter", "magicaster", "survivalist"]
ALL_DESCRIPTIONS = ["Cunning creatures that live in the dungeons.",
    "Those who have answered the call of arms and use them to async defeat their opponents.",
    "Their sense of magic allow them to make one with it and conjure forth spells for good or evil.",
    "One who has made the wilderness their home and require no help to survive its dangers."
]
# items
CONS = 0
N_CONS = 1
EQPT = 2
ALL_ITYPES = ["consumable", "n_consumable", "equipment"]
BODY_PARTS = ["head", "larm", "rarm", "chest", "legs", "feet", "accessory"]

##### CUSTOM CLASSES #####
# class for items
class item:
    '''Class that represent items that can be collected by the adventurer.
    Items will be distinguished by their "iType".
    Possible "iType" are "consumable", "n_consumable", "equipment"'''
    def __init__(self, name, iType = ALL_ITYPES[N_CONS], description =  "nothing",
                                                            stats = None, req = None):
        self.name = name
        self.iType = iType
        self.description = description
        if self.iType == ALL_ITYPES[EQPT]: # if equipment
            self.stats = stats # only equipment will have stats
            self.req = req
    def descr(self):
        '''Return a string that describes the object.'''
        descr = "[{}]: {}\n".format(self.name, self.description)
        if self.iType == ALL_ITYPES[EQPT]:
            descr += "HP: {:3d}|ATK: {:3d}|DEF: {:3d}|".format(self.stats[HP],
                self.stats[ATK], self.stats[DEF])
            descr += "SPATK: {:3d}|SPDEF: {:3d}|AGI: {:3d}|".format(self.stats[SPATK],
                self.stats[SPDEF], self.stats[AGI])
        return descr
    # getters
    def getName(self):
        return self.name
    def getRequirements(self):
        return self.req
    def getStats(self):
        return self.stats

# class for inventory
class bag:
    '''Bag in which an adventurer can stock items they find.
    "level" is the size of the bag. It will be multiples of 30 items.
    It can be increased later in the game.'''
    def __init__(self, level = 1):
        self.level = 1
        self.size = self.level * 30
        self.contents = list()
        self.qties = list() # the qty of each item
    def reveal(self):
        '''Return a string that reveals the contents of the bag.'''
        contents = "Inventory:   ({:3d}/{:3d})\n".format(len(self.contents), self.size)
        if len(self.contents) == 0: # empty bag
            contents += "`Nothing to see here.`\n"
        else:
            for i, item in enumerate(self.contents): # items are tuple of (name, qty)
                contents += "{:3d} - {:20s} (x {:3d})\n".format(i + 1, item.getName(),
                    self.qties[i])
        return contents
    def inBag(self, itemName):
        '''Check to see if a specific item already exists in the bag.
        Return the position if it does. None elsewise.'''
        pos = None
        found = False
        if len(self.contents) > 0: # bag not empty
            i = 0
            while not found and i < len(self.contents): # searching loop
                found = itemName.lower() == self.contents[i].getName().lower()
                if not found: # was not the item
                    i += 1
        if found: # was in the bag
            pos = i
        return pos
    def putIn(self, item, qty):
        '''Put an item in the bag if the bag is not full.
        Return True if adding was successful, false elsewise.'''
        added = False
        if len(self.contents) < self.size: # bag not full
            pos = self.inBag(item.getName())
            if pos != None: # item exists in the bag so add to existing
                self.qties[pos] += 1
            else:
                self.contents.append(item) # add item
                self.qties.append(qty) # add its qty
            added = True
        return added
    # getters
    def getContentsSize(self):
        return len(self.contents)
    def getSize(self):
        return self.size
    def isFull(self):
        return self.getContentsSize() == self.size
    def getItemAt(self, pos):
        '''Return the item at the "pos" in the bag.'''
        return self.contents[pos]
    def getQtyAt(self, pos):
        '''Return the qty of item at the "pos" in the bag.'''
        return self.qties[pos]
    def takeOut(self, itemName, qty):
        '''Takes out the qty requested of an item out of the bag and returns it.
        If the number of items reaches 0, then it is deleted from the bag.
        Returns None if operation failed.'''
        takenOut = None
        pos = self.inBag(itemName)
        if pos != None:
            if qty <= self.qties[pos]: # you have enough of it
                takenOut = self.contents[pos] # recover the item for validation
                self.qties[pos] -= qty # update qty
            else:
                takenOut = "You don't have enough of that." # return for printing
            if self.qties[pos] == 0: # ran out of the item
                # delete from inventory
                del self.contents[pos]
                del self.qties[pos]
        return takenOut

# class for wallet
class wallet:
    '''Class that represents the money pouch.'''
    def __init__(self):
        self.contents = 0 # default value
    def getContents(self):
        return self.contents
    def reveal(self):
        '''Return a string that tells how much there is inside.'''
        return "{} isekash".format(self.contents)
    def cashIn(self, amount):
        '''Adds the amount to your pouch.'''
        self.contents += amount
    def cashOut(self, amount):
        '''Takes out the amount to your pouch.
        Return the ampunt cashed out if possible; None elsewise.'''
        out = None
        if self.contents >= amount: # you can afford it
            self.contents -= amount
            out = amount
        return out

# class for adventurers and monsters
class isekaiMob:
    '''Class of any mob of the isekai universe.
    The "iClass" attribute will distinguish them.
    '''
    def __init__(self, name, iClass, level = 1, stats = list):
        self.name = name
        self.iClass = iClass
        self.level = level
        self.exp = (self.level - 1) * 100
        self.stats = {
            "HP": {"cur": stats[HP], "max": stats[HP]},
            "ATK": {"cur": stats[ATK], "max": stats[ATK]},
            "DEF": {"cur": stats[DEF], "max": stats[DEF]},
            "SPATK": {"cur": stats[SPATK], "max": stats[SPATK]},
            "SPDEF": {"cur": stats[SPDEF], "max": stats[SPDEF]},
            "AGI": {"cur": stats[AGI], "max": stats[AGI]}
        }
        self.bag = bag()
        if iClass != ALL_CLASSES[MNST]: # if not a monster
            # add a wallet
            self.wallet = wallet()
            # add equipment slots
            self.equipment = {
                "head": None,
                "larm": None,
                "rarm": None,
                "chest": None,
                "legs": None,
                "feet": None,
                "accessory": None,
            }
    # getters
    def getName(self):
        return self.name
    def getClass(self):
        return self.iClass
    def getLvl(self):
        return self.level
    def getStats(self): # return list of current stats
        return [self.stats[stat]["cur"] for stat in self.stats]
    def isAlive(self):
        return self.stats["HP"]["cur"] > 0
    def getBag(self):
        return self.bag
    def getWallet(self):
        return self.wallet
    def getEquipment(self):
        return self.equipment
    def getGear(self, part):
        return self.equipment[part]
    def getGearStat(self, part):
        return self.getGear(part).getStats()
    def inventory(self):
        '''Open and reveal the contents of their bag.'''
        return self.bag.reveal()
    def money(self):
        '''Open and reveal the contents of their wallet.'''
        return self.wallet.reveal()
    # setters
    def addStats(self, addedStats):
        for i, stat in self.stats:
            self.stats[stat]["cur"] += addedStats[i]
            self.stats[stat]["max"] += addedStats[i]
    def subStats(self, subsedStats):
        for i, stat in self.stats:
            self.stats[stat]["cur"] -= subsedStats[i]
            self.stats[stat]["max"] -= subsedStats[i]
    def sufferDamage(self, amount):
        '''Inflict the damage to the character and return if it withstood it or not.'''
        self.stats["HP"]["cur"] -= int(amount)
        if self.stats["HP"]["cur"] <= 0:
            self.stats["HP"]["cur"] = 0
    def cashIn(self, amount):
        self.wallet.cashIn(amount)
    def receive(self, item, qty):
        return self.bag.putIn(item, qty)
    def pres(self):
        '''Provide a shortenned description for battle purposes.'''
        pres = str()
        pres += "[{} (lv. {:3d}) HP: {:3d}/{:3d}]".format(self.name, self.level,
                self.stats["HP"]["cur"], self.stats["HP"]["max"])
        return pres
    def equip(self, gearPos):
        '''Equip the gear in required positions. Unequip the current conflicting gear.
        requirements are a list; as a gear can have multiples requirements.'''
        done = None
        if gearPos != None: # the gear is in the bag
            gear = self.bag.getItemAt(gearPos)
            req = gear.getRequirements()
            oldGear = [self.equipment[part] for part in req] # get the previous gear equiped
            for old in oldGear:
                if old != None:
                    self.unequip(old.getName()) # unequip anything you had on
            self.bag.takeOut(gear.getName(), 1) # take new out of the bag
            self.equipment[req[0]] = gear # equip new only on the first required part
            self.addStats(gear.getStats()) # add new influence on stats
            done = True
        else:
            done = "You don't have that!"
        return done
    def unequip(self, gearName):
        '''Take off the gear "gearName" that you have on you and put it in your bag.
        If you don't have a gear equipped by that name if fails.
        If your inventory is full, it fails.'''
        done = False
        equiped = None
        for part in BODY_PARTS:
            if self.equipment[part] != None:
                if areSame(self.equipment[part].getName(), gearName): # had it equiped somewhere
                    equiped = part # get where
        if equiped == None: # gear not equiped
            done = "You don't have that equiped!"
        elif self.bag.isFull(): # if the bag can store the unequiped gear
            done = "Oh oh. You don't have any more space in your bag."
        else: # all is clear we proceed
            gear = self.equipment[equiped] # recover the gear
            self.equipment[equiped] = None # free the body part
            self.subStats(gear.getStats()) # remove its influence on stats
            self.bag.putIn(gear, 1) # return it to the bag
            done = True
        return done
    def profile(self):
        '''Returns a string that describe the mob.'''
        descr = str()
        descr += "[{}]{} Lv. {:3d}| HP: {:3d}/{:3d}\n".format(self.name, self.iClass, self.level,
            self.stats["HP"]["cur"], self.stats["HP"]["max"])
        # head
        if self.equipment["head"] == None:
            descr += "Head: None\n"
        else:
            descr += "Head: `{}`\n".format(self.equipment["head"].getName())
        # rarm chest larm
        if self.equipment["rarm"] == None:
            descr += "R.Arm: None\n"
        else:
            descr += "R.Arm: `{}`\n".format(self.equipment["rarm"].getName())
        if self.equipment["chest"] == None:
            descr += "Chest: None\n"
        else:
            descr += "Chest: `{}`\n".format(self.equipment["chest"].getName())
        if self.equipment["larm"] == None:
            descr += "L.Arm: None\n"
        else:
            descr += "L.Arm: `{}`\n".format(self.equipment["larm"].getName())    
        # legs
        if self.equipment["legs"] == None:
            descr += "Legs: None\n"
        else:
            descr += "Legs: `{}`\n".format(self.equipment["legs"].getName())
        # feet accessory
        if self.equipment["feet"] == None:
            descr += "Feet: None\n"
        else:
            descr += "Feet: `{}`\n".format(self.equipment["feet"].getName())
        if self.equipment["accessory"] == None:
            descr += "Accessory: None\n"
        else:
            descr += "Accessory: `{}`\n".format(self.equipment["accessory"].getName())
        # stats
        descr += "ATK: {:3d}|DEF: {:3d}|SPATK: {:3d}|SPDEF: {:3d}| AGI: {:3d}\n".format(
            self.stats["ATK"]["cur"], self.stats["DEF"]["cur"], self.stats["SPATK"]["cur"],
            self.stats["SPDEF"]["cur"], self.stats["AGI"]["cur"])
        descr += "Exp.: {:3d}\n".format(self.exp)
        return descr
    def develUp(self, expAmount):
        '''Receive exp and raise level if needed. Each time level is raised
        update base stats.'''
        levelUP = False
        self.exp += expAmount
        newLvl = self.exp // 100 + 1
        diffLvl = newLvl - self.level
        if diffLvl != 0:
            levelUP = True
            for lvl in range(diffLvl):
                self.addStats(DEV_STATS)
        return levelUP

##### CONNECTIVITY EVENTS #####
@bot.event
async def on_error(context, error):
    archive() # save data
    eReport(str(error.__cause__))

# on connexion established
@bot.event
async def on_ready():
    print("We have logged in as {}".format(bot.user))

# expect replies
async def userReply(message, username):
    '''Expect input from a specific user. Discard anything else.'''
    if areSame(message.author.name, username):
        return message.content
    else:
        return None

# send responses
async def narrate(channel, description):
    '''description can be either a string of a list of strings.'''
    naration = str()
    sleep(1.8)
    if type(description) == str:
        # print(description)
        await channel.send(description)
    elif type(description == list): # for lists
        for num, sentence in enumerate(description):
            sleep(2) # waits 3 seconds before continuing
            # print(sentence)
            await channel.send(sentence)
    else:
        print("Nothing to say.")

# add a new user to user list file
async def register(context, accessLvl):
    '''Update the users list json file with a new entry.
    Return "True" if something was added, False elsewise.'''
    tag = context.message.author.name
    user = isUser(tag)
    if user == None: # can only register non users
        currentList = None
        with open(USERS_LIST, 'r') as jsonData:
            try:
                currentList = json.load(jsonData) # load current contents as a dict
            except json.JSONDecodeError: # the file is empty or unreadable
                currentList = {"users": [{"username":tag, "level":2}]} # add this user then
            else: # if the exception wasn't raised
                currentList["users"].append({"username":tag, "level":2}) # append new user
        with open(USERS_LIST, "w+") as jsonData: # reset the file before writing
            json.dump(currentList, jsonData, indent = 4) # save the new list
        return True
    else:
        await narrate(context.message.channel, "Hey there! You are already an traveler!")
        return False

##### ISEKAI COMMANDS #####
# says hello to the username that calls it
@bot.command(name = "hello", help = "Says hello to the username, using a randomly choosed formula.")
async def hello(context):
    '''Says Hi to the username.'''
    hellos = ["Hi", "Oh hello there", "Hiya", "What's up", "What's cooking",
        "Ohayo"
    ]
    await narrate(context.message.channel, " ".join([rnd.choice(hellos),
        context.message.author.mention, '.']))

# random omae wa mou shindeiru reaction
@bot.command(name = "omae", help = "Responds <nani>")
async def nani(context):
    commandline = decode(context)
    channel = context.message.channel
    response = "> "
    response += context.message.content
    response += '\n'
    response += context.message.author.mention
    response += "\nNANI!? :scream::scream::scream:"
    await narrate(channel, response)

# add a new user to the game, instantiate his character, runs a tutorial for them
@bot.command(name = "isekai", help = "Starts your traveler adventure in another world.")
async def isekai(context):
    commandline = decode(context)
    username = commandline[USERNAME]
    mention = context.message.author.mention
    # add the username to the users list
    if await register(context, TRAVELER): # was registered
        await hello(context)
        await narrate(context.message.channel, "We are so happy to have you with us in this DT!")
        # ask them which class they want to start with
        valid = False
        for index in range(len(ALL_CLASSES)):
            if index != MNST: # not monster class
                await narrate(context.message.channel,
                "\n[{}]: {}".format(ALL_CLASSES[index].upper(), ALL_DESCRIPTIONS[index]))
        await narrate(context.message.channel,
            ["Which path will you follow {}? Enter it now.".format(mention),
             "(Base stats will not be affected by this choice): "])
        while not valid:
            classChoice = await userReply(await bot.wait_for("message"), username) # user control response
            if classChoice != None: # we got a good input
                classChoice = classChoice.lower()
                if classChoice in ALL_CLASSES[FIGT:]: # not monsters
                    valid = True
        # makes the avatar
        avatar = isekaiMob(username, classChoice, stats = BASE_STATS)
        # grant starter equipment
        grants = [
            item("Leather Garb", ALL_ITYPES[EQPT],
                "A simple sturdy garb made from durable leather. :coat:",
                [0, 0, 5, 0, 0, 0], ["chest",]
            ),
            item("Canvas Pants", ALL_ITYPES[EQPT],
                "Light-weight pants favored by many for their low price. :jeans:",
                [0, 0, 3, 0, 0, 1], ["legs",]
            ),
            item("Sandals", ALL_ITYPES[EQPT],
                "Easy to walk in but not the highest quality. :sandal:",
                [0, 0, 1, 0, 0, 1], ["feet",]
            )
        ]
        if avatar.getClass() == ALL_CLASSES[FIGT]: # if fighter grant a sword
            grants.append(
                item("Short Sword", ALL_ITYPES[EQPT],
                    "A simple arm-long iron blade for beginners. :dagger:",
                    [0, 6, 0, 0, 0, 0], ["rarm",]
                )
            )
        elif avatar.getClass() == ALL_CLASSES[MAGC]: # if magicaster grant a staff
            grants.append(
                item("Rod", ALL_ITYPES[EQPT],
                    "Wooden staff that help beginner casters focus. :key2:",
                    [0, 0, 0, 6, 0, 0], ["rarm"]
                )
            )
        else: # if survivalist grant a bow
            grants.append(
                item("Long Bow", ALL_ITYPES[EQPT],
                    "Arm-long wooden bow with a wild vine for string. :archery:",
                    [0, 5, 0, 0, 0, 2], ["rarm", "larm"]
                )
            )
        for grant in grants:
            avatar.receive(grant, 1) # give them out
            await narrate(context.message.channel,
                "{} was granted `{}`.".format(mention, grant.getName()))
        # grant out starting money
        avatar.cashIn(500)
        await narrate(context.message.channel,
            "{} was granted `500 isekash`.".format(mention))
        # record the avatar
        if save(avatar): # true if it was successful
            await narrate(context.message.channel,
                "Your avatar has been well created. Welcome to Isekai traveler {}!".format(mention))
        else:
            await narrate(context.message.channel, "There was an error. Please retry.")

# show the current overall status of the player
@bot.command(name = "profile", help = "Shows info of a traveler.")
async def profile(context):
    '''Load the avatar associated with "username" and then show his informations.'''
    commandline = decode(context)
    username = commandline[USERNAME]
    avatar = load(username)
    if avatar != None:
        await narrate(context.message.channel, avatar.profile()) # display the profile
    elif avatar == None:
        await narrate(context.message.channel, 
            ["It appears you are not yet an traveler {}".format(username),
             "use <..isekai> to sign up."]
        )
    else:
        await narrate(context.message.channel, 
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry :sweat_smile:"]
        )

# display inventory
@bot.command(name = "bag", help = "Display your inventory.")
async def inventory(context):
    commandline = decode(context)
    username = commandline[USERNAME]
    avatar = load(username)
    if avatar != None:
        await narrate(context.message.channel,
            "".join([context.message.author.mention, "'s", ' ', avatar.inventory()]))
    else:
        await narrate(context.message.channel, 
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry :sweat_smile:"]
        )

# equip owned gear
@bot.command(name = "equip", help = "Equip gear stored in your bag. Composite gear names must be written in quotes. e.g.: ..equip bow   ..equip \"blue jeans\"")
async def equip(context, gearName: str):
    '''Makes "username"'s avatar equip "gearName" if its in their inventory.'''
    commandline = decode(context)
    username = commandline[USERNAME]
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        returned = avatar.equip(avatar.getBag().inBag(gearName))
        if type(returned) == str: # a string means an error message was returned
            await narrate(channel, returned)
        else: # returned will be True meaning success
            await narrate(channel, "{} equiped `{}`.".format(mention, gearName))
    else:
        await narrate(channel, 
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry :sweat_smile:"]
        )
    save(avatar)

# unequip items
@bot.command(name = "unequip", help = "Equip gear stored in your bag. Composite gear names must be written in quotes. e.g.: ..unequip bow   ..unequip \"blue jeans\"")
async def unequip(context, gearName: str):
    '''Makes "username"'s avatar equip "itemName" if its in their inventory.'''
    commandline = decode(context)
    username = commandline[USERNAME]
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        returned = avatar.unequip(gearName)
        if type(returned) == str: # a string means an error message was returned
            await narrate(channel, returned)
        else: # returned will be True meaning success
            await narrate(channel, "{} took off `{}`.".format(mention, gearName))
    else:
        narrate(channel,
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry X[ !"])
    save(avatar)

# get informations about an owned item
@bot.command(name = "itemInfo", help = "Shows trivia about an item in your inventory.")
async def itemInfo(context, itemName):
    '''Shows the infos of "itemName" in inventory.'''
    commandline = decode(context)
    username = commandline[USERNAME]
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        itemPos = avatar.getBag().inBag(itemName)
        if itemPos != None: # you have the item
            await narrate(channel, 
                " ".join([mention, avatar.getBag().getItemAt(itemPos).descr()]))
        else:
            await narrate(channel,
                "{}, you don't own any item by that name.".format(mention))
    else:
        await narrate(channel,
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry :sweat_smile:"])

# tutorial for exploration
@bot.command(name = "tutorial", help = "Takes the player through a journey on a beginner dungeon floor to tell them how exploration works.")
async def tutorial(context):
    '''Takes player through a mock up exploration.'''
    commandline = decode(context)
    username = commandline[USERNAME]
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        # initial message
        complete = False # flow control
        await narrate(channel,
            ["Hi {}. I will be teaching you how dungeon exploration works.".format(mention),
             "A dungeon is made of `floors` and each floors are separated into random `blocks`.",
             "You can only explore a floor at the time but you need to complete the exploration of that floor before exploring the next one.",
             "Completing the exploration of a floor requires finding the `stairs` and defeating the boss guarding them.",
             "You only need to defeat the boss once but everytime you restart the floor the boss will respawn neverthless.",
             "Boss fights are hard so you get to choose if you'll confront it or not.",
             "But there is a lot more to floor exploration.",
             "Follow me :grin::grin::grin:",
             "P.S.: {} make sure to equip your best gear. Enter `ready` when you are. You can cancel the tutorial using `abort`".format(mention) 
            ]
        )
        # choice control
        userEntry = None
        ready = False 
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # floor characteristics
            nbBlocks = 6
            slime = isekaiMob("Green Slime", ALL_CLASSES[MNST], stats = [10, 2, 2, 2, 2, 5])
            golemini = isekaiMob("Golemini", ALL_CLASSES[MNST], 3, [22, 9, 7, 3, 2, 5])
            party = [avatar]
            # begin exploration
            await narrate(channel,
                "{} ventured inside the `Trial Grounds Cave`!".format(mention)
            )
            # empty block
            await narrate(channel,
                ["As {} was walking in the dark cave, he came across an open space.".format(mention),
                "The rocky wall seemed suddenly to be moving and the dark getting deeper but it was just the result of {} anxiety.".format(mention),
                "relieved, {} kept going since there wasn't much to do around.".format(mention)]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "A bunch of times Blocks will be empty, just like the previous one was.",
                 "You can just read through it and I hope you enjoy the narration.",
                 "But there won't be much in there so just keep your eyes open for the next block.",
                 "Enter `ready` to keep going; `abort`, to stop."]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # fight
            await narrate(channel,
                ["As {} was exploring a dark hallway, his danger senses suddenly tingled.".format(mention),
                 "{} suddenly hear hostile noises from behind the crage in front a few steps ahead.".format(mention),
                 "{} barely had the time to grab his weapon that a monster appeared!".format(mention)]
            )
            # print battle state
            monster = [slime,]
            battleState = str()
            battleState += "\n\nA battle has started:"
            battleState += "\n{}\n\nVS\n\n{}".format(present(monster), present(party))
            win = winChances(party, monster, 1)
            esc = escapeChances(party, monster, 1)
            battleState += "\nOdds: Winning prob. = {:.2f}%| Escape prob. = {:.2f}%".format(win, esc)
            await narrate(channel, battleState)
            await narrate(channel,
                ["`TUTORIAL`",
                 "{} entered a fight with a Slime.".format(mention),
                 "You have two options in a fight: fighting, or running away.",
                 "The bot will always show you probabilities of both actions:",
                 "Odds: Winning prob. = `{:.2f}%`| Escape prob. = `{:.2f}%`".format(win, esc),
                 "Make sure to check them out before choosing anything {}.".format(mention),
                 "For now let's beat up this little guy! :smirk::smirk::smirk:",
                 "What should the party do?\n[`Fight` :crossed_swords:]>>>"]
            )
            userEntry = None
            while userEntry == None:
                userEntry = await userReply(await bot.wait_for("message"), username)
                if userEntry != None:
                    if areSame(userEntry, "fight"):
                        ready = True
                    else:
                        userEntry = None
            # we got a fighting
            await narrate(channel,
                "{} fought like a pro and the slime has fallen.".format(mention))
            # end of the battle we give last tips
            await narrate(channel,
                ["Good job {}!".format(mention),
                 "This is a tutorial so you won't win or lose anything but usually you will get experience and possibly loot from defeating monsters.",
                 "Selling dropped loot is a easiest way to make money and experience will make you stronger.",
                 "Anyway let's keep going do we? [`ready`] [`abort`]"]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # gathering
            await narrate(channel,
                ["{} was strolling quickly through a wide chamber when they were attracted by some kind of glimmer.".format(mention),
                 "With a closer look they noticed the wall was brittle and seemed like some kind of mineral deposit.",
                 "digging there could surely prove rewarding they thought."]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "This is what is called a gathering block. Once in a while on floors you will find some of them.",
                 "Depending on the floor, the items you can get will be shown and you can try obtaining them.",
                 "You can only gather once per exploration and there is a chance that you attract monsters trying to gather so be careful.",
                 "Saddly there won't be anything here cause it's a testing ground. Sorry :sweat_smile:",
                 "If you don't mind let's keep going {} okay? [`ready`] [`abort`].".format(mention)
                ]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # treasure
            await narrate(channel,
                ["As {} continued his exploration of the cave, they stopped to catch their breath.".format(mention),
                 "They nonchalantly tried to use the wall as a support when suddenly their hand activated what seemed to be hidden switch.",
                 "It seem {} stumbled accross a secret room and they could see a treasure chest at the bottom of it.".format(mention),
                 "Dropping any guard they ran inside to open the chest... only to find it empty."]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "Hidden chambers are rare but if you can find one, you can get treasure in it.",
                 "Although each hidden chamber is unique and its treasure as well.",
                 "If you found it once before, it will always be empty.",
                 "Don't be sad {} and let's keep going shall we? [`ready`] [`abort`]".format(mention)]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # special point
            await narrate(channel,
                ["Still exploring the cave, {} comes across a small pond.".format(mention),
                 "The water seems to have been made by rain water sipping through the mountain into this place.",
                 "The view of the water made them thirsty and the water was so clear.",
                 "{} crouched and delved their head into the water to drink.".format(mention),
                 "This true mineral water quenched their thirst and also healed their wounds."]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "Floors might have special blocks where you can interact with the environment.",
                 "In some cases they will grant you benefit like this life pond. In others, it could hurt you instead.",
                 "Always trust your best judgement when you read the narration.",
                 "Special blocks effect will not change so remember which are dangerous {}.".format(mention),
                 "Anyway let's go? [`ready`] [`abort`]"]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # teleporter
            await narrate(channel, 
                ["As {} was strolling through the dark cave, from the distance they saw a bright light phenomenon.".format(mention),
                 "intrigued, they got closer and couldn't believe their eyes: There was a pillar of light in the corner of the room.",
                 "It didn't seem dangerous but {} had no clue what that was.".format(mention)]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "Once in a while on floors you will see a pillar of light which actually is a teleporter.",
                 "Using it you can escape the dungeon whenever you want.",
                 "It is practical when your `HP` is low and you don't want to reach the end of the floor.",
                 "Be sure to use your best judgement when you encounter them.",
                 "Let's see the last block okay? [`ready`] [`abort`]"]
            )
        # choice control
        userEntry = None
        ready = False
        while (not complete) and userEntry == None:
            userEntry = await userReply(await bot.wait_for("message"), username)
            if userEntry != None:
                if areSame(userEntry, "ready"):
                    ready = True
                elif areSame(userEntry, "abort"):
                    complete = True
                else:
                    userEntry = None
        # continuing
        if ready or (not complete): # they want to continue
            # stairs
            await narrate(channel,
                ["{} stumbled across a double steel doors.".format(mention),
                 "These must be the entrance to the stairway they thought.",
                 "They entered and suddenly, they were face to face with a (tiny) golem monster.",
                 "{} tried to go back out but the doors were locked behind them and wouldn't move.".format(mention),
                 "It seems your only option out of this place is to beat the boss or die trying..."]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "As said previously, each floor will have a staircase that leads to the next floor.",
                 "But they will be guarded by boss monsters. Boss monsters are strong and somewhat hard to beat.",
                 "You will be prompted with a choice to confront them or not. Choosing to retreat will take you out of the dungeon as if the exploration was complete.",
                 "Fighting and beating the boss mob will do the same, but also unlock the next floor.",
                 "Choose wisely as there is no running away from bosses and they can have multiples forms.",
                 "Since dungeons are random, you could stumble accross the stairs anytime, but if you don't, then the last block of the block will be the stairs.",
                 "For now let's beat this (unimpressive) boss {}! :smirk::smirk::smirk:".format(mention)]
            )
            # boss fight
            # print battle state
            monster = [golemini,]
            battleState = str()
            battleState += "\n\nA battle has started:"
            battleState += "{}\n\nVS\n\n{}".format(present(monster), present(party))
            win = winChances(party, monster, 1)
            esc = escapeChances(party, monster, 1)
            battleState += "\nOdds: Winning prob. = {:.2f}%| Escape prob. = {:.2f}%".format(win, esc)
            await narrate(channel, battleState)
            await narrate(channel,
                 "What should the party do?\n[`Fight` :crossed_swords:]>>>")
            userEntry = None
            while userEntry == None:
                userEntry = await userReply(await bot.wait_for("message"), username)
                if userEntry != None:
                    if areSame(userEntry, "fight"):
                        ready = True
                    else:
                        userEntry = None
            # we got a fighting
            await narrate(channel,
                ["The golem roars once so frightening soon turned into freaked out moans as {} utterly beat the crap out of it.".format(mention),
                 "You win the fight and the golem falls. Using the stairs, you are magically transported to the entrance of the cave.",
                 "{} completed the tutorial `Testing Grounds Cave`! :tada::tada::tada:".format(mention)]
            )
            await narrate(channel,
                ["`TUTORIAL`",
                 "This concludes the tutorial. I hope you liked it.",
                 "One more thing: In case of death in the dungeon, your avatar will not be saved.",
                 "You will lose nothing but all the items and loots and level ups which happenned during the exploration.",
                 "Always be wary of the `danger level` of the floor you are going on."]
            )
            # end of the battle we give last tips
        await narrate(channel,
            "Alright, good luck on your explorations traveler {}! :grin::grin::grin:".format(mention)
        )

# turn bot off
@bot.command(name = "disconnect", help = "Disconnect the bot. Only works if received from admin level user.")
async def disconnect(context):
    '''Turns the bot offline. Requires access level "ADMIN".'''
    commandline = decode(context)
    username = commandline[USERNAME]
    user = isUser(username)
    if user != None: # the user exists
        if user[ACCESS_LEVEL] == ADMIN: # only admin can do this
            archive() # save avatars
            await narrate(context.message.channel,
                "Roger! Going offline... :grin::grin::grin:")
            exit()
    else:
        await narrate(context.message.channel, "You do not have authorization for that command.")

##### EXPLORATION MECHANICS #####
# empty block
def emptyBlock(narration):
    '''Describes a block using intros, descriptions and continuation sentences provided.
    narration[0] are intros list
    narration[1] are descriptions list
    narration[2] are continues list'''
    rnd.seed()
    # add an intro
    print(rnd.choice(narration[0]))
    # add a random number of descriptions
    sentIndexes = rnd.sample(range(len(narration[1])), rnd.randint(1, 3))
    for index in sentIndexes:
        print(narration[1][index])
    # add continuation
    print(rnd.choice(narration[2]))
    # returns signal if exploration continues or not
    return True

# fight block
def fightBlock(narration, party, floorMonsters, monstersProb, maxMonsters, dangerLvl):
    '''Narrates the start of a fight and then does the fight. Then narrates the end of the fight.'''
    rnd.seed()
    # add an intro
    print(rnd.choice(narration[0]))
    # add an description
    print(rnd.choice(narration[1]))
    # fight
    if encounter(party, floorMonsters, monstersProb, maxMonsters, dangerLvl):
        print(rnd.choice(narration[2]))
        return True
    else:
        return False

# gathering block
def gatheringBlock(narration, party, itemList, itemChances,
            floorMonsters, monstersProb, maxMonsters, dangerLvl):
    '''Describes a gathering block and give the option to the team to gather or leave.
    Includes a possibility of starting a fight.'''
    # intro
    print(rnd.choice(narration[0]))
    # point description
    for sentence in narration[1]:
        print(sentence)
    # give choice gather or leave
     # action choice
    valid = False
    action = None
    survived = True
    while not valid:
        action = input("Try gathering here? [Gather] [Leave] >>> ")
        valid = action.lower() in ['g', "gather", 'l', "leave"] # valid action
    if action in ['g', "gather"]:
        success = ceil((1 - (.1 * dangerLvl)) * 100) # chances of getting an item
        if rnd.randint(0, 100) > success: # monsters attacked
            print("The party just decided to gather but suddenly monsters attacked!")
            if encounter(party, floorMonsters, monstersProb, maxMonsters, dangerLvl): # we won
                print("With the monsters out of the way they got back to gathering.")
            else:
                survived = False
        if survived: #randint(0, 100) <= success: # we gather
            found = rnd.choices(itemList, weights = itemChances, k = 1)
            qty = rnd.randint(1, 3)
            print("While herb picking, the party found `{} {}`!".format(qty, found[0]["name"]))
            for unit in party:
                unit.receive(item(found[0]["name"], found[0]["type"], found[0]["description"],
                    found[0]["stats"], found[0]["reqs"]), qty)
    # we either left or went through a gathering
    if survived:
        print(rnd.choice(narration[2]))
    return survived

##### BATTLE MECHANICS #####
# return a party's cumulated specific stat
def cumulated(party, statNum):
    '''Send the cumulated sum of a specific stat.'''
    cumSum = 0
    if statNum in range(len(BASE_STATS)):
        for unit in party:
            if unit.isAlive():
                cumSum += unit.getStats()[statNum]
    return cumSum

# sigmoid function that output values between 0 and a 100 whatever its input is
def absoluteSigmoid(value):
    return ((value / (1 + abs(value))) + 1) * .5# so it is 50% at value = 0

# battle presentation
def present(party):
    '''Present all the units in a party.'''
    pres = str()
    for unit in party:
        pres += unit.pres()
        pres += "   "
    return pres

# makes a party of monsters from a monster list
def monsterParty(monstersList, monstersProb = None, maxMonsters = 1, dangerLvl = 1):
    '''Creates a list of monsters for an encounter.'''
    partySize = rnd.choice(range(maxMonsters)) + 1# random party size
    # dangerLvl * 10% of chances to add a monster
    if (partySize < maxMonsters) and (rnd.randint(0, 100) <= (dangerLvl * 10)):
        partySize += 1
    # make the monsters
    party = rnd.choices(population = monstersList, weights = monstersProb, k = partySize)
    i = 0
    while i < len(party):
        monster = isekaiMob(party[i]["name"], party[i]["class"], party[i]["level"],
            copy(party[i]["stats"])) # create the monster
        for loot in party[i]["loot"]:
            monster.receive(item(loot["name"], loot["type"], loot["description"],
                loot["stats"], loot["reqs"]), 1) # give it it's loot
        party[i] = monster # replace the dict by the actual monster
        i += 1
    return party

# compute and return an amount of experience for fights
def expAwarding(party, party2, dangerLvl):
    '''Computes the total exp to be gained by "party".'''
    lvlDiff = 0
    for unit in party2:
        lvlDiff += unit.getLvl()
    for unit in party:
        lvlDiff -= (unit.getLvl() / len(party))
    if lvlDiff <= 0: # correction
        lvlDiff = 1
    gainedExp = (len(party2) + lvlDiff) * dangerLvl
    return gainedExp

# computes the amount of damage a party can inflict to the other
def atkRound(party, party2):
    '''Compute the damage that party2 will suffer from getting attacked by party.'''
    rawDMG = (cumulated(party, ATK) + cumulated(party, SPATK)) / len(party)
    rawRES = (cumulated(party2, DEF) + cumulated(party2, SPDEF)) / len(party2)
    dmg = rawDMG - rawRES
    if dmg < 1:
        dmg = 1
    return int(dmg)

# average agility stat
def averageAGI(party):
    return cumulated(party, AGI) / len(party)

# compute running away probability
def escapeChances(party, party2, dangerLvl):
    '''Compute the probability that party1 has of running away from the battle against
    party2 using their units AGI and the dangerLvl.'''
    avgAgi = averageAGI(party)
    avgAgi2 = averageAGI(party2) + dangerLvl # monsters are helped by the terrain
    esc = absoluteSigmoid(avgAgi - avgAgi2) * 100 # * 100 to center it 0 - 100
    return ceil(esc)

# distribute total damage to party
def distributeDMG(party, dmg):
    for unit in party:
        if unit.isAlive():
            unit.sufferDamage(dmg)

# checks if the party is still alive
def partyStatus(party):
    '''Returns true if the party is alive, false elsewhere.'''
    alive = 0
    for unit in party:
        if unit.isAlive():
            alive += 1
    return alive > 0

# makes a fight loop and determine the winner
def autoFight(party, party2):
    '''Simulate a fight between "party" and "party2" their opponents.
    Return true if "party" won and false else.'''
    alive = True
    won = False
    turn = 0
    while alive and not won:
        # battle state
        print("`TURN {}`\n{}\n\nVS\n\n{}".format(turn + 1, present(party2), present(party)))
        # turn
        attackers = None
        defenders = None
        # speed test
        if averageAGI(party) >= averageAGI(party2): # party moves first
            attackers = party
            defenders = party2
        else: # monsters move first
            attackers = party2
            defenders = party
        # moves rounds
        rounds = 0
        while rounds in range(2):
            if attackers == party:
                print("The party attacked with all their might.")
            else: # defenders == party2
                print("The monsters attacked with all their might.")
            avgDamage = ceil(atkRound(attackers, defenders) / len(defenders)) # compute damage
            if defenders == party:
                print("The party suffered {:3d} damage per units.".format(avgDamage))
            else: # defenders == party2
                print("The monsters took {:3d} damage per units.".format(avgDamage))
            distributeDMG(defenders, avgDamage) # distribute damage
            i = 0
            while i < len(defenders):
                if not defenders[i].isAlive():  
                    print("{} has fallen.".format(defenders[i].getName()))
                    defenders.remove(defenders[i])
                else:
                    i += 1
            # stop the fight in case defenders were defeated
            if partyStatus(defenders):
                rounds += 1
            else: # defenders fell
                rounds += 2 # break the loop
            # swap the positions
            attackers, defenders = defenders, attackers
        # check status of each party
        turn += 1
        alive = partyStatus(party)
        won = not partyStatus(party2)
    # return statement
    if alive and won: # good outcome
        return True
    else:
        return False

# create fight conditions, do the fight, give exp and loot    
def encounter(party, floorMonsters, monstersProb, maxMonsters, dangerLvl):
    # init
    rnd.seed()
    survived = False
    # make monsters party
    party2 = monsterParty(floorMonsters, monstersProb, maxMonsters, dangerLvl)
    # show battle state
    print("A battle has started:")
    print("{}\n\nVS\n\n{}".format(present(party2), present(party)))
    esc = escapeChances(party, party2, dangerLvl)
    dmg = int(atkRound(party, party2) / len(party2))
    rDmg = int(atkRound(party2, party) / len(party))
    print("Dmg. dealt: `{:3d}HP`| Dmg. rec.: `{:3d}HP`| Esc. prob. = `{:2d}%`".format(dmg, rDmg, esc)) 
    # action choice
    valid = False
    while not valid:
        action = input("What should the party do?\n[Fight][Run] >>> ")
        valid = action.upper() in ["F", "FIGHT", "R", "RUN"] # valid action
        if not valid:
            print("Enter Fight, or F to fight; Run or R to run.")
    # execution
    completed = False
    if action.upper() in ["R", "RUN"]: # run first cause in case it fails the battle still happens
        if rnd.randint(0, 100) <= esc: # could get away 
            print("The party ran so quickly that the monsters couldn't catch up.")
            completed = True
            survived = True
        else:
            print("The party bolted but the monsters stopped them in their track.")
    if not completed: # team didn't try to or didn't manage to escape
        # recompute probabilities
        if autoFight(party, copy(party2)): # win
            survived = True
            print("The battle has ended.")
            # experience
            exp = ceil(expAwarding(party, party2, dangerLvl))
            if len(party) > 1:
                print("Each party member gained `{:3d} exp`. points.".format(exp))
            else:
                print("{} gained `{:3d} exp`. points.".format(party[0].getName(), exp))
            for unit in party:
                if(unit.develUp(exp)): # a true will mean they leveled up
                    print("`{}` has reached `lvl {:3d}`!".format(unit.getName(), unit.getLvl()))
            # loot
            allLoot = list()
            for unit in party2:
                for drop in unit.getBag().availableInBag():
                    allLoot.append(drop) # gather all possible loot
            dropped = rnd.sample(allLoot, rnd.randint(0, len(allLoot)))
            if len(dropped) > 0: # something was dropped
                for drop in dropped:
                    print("`{}` was dropped by the monsters.".format(drop.getName()))
                    for unit in party:
                        unit.receive(drop, 1)
        else: # lost
            survived = False
    return survived

##### HELPER FUNCTIONS #####
# log errors
async def eReport(report):
    ''' uses the logging module to quickly save the report in a file'''
    
    logging.basicConfig(filename = REPORT_FILE,
                        format = "%(asctime)s %(process)d %(message)s",
                        datefmt = "%d-%b-%y %H:%M:%S",
                        filemode = "w")
                        
    # making log object
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # log the report
    logger.info(report)

# get information out of context for functions operations
def decode(discordCtx):
    '''Analyses "discordCtx" returns command and parameters.'''
    parts = [discordCtx.message.author.name,] # list the username
    argument = str()
    if len(discordCtx.args) != 0: # there are arguments passed
        for arg in discordCtx.args:
            argument += str(arg)
        parts.append(argument)
    return parts

# check of user exists
def isUser(tag):
    '''Look in the userfile and check to see if "tag" is registered.
    Returns the user and his authorization level.'''
    found = False
    with open(USERS_LIST, 'r') as jsonData:
        try:
            database = json.load(jsonData)["users"]
        except json.JSONDecodeError: # the file is empty or unreadable
            return None
    # else we keep going
    i = 0
    while (not found) and (i < len(database)): # database[i] is a dict
        found = database[i]["username"] == tag # the tag is this element of 
        if not found:
            i += 1        
    # return statements
    if found:
        return (database[i]["username"], database[i]["level"])
    else:
        return None

# compare two strings
def areSame(string, string2):
    '''Compare two strings by lower casing both and checking character by character.
    Return True if they're similar, False elesewise.'''
    return string.lower() == string2.lower()

# record the infos of players as persistent files
def archive():
    print("In archive >>> {}".format(runtimeSaves))
    if len(runtimeSaves) != 0: # we have things to archive
        for avatar in runtimeSaves: # loop on all the avatars in memory
            savefile = ".".join(["/".join([SAVE_FILES, avatar.getName()]), "isav"])
            with open(savefile, "wb") as cartridge: # overwrite previous if any
                pickle.dump(avatar, cartridge, pickle.HIGHEST_PROTOCOL)
            del avatar

# record the infos of a player in runtime memory
def save(avatar):
    saved = False
    print("In save >>> {}".format(runtimeSaves))
    if len(runtimeSaves) != 0: # the runtime memory is not empty
        found = False
        i = 0
        while i < len(runtimeSaves) and not found: # search for the avatar in runtime mem
            found = areSame(avatar.getName(), runtimeSaves[i].getName())
            if not found:
                i += 1
        if found:
            runtimeSaves[i] = avatar # overwrite the data if its in memory
            saved = True
    if not saved: # meaning we couldn't find it earlier
        runtimeSaves.append(avatar) # add it to memory then
        saved = True
    print("In save end>>> {}".format(runtimeSaves))
    return saved

# load the infos of a player from memory if it is in memory or from harddrive
def load(username):
    loaded = None
    # check runtime memory
    print("In load >>> {}".format(runtimeSaves))
    print(len(runtimeSaves))
    if len(runtimeSaves) > 0: # there are stuff in memory
        found = False
        i = 0
        while i < len(runtimeSaves) and not found:
            found = areSame(username, runtimeSaves[i].getName())
            if not found:
                i += 1
        if found:
            loaded = runtimeSaves[i]
    # if the avatar wasn't found then we load it from file
    if loaded == None:
        savefile = ".".join(["/".join([SAVE_FILES, username]), "isav"])
        if isfile(savefile): # savefile exists
            with open(savefile, "rb") as cartridge: # read binary
                loaded = pickle.load(cartridge)
        if loaded != None: # the file was found
            runtimeSaves.append(loaded) # append new import to memory
    print("In load end>>> {}".format(runtimeSaves))
    return loaded # return either info or none

##### MAIN #####
if __name__ == "__main__":
    # system requirements
    runtimeSaves = list() # for run time changes
    # connection requirements
    bot.run(TOKEN)
    