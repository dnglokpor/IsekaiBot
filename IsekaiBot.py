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
from copy import copy, deepcopy
import random as rnd
from random import choices
# system control
import os
from os.path import isfile, join
import time as t
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
DUNGEON_PATH = "Dungeon"
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
# stats
HP = 0
ATK = 1
DEF = 2
SPATK = 3
SPDEF = 4
AGI = 5
CRIT = 6
LUCK = 7
# same for every adventurer
BASE_STATS = [40, 12, 10, 12, 10, 8, 1, 1]
# isekai world
MNST = 0
FIGT = 1
MAGC = 2
SRVL = 3
ALL_CLASSES = ["monster", "fighter", "magicaster", "survivalist"]
ALL_DESCRIPTIONS = ["Cunning creatures that live in the dungeons.",
    "Those who have answered the call of arms and use them to defeat their opponents.",
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
        # will be none for anything but gear
        self.stats = copy(stats)
        self.req = copy(req)
    def descr(self):
        '''Return a string that describes the object.'''
        descr = "[{}]`{}`\n{}\n".format(self.iType, self.name, self.description)
        if self.iType == ALL_ITYPES[EQPT]:
            descr += "Requirements: `{}`\n".format(self.req)
            descr += "HP: `{:3d}`|ATK: `{:3d}`|DEF: `{:3d}`|".format(self.stats[HP],
                self.stats[ATK], self.stats[DEF])
            descr += "SPATK: `{:3d}`|SPDEF: `{:3d}`|AGI: `{:3d}`|".format(self.stats[SPATK],
                self.stats[SPDEF], self.stats[AGI])
            descr += "CRIT: `{:3d}`|LUCK: `{:3d}`|".format(self.stats[CRIT], self.stats[LUCK])
        return descr
    # getters
    def getName(self):
        return self.name
    def getRequirements(self):
        if self.iType == ALL_ITYPES[EQPT]:
            return self.req
        else:
            return None
    def getStats(self):
        if self.iType == ALL_ITYPES[EQPT]:
            return self.stats
        else:
            return None

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
    def availableInBag(self):
        '''Returns a sample the contents of the bag as a list of "item" objects.
        Will be used to loot monsters.'''
        return self.contents

# class for wallet
class wallet:
    '''Class that represents the money pouch.'''
    def __init__(self):
        self.contents = 0 # default value
    def getContents(self):
        return self.contents
    def reveal(self):
        '''Return a string that tells how much there is inside.'''
        return "`{} i$`".format(self.contents)
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
            "AGI": {"cur": stats[AGI], "max": stats[AGI]},
            "CRIT": {"cur": stats[CRIT], "max": stats[CRIT]},
            "LUCK": {"cur": stats[LUCK], "max": stats[LUCK]}
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
    def getDictStats(self): # return the dict of all the stats
        return self.stats
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
    def heal(self, hpAmount):
        '''Heals HP by "hpAmount".'''
        self.stats["HP"]["cur"] += hpAmount
        if self.stats["HP"]["cur"] > self.stats["HP"]["max"]:
            self.stats["HP"]["cur"] = self.stats["HP"]["max"]
    def addStats(self, addedStats):
        '''Increase "self.stats" by a list of stats.'''
        for i, stat in enumerate(self.stats):
            if stat != "HP": # current HP won't change on the fly
                self.stats[stat]["cur"] += addedStats[i]
            self.stats[stat]["max"] += addedStats[i]
    def subStats(self, subsedStats):
        for i, stat in enumerate(self.stats):
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
        descr += "`<{}>` `{}`   lv. `{:3d}`|   HP: `{:3d}/{:3d}`\n".format(self.iClass, self.name, self.level,
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
        descr += "ATK: `{:3d}`|DEF: `{:3d}`|SPATK: `{:3d}`|SPDEF: `{:3d}`| AGI: `{:3d}`| CRIT: `{:3d}`| LUCK: `{:3d}`\n".format(self.stats["ATK"]["cur"],
            self.stats["DEF"]["cur"], self.stats["SPATK"]["cur"], self.stats["SPDEF"]["cur"],
            self.stats["AGI"]["cur"], self.stats["CRIT"]["cur"], self.stats["LUCK"]["cur"])
        descr += "Exp.: `{:3d}`\n".format(self.exp)
        return descr
    def develUp(self, expAmount):
        '''Receive exp and raise level if needed. Each time level is raised
        update base stats.'''
        levelUP = False
        self.exp += expAmount
        print(self.exp)
        newLvl = self.exp // 100 + 1
        diffLvl = newLvl - self.level
        if diffLvl != 0:
            levelUP = True
            for lvl in range(diffLvl):
                # evolution depends on class for specific stats
                evo = list()
                # between 15% and 20% hp gain for anyone
                evo.append(rnd.randint(ceil(self.stats["HP"]["max"] * .15), 
                    ceil(self.stats["HP"]["max"] * .20)))
                if self.iClass == ALL_CLASSES[FIGT]:
                    # between 15% and 20% atk and def gain
                    evo.append(rnd.randint(ceil(self.stats["ATK"]["max"] * .15), 
                        ceil(self.stats["ATK"]["max"] * .20)))
                    evo.append(rnd.randint(ceil(self.stats["DEF"]["max"] * .15), 
                        ceil(self.stats["DEF"]["max"] * .20)))
                    # between 3% and 6% spatk and spdef gain
                    evo.append(rnd.randint(ceil(self.stats["SPATK"]["max"] * .03), 
                        ceil(self.stats["SPATK"]["max"] * .06)))
                    evo.append(rnd.randint(ceil(self.stats["SPDEF"]["max"] * .03), 
                        ceil(self.stats["SPDEF"]["max"] * .06)))
                    # between 10% and 12% agi gain
                    evo.append(rnd.randint(ceil(self.stats["AGI"]["max"] * .1), 
                        ceil(self.stats["AGI"]["max"] * .12))) 
                if self.iClass == ALL_CLASSES[MAGC]:
                    # between 3% and 6% atk and def gain
                    evo.append(rnd.randint(ceil(self.stats["ATK"]["max"] * .03), 
                        ceil(self.stats["ATK"]["max"] * .06)))
                    evo.append(rnd.randint(ceil(self.stats["DEF"]["max"] * .03), 
                        ceil(self.stats["DEF"]["max"] * .06)))
                    # between 15% and 20% spatk and spdef gain
                    evo.append(rnd.randint(ceil(self.stats["SPATK"]["max"] * .15), 
                        ceil(self.stats["SPATK"]["max"] * .2)))
                    evo.append(rnd.randint(ceil(self.stats["SPDEF"]["max"] * .15), 
                        ceil(self.stats["SPDEF"]["max"] * .3)))
                    # between 10% and 12% agi gain
                    evo.append(rnd.randint(int(self.stats["AGI"]["max"] * .1), 
                        int(self.stats["AGI"]["max"] * .12)))
                if self.iClass == ALL_CLASSES[SRVL]:
                    # between 15% and 20% atk gain
                    evo.append(rnd.randint(ceil(self.stats["ATK"]["max"] * .15), 
                        ceil(self.stats["ATK"]["max"] * .2)))
                    # between 10% and 12% def gain
                    evo.append(rnd.randint(ceil(self.stats["DEF"]["max"] * .1), 
                        ceil(self.stats["DEF"]["max"] * .12)))
                    # between 3% and 6% spatk gain
                    evo.append(rnd.randint(ceil(self.stats["SPATK"]["max"] * .03), 
                        ceil(self.stats["SPATK"]["max"] * .06)))
                    # between 10% and 12% spdef gain
                    evo.append(rnd.randint(ceil(self.stats["SPDEF"]["max"] * .1), 
                        ceil(self.stats["SPDEF"]["max"] * .12)))
                    # between 12% and 15% agi gain
                    evo.append(rnd.randint(ceil(self.stats["AGI"]["max"] * .12), 
                        ceil(self.stats["AGI"]["max"] * .15)))
                # between 10% and 10% + cur. luck. crit and luck gain for anyone
                evo.append(rnd.randint(ceil(self.stats["CRIT"]["max"] * .1),
                    ceil(self.stats["CRIT"]["max"] * .1) + self.stats["LUCK"]["max"]))
                evo.append(rnd.randint(ceil(self.stats["LUCK"]["max"] * .1),
                    ceil(self.stats["LUCK"]["max"] * .1) + self.stats["LUCK"]["max"]))
                # award the evolution points
                self.addStats(evo)
        return levelUP

##### CONNECTIVITY EVENTS #####
@bot.event
async def on_command_error(context, exception):
    channel = context.message.channel
    mention = context.message.author.mention
    # check possible errors
    if type(exception) == discord.ext.commands.errors.CommandNotFound:
        await narrate(channel,
            ["{}, that command doesn't exist :thinking::thinking::thinking:".\
                format(mention),
             "Use `..help` to see all available commands."]
        )
    elif type(exception) == discord.ext.commands.errors.MissingRequiredArgument:
        command = context.command
        if context.command.name == "equip" or context.command.name == "unequip":
            await narrate(channel,
                "{}, you forgot to mention the `\"gear name\"`".format(mention)
            )
        if context.command.name == "itemInfo":
            await narrate(channel,
                "{}, you forgot to mention the `\"item name\"`".format(mention)
            )
        if context.command.name == "explore":
            await narrate(channel,
                "{}, you forgot to mention the `\"floor number\"`".format(mention)
            )
        await narrate(channel,
            "Type `..help {}` to find out more about the command.".format(command)
        )
    else: # unknown error
        print(exception)
        report = "Unknown Error\nIn message: "
        report += context.message.content
        report += '\n'
        report += str(type(exception))
        eReport(report)
        await narrate(channel,
            ["It seems there was a problem {}".format(mention),
             "I'll let the devs know about that.",
             "Why don't you do something else for now? :sweat_smile::sweat_smile::sweat_smile:",
            ]
        )
        archive()

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
        return "invalid" # that way it always returns a string

# send responses
async def narrate(channel, description):
    '''description can be either a string of a list of strings.'''
    if type(description) == str:
        # print(description)
        t.sleep(2.2)
        await channel.send(description)
    elif type(description == list): # for lists
        t.sleep(2.2)
        for num, sentence in enumerate(description):
            await channel.send(sentence)
            t.sleep(2.8)
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
        newUser = {
            "username":tag,
            "access level":2,
            "dungeon top":0,
            "party": [],
            "idle":"yes",
            "resting": "no",
			"exploring": "no"
        }
        with open(USERS_LIST, 'r') as jsonData:
            try:
                currentList = json.load(jsonData) # load current contents as a dict
            except json.JSONDecodeError: # the file is empty or unreadable
                # add this user then
                currentList = {"users": [newUser,]}
            else: # if the exception wasn't raised
                currentList["users"].append(newUser) # append new user
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
    username = context.message.author.name
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
                [0, 0, 5, 0, 0, 0, 0, 0], ["chest",]
            ),
            item("Canvas Pants", ALL_ITYPES[EQPT],
                "Light-weight pants favored by many for their low price. :jeans:",
                [0, 0, 3, 0, 0, 1, 0, 0], ["legs",]
            ),
            item("Sandals", ALL_ITYPES[EQPT],
                "Easy to walk in but not the highest quality. :sandal:",
                [0, 0, 1, 0, 0, 1, 0, 0], ["feet",]
            )
        ]
        if avatar.getClass() == ALL_CLASSES[FIGT]: # if fighter grant a sword
            grants.append(
                item("Short Sword", ALL_ITYPES[EQPT],
                    "A simple arm-long iron blade for beginners. :dagger:",
                    [0, 6, 0, 0, 0, 0, 0, 0], ["rarm",]
                )
            )
        elif avatar.getClass() == ALL_CLASSES[MAGC]: # if magicaster grant a staff
            grants.append(
                item("Rod", ALL_ITYPES[EQPT],
                    "Wooden staff that help beginner casters focus. :key2:",
                    [0, 0, 0, 6, 0, 0, 0, 0], ["rarm"]
                )
            )
        else: # if survivalist grant a bow
            grants.append(
                item("Long Bow", ALL_ITYPES[EQPT],
                    "Arm-long wooden bow with a wild vine for string. :archery:",
                    [0, 5, 0, 0, 0, 1, 0, 0], ["rarm", "larm"]
                )
            )
        for grant in grants:
            avatar.receive(grant, 1) # give them out
            await narrate(context.message.channel,
                "{} was granted `{}`.".format(mention, grant.getName()))
        # grant out starting money
        avatar.cashIn(500)
        await narrate(context.message.channel,
            "{} was granted `500 i$`.".format(mention))
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
    username = context.message.author.name
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
    username = context.message.author.name
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        await narrate(context.message.channel,
            "{}'s {}\n{} has {}".format(mention, avatar.inventory(), mention,
            avatar.money()))
    else:
        await narrate(context.message.channel, 
            ["Error while loading your data!",
             "I will personally tell the devs so try later.",
             "Sorry :sweat_smile:"]
        )

# equip owned gear
@bot.command(name = "equip", help = "Equip gear stored in your bag. Composite gear names must be written in quotes. e.g.: ..equip bow   ..equip \"blue jeans\"")
async def equip(context, gearName):
    '''Makes "username"'s avatar equip "gearName" if its in their inventory.'''
    username = context.message.author.name
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
@bot.command(name = "unequip", help = "Take off gear stored in your bag.\nComposite gear names must be written in quotes.e.g.:\n..unequip bow   ..unequip \"blue jeans\"")
async def unequip(context, gearName: str):
    '''Makes "username"'s avatar equip "itemName" if its in their inventory.'''
    username = context.message.author.name
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
    username = context.message.author.name
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
    username = context.message.author.name
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
            esc = escapeChances(party, monster, 1)
            dmg = atkRound(party, monster)
            if dmg[0] == "critical":
                dmg = (dmg[0], dmg[1] / 2) # prevent critical hit misinformation
            dmg = ceil(dmg[1] / len(monster))
            rDmg = atkRound(monster, party)
            if rDmg[0] == "critical":
                rDmg = (rDmg[0], rDmg[1] / 2)
            rDmg = ceil(rDmg[1] / len(party))
            battleState += "\nDmg. dealt: `{:3d}HP`| Dmg. rec.: `{:3d}HP`| Esc. prob. = `{:2d}%`".format(dmg,rDmg, esc)
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
# invite others to a party
@bot.command(name = "invite", help = "Form a party with someone to explore together. Usage: ..invite <username>")
async def invite(context, invited: discord.User):
    '''Adds another player to your character'''
    username = context.message.author.name
    channel = context.message.channel
    mention = context.message.author.mention
    user = isUser(username)
    if user != None:
        if user["idle"] == "yes":
            invUser = isUser(invited.name)
            if invUser != None:
                if len(user["party"]) < 4:
                    if invUser["idle"] == "yes":
                        valid = False
                        accept = None
                        while not valid:
                            await narrate(channel,
                                ["Will you join {}?".format(invited.mention),
                                 "[`Yes` :thumbsup:] [`No` :thumbsdown:] >>>"])
                            accept = await userReply(await bot.wait_for("message"),
                                invited.name)
                            valid = accept.lower() in ['y', "yes", 'n', "no"]
                        if accept.lower() in ['y', "yes"]:
                            if invited.id not in user["party"]:
                                user["party"].append(invited.id)
                                invUser["party"].append(context.message.author.id)
                                invUser["idle"] = "no"
                                updateUserData(user)
                                updateUserData(invUser)
                            await narrate(channel,
                                "{} has joined {}'s party.".format(invited.mention,
                                    mention))
                        else:
                            await narrate(channel,
                                "{} refused the invitation.".format(invited.mention))
                    else:
                        await narrate(channel,
                            ["{} is not free at the moment.".format(invited["username"]),
                             "Try again later."])
                else:
                    await narrate(channel,
                        "Your party is already full {}.".format(mention))
            else:
                await narrate(channel,
                    ["You can only invite someone who is a traveler themselves.",
                     "Invite them to play {}.".format(mention)])
        else:
            await narrate(channel,
                "It seem you are busy at the moment {}".format(mention))
    else:
        await narrate(channel, ["You don't have access to that command.",
            "Use `..isekai` to travel first."])

# shows the party leader his party
@bot.command(name = "party", help = "Display the avatars that are in your party.")
async def party(context):
    '''List all members of your party.'''
    username = context.message.author.name
    mention = context.message.author.mention
    channel = context.message.channel
    user = isUser(username)
    if user != None:
        if len(user["party"]) != 0:
            party = "{}'s party:\n".format(mention)
            i = 0
            while i < len(user["party"]):
                party += bot.get_user(user["party"][i]).mention
                i += 1
            await narrate(channel, "{}.".format(party))
        else:
            await narrate(channel,
                "You don't have anyone in your party {}.".format(mention))
    else:
        await narrate(channel, ["You don't have access to that command.",
            "Use `..isekai` to travel first."])

# dispell your party
@bot.command(name = "cancelParty", help = "Dispel your party and free every single member.")
async def cancelParty(context):
    '''Remove all party members.'''
    username = context.message.author.name
    mention = context.message.author.mention
    channel = context.message.channel
    user = isUser(username)
    if user != None:
        if len(user["party"]) != 0:
            i = 0 # won't be incremented
            while i < len(user["party"]):
                invUser = isUser(bot.get_user(user["party"][i]).name)
                invUser["idle"] = "yes"
                invUser["party"] = []
                updateUserData(invUser)
                user["party"].remove(user["party"][i])
            updateUserData(user)
            await narrate(channel,
                "You sent your party members away {}.".format(mention))
        else:
            await narrate(channel,
                "You don't have anyone in your party {}.".format(mention))
    else:
        await narrate(channel, ["You don't have access to that command.",
            "Use `..isekai` to travel first."])

# explore a floor
@bot.command(name = "explore", help = "Begin the exploration of a dungeon floor. You can only explore up to the floor after the last floor you completed.\nUse <..dungeon> to see what levels are available.\nE.g.: <..explore 1> to explore first floor.")
async def explore(context, floorNum: int):
    '''Takes the avatar on the exploration of "floorNum"'''
    rnd.seed()
    username = context.message.author.name
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        if isUser(username)["idle"] == "yes": # you're free to go
            # make sure youre not free anymore
            user = isUser(username)
            user["idle"] = "no"
            user["exploring"] = "yes"
            updateUserData(user)
            # check current level explored
            top = isUser(username)["dungeon top"]
            if floorNum < 1 or floorNum > (top + 1) or floorNum > len(all_floors()):
                if top == 0:
                    await narrate(channel, ["Invalid floor selection!",
                        "You can only explore the `1` st floor."])
                else:
                    await narrate(channel, ["Invalid floor selection!",
                        "You can only explore from the `1` st floor. to the `{}` th floors."\
                            .format(top + 1)])
            else: # we got an existing available floor to the user.
                # gets the dict describing floor
                floor = floorConfig(floorNum)
                sBlocks = list()
                if floor["specials"] != None:
                    sBlocks = [(special["block"] - 1) for special in floor["specials"]]
                # make party
                explorers = [deepcopy(avatar), ]
                # add party members
                for invUserId in user["party"]:
                    invUser = isUser(bot.get_user(invUserId).name)
                    invUser["exploring"] = "yes"
                    updateUserData(invUser)
                    explorers.append(deepcopy(load(bot.get_user(invUserId).name)))
                partyName = mention
                if len(explorers) > 1:
                    partyName += "'s party"
                # start the exploration
                alive = True
                giveUp = False
                completed = False
                await narrate(channel, "{} entered `{}` in the `{}`".format(partyName,
                    floor["name"], floor["stratum"]))
                # exploration loop
                num_block = 0
                while alive and not giveUp and num_block < floor["size"]:
                    await narrate(channel, "`{}` Block `{:2d}`".format(floor["name"],
                        num_block + 1))
                    if num_block in sBlocks: # special events
                        block = None
                        i = 0
                        found = False
                        # search and find the event
                        while not found and i < len(floor["specials"]):
                            if (num_block + 1) == floor["specials"][i]["block"]:
                                block = floor["specials"][i]
                                found = True
                            else:
                                i += 1
                        # act on event
                        if block["event"] == "gathering":
                            narration = None
                            if block["type"] == "herbs":
                                narration = (floor["narration"]["intros"],
                                    floor["narration"]["herb point"],
                                    floor["narration"]["continues"])
                            elif block["type"] == "wood":
                                narration = (floor["narration"]["intros"],
                                    floor["narration"]["wood point"],
                                    floor["narration"]["continues"])
                            else: # minerals
                                narration = (floor["narration"]["intros"],
                                    floor["narration"]["mineral point"],
                                    floor["narration"]["continues"])
                            alive = await gatheringBlock(context, narration, explorers,
                                block["items"], block["rates"], floor["monsters"],
                                floor["monsters prob."], floor["swarm size"],
                                floor["danger"])
                        else:
                            print("Other events will be added later")
                    elif num_block == (floor["size"] - 1): # stairs
                        if floor["boss"] == None: # no boss
                            alive, completed = await stairsBlock(context,
                                (floor["narration"]["intros"],
                                 floor["narration"]["stairs"],
                                 floor["narration"]["completion"]),
                                explorers, floor["boss"])
                        else: # boss fight or escape
                            alive, completed = await stairsBlock(context,
                                (floor["narration"]["intros"], floor["narration"]["boss room"],
                                 floor["narration"]["completion"]),
                                explorers, floor["boss"])
                    else: # regular blocks
                        if rnd.randint(0, 99) < floor["encounter rate"] + floor["danger"]:
                            # monsters attack
                            alive = await fightBlock(context,
                                (floor["narration"]["intros"],
                                 floor["narration"]["fight"],
                                 floor["narration"]["continues"]),
                                explorers, floor["monsters"], floor["monsters prob."],
                                floor["swarm size"], floor["danger"]
                            )
                        else:
                            await emptyBlock(context,
                                (floor["narration"]["intros"],
                                 floor["narration"]["empty"],
                                 floor["narration"]["continues"]),
                                explorers
                            )
                    if alive and not giveUp:
                        num_block += 1
                # end of exploration loop
                if alive:
                    if completed:
                        await narrate(channel,
                            "{} have completed their exploration of `{}` with success!"\
                            .format(partyName, floor["name"]))
                        # update their top floor
                        current = int(floor["name"][-1])
                        for avatar in explorers:
                            user = isUser(avatar.getName())
                            if user["dungeon top"] < current: # mark floor as completed
                                user["dungeon top"] = current
                                updateUserData(user)
                    else: # not completed:
                        await narrate(channel,
                            "{} didn't complete their exploration of `{}` but they came back alive. Hooray~!"\
                            .format(partyName, floor["name"]))
                    # save
                    for avatar in explorers:
                        save(avatar)
                else: # death
                    await narrate(channel,
                        "{} have fallen... They'll do better next time!"\
                        .format(partyName, floor["name"]))
                # free the user
                user = isUser(username)
                user["idle"] = "yes"
                user["exploring"] = "no"
                updateUserData(user)
                explorers.remove(explorers[0]) # remove leader
                for member in explorers:
                    invUser = isUser(member.getName())
                    invUser["exploring"] = "no"
                    updateUserData(invUser)
        else:
            await narrate(channel,
                "But you are already doing something else {}".format(mention))
    else:
        await narrate(channel, "Only travelers can explore the dungeon {}!".format(mention))

# show available dungeon floors
@bot.command(name = "dungeon", help = "See all available dungeon floors.")
async def showFloors(context):
    '''Displays a list of all levels available for the player to see.'''
    username = context.message.author.name
    channel = context.message.channel
    mention = context.message.author.mention
    avatar = load(username)
    if avatar != None:
        available = str()
        dungeon = all_floors()
        top = isUser(username)["dungeon top"] + 1 # have access to up to the next level to current explored
        available += "`Dungeon:`\n"
        i = 0
        if top > len(dungeon):
            top = len(dungeon) # in case they explored the whole dungeon 
        while i < top:
            floor = floorConfig(i + 1)
            available += " - `{}` `{}`| Size: `{}` blocks| Danger Level: `{}`\n".\
                format(floor["stratum"], floor["name"], floor["size"], floor["danger"])
            i += 1
        await narrate(channel, available)
    else:
        await narrate(channel, "You do not have authorization for that command.")

# heal characters
@bot.command(name = "inn", help = "Allows you to rest and recover hp.")
async def rest(context):
    '''Allows an avatar to rest and recover hp.'''
    username = context.message.author.name
    mention = context.message.author.mention
    channel = context.message.channel
    user = isUser(username)
    if user != None:
        if user["idle"] != "no": # you're free
            avatar = load(username)
            lostHP = avatar.getDictStats()["HP"]["max"] - avatar.getDictStats()["HP"]["cur"]
            # intro message
            await narrate(channel,
                ["Welcome to `Sleepy Adventurer`, the best inn in the city!",
                 "You can heal your hp when you rest here."]
            )
            if lostHP != 0:
                cost = ceil(lostHP / 10) * 2 # 2i$ for 10 hp
                await narrate(channel,
                    "Sleep for the night and heal `{} HP`? Cost: `{} i$`.".format(\
                        lostHP, cost))
                # take user input
                valid = False
                choice = None
                while not valid:
                    await narrate(channel,
                        "[`Rest` :sleeping_accommodation:] [`Leave` :walking:] >>> ")
                    choice = await userReply(await bot.wait_for("message"), username)
                    if type(choice) == str:
                        valid = choice.lower() in ['r', "rest", 'l', "leave"] # valid action
                # action
                if choice.lower() in ['r', "rest"]:
                    # take the money
                    if type(avatar.getWallet().cashOut(cost)) == int: # can afford it
                        # sleep
                        user["idle"] = "no"
                        user["resting"] = "yes"
                        updateUserData(user)
                        await narrate(channel,
                            "{} barely hit the mattress that he fell in a deep sleep.".\
                            format(mention))
                        avatar.heal(lostHP)
                        await narrate(channel,
                            "{} woke up refreshed!".format(mention))
                        user["idle"] = "yes"
                        user["resting"] = "no"
                        updateUserData(user)
                        save(avatar)
                    else: # can't afford it
                        await narrate(channel,
                            "You don't have enough for this!")
                else: # leaving
                    await narrate(channel,
                        "{} decided to leave for the time being.".format(mention))
            else: # HP is full
                await narrate(channel,
                    ["{}, you seem to be in great shape already.".format(mention),
                     "Come back later."]
                )
        else: # you're busy
            await narrate(channel,
                "You can't rest at the inn if you're doing something else."
            )
    else:
        await narrate(channel,
            ["Only registered users can sleep {}".format(mention),
             "Use `..isekai` to register as a traveler."]
        )

# turn bot off
@bot.command(name = "disconnect", help = "Disconnect the bot. Only works if received from admin level user.")
async def disconnect(context):
    '''Turns the bot offline. Requires access level "ADMIN".'''
    username = context.message.author.name
    user = isUser(username)
    if user != None: # the user exists
        if user["access level"] == ADMIN: # only admin can do this
            archive() # save avatars
            await narrate(context.message.channel,
                "Roger! Going offline... :grin::grin::grin:")
            exit()
        else:
            await narrate(context.message.channel, "You do not have authorization for that command.")
    else:
        await narrate(context.message.channel, "You do not have authorization for that command.")

##### EXPLORATION MECHANICS #####
# empty block
async def emptyBlock(context, narration, party):
    '''Describes a block using intros, descriptions and continuation sentences provided.
    narration[0] are intros list
    narration[1] are descriptions list
    narration[2] are continues list'''
    rnd.seed()
    channel = context.message.channel
    # add an intro
    await narrate(channel,
        rnd.choice(narration[0]).format(mentionParty(context, party)))
    # add a random number of descriptions
    sentIndexes = rnd.sample(range(len(narration[1])), rnd.randint(1, 3))
    for index in sentIndexes:
        await narrate(channel,
            narration[1][index].format(mentionParty(context, party)))
    # add continuation
    await narrate(channel, rnd.choice(narration[2]).format(mentionParty(context, party)))

# fight block
async def fightBlock(context, narration, party, floorMonsters, monstersProb, maxMonsters,\
    dangerLvl):
    '''Narrates the start of a fight and then does the fight. Then narrates the end of the fight.'''
    rnd.seed()
    channel = context.message.channel
    # add an intro
    await narrate(channel, rnd.choice(narration[0]).format(mentionParty(context,
        party)))
    # add an description
    await narrate(channel, rnd.choice(narration[1]).format(mentionParty(context, 
        party)))
    # fight
    if await encounter(context, party, floorMonsters, monstersProb, maxMonsters,
        dangerLvl):
        await narrate(channel, rnd.choice(narration[2]).format(mentionParty(context,
            party)))
        return True
    else:
        return False

# gathering block
async def gatheringBlock(context, narration, party, itemList, itemChances,
    floorMonsters, monstersProb, maxMonsters, dangerLvl):
    '''Describes a gathering block and give the option to the team to gather or leave.
    Includes a possibility of starting a fight.'''
    channel = context.message.channel
    username = context.message.author.name
    survived = True
    # intro
    await narrate(channel,
        rnd.choice(narration[0]).format(mentionParty(context, party)))
    # point description
    for sentence in narration[1]:
        await narrate(channel, sentence.format(mentionParty(context, party)))
    # give choice gather or leave
    action = None
    gather = 0
    leave = 0
    for i, member in enumerate(party):
        if i == 0: # leader
            memberMention = context.message.author.mention
        else: # get mention of other members
            memberMention = bot.get_user(isUser(username)["party"][i-1]).mention
        valid = False
        while not valid:
            await narrate(channel, "Try gathering here {}? [`Gather` :hand_splayed:]\
            [`Leave` :man_running:] >>> ".format(memberMention))
            action = await userReply(await bot.wait_for("message"), member.getName())
            if action != None:
                valid = action.lower() in ['g', "gather", 'l', "leave"] # valid action
        if action in ['g', "gather"]:
            gather += 1
        else:
            leave += 1
    # execution
    if gather > leave:
        success = ceil((1 - (.1 * dangerLvl)) * 100) # chances of getting an item
        if rnd.randint(0, 99) > success: # monsters attacked
            await narrate(channel,
                "{} just decided to gather but suddenly monsters attacked!"\
                .format(mentionParty(context, party)))
            if await encounter(context, party, floorMonsters, monstersProb, maxMonsters, dangerLvl): # we won
                await narrate(channel,
                    "With the monsters out of the way {} got back to gathering."\
                    .format(mentionParty(context, party)))
            else:
                survived = False
        if survived:
            found = rnd.choices(itemList, weights = itemChances, k = 1)
            qty = rnd.randint(1, 3)
            await narrate(channel, "While herb picking, {} found `{} {}`!"\
                .format(mentionParty(context, party), qty, found[0]["name"]))
            for unit in party:
                unit.receive(item(found[0]["name"], found[0]["type"], found[0]["description"],
                    found[0]["stats"], found[0]["reqs"]), qty)
    # we either left or went through a gathering
    if survived:
        await narrate(channel, rnd.choice(narration[2]).format(mentionParty(context,
            party)))
    return survived

# stairs block
async def stairsBlock(context, narration, party, boss = None):
    channel = context.message.channel
    username = context.message.author.name
    completed = False
    survived = True
    # intro
    await narrate(channel, rnd.choice(narration[0]).format(mentionParty(context, party)))
    # description
    for sentence in narration[1]:
        await narrate(channel, sentence.format(mentionParty(context, party)))
    if boss == None:
        completed = True
    if boss != None: # there is a boss monster
        # fight or retreat
        action = None
        boss = 0
        city = 0
        for i, member in enumerate(party):
            if i == 0: # leader
                memberMention = context.message.author.mention
            else: # get mention of other members
                memberMention = bot.get_user(isUser(username)["party"][i-1]).mention
            valid = False
            while not valid:
                await narrate(channel, 
                    "Will you try to defeat the boss or teleport back to town {}?"\
                    .format(memberMention),
                    "[`Boss` :crossed_swords:] [`City` :homes:] >>> ")
                action = await userReply(await bot.wait_for("message"), member.getName())
                if action != None:
                    valid = action.lower() in ['b', "boss", 'c', "city"] # valid action
            if action.lower in ['b', "boss"]:
                boss += 1
            else:
                city += 1
        # depends on action
        if city >= boss:
            await narrate(channel,
                "{} decide to not take the risk of facing the boss and head back."\
                .format(mentionParty(context, party)))
            completed = False
        else:
            i = 0
            while survived and i < len(boss): # fight each form separately
                currentForm = monsterParty([boss[i],])
                if i == 0:
                    await narrate(channel, "The boss approaches.")
                elif i == (len(boss) - 1): # last form
                    await narrate(channel,
                        "Covered in the wounds you inflicted onto it, the boss\
                        furiously faces {} for the last time.".format(\
                        mentionParty(context, party)))
                else:
                    await narrate(channel,
                        "The boss roars savagely and attacks {} once more!".format(\
                        mentionParty(context, party)))
                if autoFight(context, party, copy(currentForm)): # win
                    i += 1
                    # experience
                    exp = 2 * ceil(expAwarding(party, currentForm, dangerLvl))
                    await narrate(channel,
                        "{} gained `{:3d} exp`. points.".format(\
                        mentionParty(context, party), exp))
                    for unit in party:
                        if(unit.develUp(exp)): # a true will mean they leveled up
                            await narrate(channel,
                                "`{}` has reached `lvl {:3d}`!".format(unit.getName(),
                                unit.getLvl()))
                    # loot
                    allLoot = list()
                    for unit in currentForm:
                        for drop in unit.getBag().availableInBag():
                            allLoot.append(drop) # gather all possible loot
                    dropped = rnd.sample(allLoot, rnd.randint(0, len(allLoot)))
                    if len(dropped) > 0: # something was dropped
                        for drop in dropped:
                            await narrate(channel,
                                "`{}` was dropped by the monsters.".format(drop.getName()))
                            for unit in party:
                                unit.receive(drop, 1)
                else: # lost
                    survived = False
            # out of the fight loop
            if survived:
                await narrate(channel,
                    "Finally, exhausted, {} falls down and stops moving, lifeless."\
                    .format(boss[0].getName()))
                completed = True
            else:
                await narrate(channel,
                    "{} did their best but fell to the power of the boss...".format(\
                    mentionParty(context, party)))
    # finish the exploration
    for sentence in narration[2]:
        await narrate(channel, sentence.format(mentionParty(context, party)))
    # return both survived and completed
    return (survived, completed)

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
        if unit.isAlive():
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
        if party[i]["loot"] != None:
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
    # all of party attacking party2
    rawDMG = (cumulated(party, ATK) + cumulated(party, SPATK)) / len(party)
    # all of party2 defending
    rawRES = (cumulated(party2, DEF) + cumulated(party2, SPDEF)) / len(party2)
    dmg = rawDMG - rawRES
    if dmg < 1:
        dmg = 1
    # introducing normal and critical hits
    hit = "normal"
    if rnd.randint(0, 99) < (10 + cumulated(party, CRIT)): # critical
        hit = "critical"
        dmg *= 2 # double damage
    return (hit, int(dmg))

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
    dmgFeed = str()
    unitDmg = ceil(dmg / len(party))
    i = 0
    while i < len(party):
        # introducing "weak" damage
        if party[i].isAlive():
            if rnd.randint(0, 99) < (20 + party[i].getStats()[LUCK]): # weak hit
                party[i].sufferDamage(ceil(unitDmg / 2))
                dmgFeed += "`{}` resisted the hit and lost `{} HP`.\n".format(\
                party[i].getName(), ceil(unitDmg / 2))
            else:
                party[i].sufferDamage(unitDmg)
                dmgFeed += "`{}` lost `{} HP`.\n".format(party[i].getName(), unitDmg)
            if not party[i].isAlive():  
                dmgFeed += "`{}` has fallen.\n".format(party[i].getName())
        i += 1
    return dmgFeed

# checks if the party is still alive
def partyStatus(party):
    '''Returns true if the party is alive, false elsewhere.'''
    alive = 0
    for unit in party:
        if unit.isAlive():
            alive += 1
    return alive > 0

# makes a fight loop and determine the winner
async def autoFight(context, party, party2):
    '''Simulate a fight between "party" and "party2" their opponents.
    Return true if "party" won and false else.'''
    channel = context.message.channel
    alive = True
    won = False
    turn = 0
    while alive and not won:
        battlefeed = str()
        # battle state
        battlefeed += "`TURN {}`\n{}\n\nVS\n\n{}\n".format(turn + 1, present(party2),
            present(party))
        # for turn taking
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
                battlefeed += "{} attacked:\n".format(mentionParty(context, party))
            else: # defenders == party2
                if len(attackers) == 1:
                    battlefeed += "`{}` attacked:.\n".format(attackers[0].getName())
                else:
                    battlefeed += "The monsters attacked:\n"
            damage = atkRound(attackers, defenders)
            if damage[0] == "critical":
                battlefeed += "It's a critical hit!!!\n"
            damage = damage[1] # strip string off            
            battlefeed += distributeDMG(defenders, damage) # distribute damage
            # stop the fight in case defenders were defeated
            if partyStatus(defenders):
                rounds += 1
            else: # defenders fell
                rounds += 2 # break the loop
            # swap the positions
            attackers, defenders = defenders, attackers
        # print the battle feed
        await narrate(channel, battlefeed)
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
async def encounter(context, party, floorMonsters, monstersProb, maxMonsters, dangerLvl):
    channel = context.message.channel
    username = context.message.author.name
    # init
    rnd.seed()
    survived = False
    # make monsters party
    party2 = monsterParty(floorMonsters, monstersProb, maxMonsters, dangerLvl)
    # show battle state
    await narrate(channel, ["A battle has started:", 
        "{}\n\nVS\n\n{}".format(present(party2), present(party))])
    esc = escapeChances(party, party2, dangerLvl)
    dmg = atkRound(party, party2)
    if dmg[0] == "critical":
        dmg = (dmg[0], dmg[1] / 2) # prevent critical hit misinformation
    dmg = ceil(dmg[1] / len(party2))
    rDmg = atkRound(party2, party)
    if rDmg[0] == "critical":
        rDmg = (rDmg[0], rDmg[1] / 2)
    rDmg = ceil(rDmg[1] / len(party))
    await narrate(channel,
        "Dmg. dealt: `{:3d}HP`| Dmg. rec.: `{:3d}HP`| Esc. prob. = `{:2d}%`".format(dmg,
        rDmg, esc)) 
    # action choice    
    action = None
    fight = 0
    run = 0
    for i, member in enumerate(party):
        if i == 0: # leader
            memberMention = context.message.author.mention
        else: # get mention of other members
            memberMention = bot.get_user(isUser(username)["party"][i-1]).mention
        valid = False
        while not valid:
            await narrate(channel, "What will you do {}?\n[`Fight` :crossed_swords:] \
            [`Run` :man_running:] >>> ".format(memberMention))
            action = await userReply(await bot.wait_for("message"), member.getName())
            if action != None:
                valid = action.lower() in ['f', "fight", 'r', "run"] # valid action
        if action.lower() in ['f', "fight"]:
            fight += 1
        else:
            run += 1
    # execution
    completed = False
    if run >= fight: # run first cause in case it fails the battle still happens
        if rnd.randint(0, 99) <= esc: # could get away 
            await narrate(channel,
                "{} ran so quickly that the monsters couldn't catch up.".format(\
                mentionParty(context, party)))
            completed = True
            survived = True
        else:
            await narrate(channel,
                "{} bolted but the monsters stopped them in their track.".format(\
                mentionParty(context, party)))
    if not completed: # team didn't try to or didn't manage to escape
        # recompute probabilities
        if await autoFight(context, party, copy(party2)): # win
            survived = True
            await narrate(channel, "The battle has ended.")
            # experience
            exp = ceil(expAwarding(party, party2, dangerLvl))
            await narrate(channel,
                "{} gained `{:3d} exp`. points.".format(mentionParty(context, party), exp))
            for unit in party:
                if(unit.develUp(exp)): # a true will mean they leveled up
                    await narrate(channel,
                        "`{}` has reached `lvl {:3d}`!".format(unit.getName(),
                        unit.getLvl()))
            # loot
            for monster in party2:
                for i, drop in enumerate(monster.getBag().availableInBag()):
                    # 80% of chance of dropping the 1st item
                    # 70% of dropping 2nd etc...
                    if rnd.randint(0, 99) < (80 - i * 10):
                        await narrate(channel,
                            "{} collected `{}` from the {}'s carcass.".format(\
                            mentionParty(context, party), drop.getName(), 
                                monster.getName())
                        )
                        for unit in party:
                            unit.receive(drop, 1)
        else: # lost
            survived = False
    return survived

##### HELPER FUNCTIONS #####
# return a string to identify a party.
def mentionParty(context, party):
    '''"party" is a list of isekai mobs.'''
    mention = context.message.author.mention
    if len(party) > 1:
        mention += "'s party"
    return mention

# count how many floors are in the dungeon
def all_floors():
    '''Return the config files for all dungeon floor'''
    allFloors = [f for f in os.listdir(DUNGEON_PATH) if isfile(join(DUNGEON_PATH, f))]
    return allFloors
    
# import dungeon config from file
def floorConfig(num: int):
    '''Open a floor file and returns the contents.'''
    config = None
    with open(str().join([DUNGEON_PATH, '/', str(num), ".json"]), 'r') as ioData:
        config = json.load(ioData)
    return config["floor"]
    
# log errors
def eReport(report):
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
        return (database[i])
    else:
        return None

# compare two strings
def areSame(string, string2):
    '''Compare two strings by lower casing both and checking character by character.
    Return True if they're similar, False elesewise.'''
    return string.lower() == string2.lower()

def updateUserData(newData: dict):
    '''Changes the contents of the "users.json" file.'''
    # load current content
    userlist = None
    with open(USERS_LIST, 'r') as jsonData:
        userlist = json.load(jsonData)["users"]
        for user in userlist:
            if user["username"] == newData["username"]:
                # update
                for key in user:
                    user[key] = newData[key]
        # save file
    # turn it into a dict
    with open(USERS_LIST, 'w') as jsonData:
        json.dump({"users": userlist}, jsonData, indent = 4)

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
    