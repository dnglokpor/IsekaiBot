# Isekai tactics
# fighting implements

# import
from copy import copy, deepcopy
from math import ceil, floor, exp
import random as rnd
import time as t
import sys
import json

# define
PROB_RANGE = range(100)
HP = 0
ATK = 1
DEF = 2
SPATK = 3
SPDEF = 4
AGI = 5

# constants
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

# adventurers and monsters
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
        '''Increase "self.stats" by a list of stats.'''
        for i, stat in self.stats:
            if stat != "HP": # current HP won't change on the fly
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
        descr += "ATK: {:3d}|DEF: {:3d}|SPATK: {:3d}|SPDEF: {:3d}| AGI: {:3d}| CRIT: {:3d}| LUCK: {:3d}\n".format(
            self.stats["ATK"]["cur"], self.stats["DEF"]["cur"], self.stats["SPATK"]["cur"],
            self.stats["SPDEF"]["cur"], self.stats["AGI"]["cur"], self.stats["CRIT"]["cur"],
            self.stats["LUCK"]["cur"])
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

# helper functions
# compare two strings
def areSame(string, string2):
    '''Compare two strings by lower casing both and checking character by character.
    Return True if they're similar, False elesewise.'''
    return string.lower() == string2.lower()

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
    rawDMG = (cumulated(party, ATK) + cumulated(party, SPATK))
    print("rawD: {}".format(rawDMG))
    rawRES = (cumulated(party2, DEF) + cumulated(party2, SPDEF))
    print("rawR: {}".format(rawRES))
    dmg = rawDMG - rawRES
    print("dmg: {}".format(dmg))
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
    unitDmg = ceil(dmg / len(party))
    i = 0
    while i < len(party):
        # introducing "weak" damage
        if rnd.randint(0, 99) < (20 + party[i].getStats()[LUCK]): # weak hit
            party[i].sufferDamage(ceil(unitDmg / 2))
            print("{} resisted the hit and lost {} HP.".format(party[i].getName(),
                ceil(unitDmg / 2)))
        else:
            party[i].sufferDamage(unitDmg)
            print("{} lost {} HP.".format(party[i].getName(), unitDmg))
        if not party[i].isAlive():  
            print("{} has fallen.".format(party[i].getName()))
            party.remove(party[i])
        else:
            i += 1

# checks if the party is still alive
def partyStatus(party):
    '''Returns true if the party is alive, false elsewhere.'''
    alive = 0
    if len(party) > 0:
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
                if len(attackers) == 1:
                    print("{} attacked:".format(attackers[0].getName()))
                else:
                    print("The party attacked:")
            else: # defenders == party2
                if len(attackers) == 1:
                    print("{} attacked:.".format(attackers[0].getName()))
                else:
                    print("The monsters attacked:")
            damage = atkRound(attackers, defenders)
            if damage[0] == "critical":
                print("It's a critical hit!!!")
            damage = damage[1] # strip string off            
            distributeDMG(defenders, damage) # distribute damage
            i = 0
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
    dmg = atkRound(party, party2)
    if dmg[0] == "critical":
        dmg = (dmg[0], dmg[1] / 2) # prevent critical hit misinformation
    dmg = ceil(dmg[1] / len(party2))
    rDmg = atkRound(party2, party)
    if rDmg[0] == "critical":
        rDmg = (rDmg[0], rDmg[1] / 2)
    rDmg = ceil(rDmg[1] / len(party))
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
        if autoFight(deepcopy(party), deepcopy(party2)): # win
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

# events
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
            qty = rnd.randint(1, 5)
            print("While herb picking, the party found `{} {}`!".format(qty, found[0]["name"]))
            for unit in party:
                unit.receive(item(found[0]["name"], found[0]["type"], found[0]["description"],
                    found[0]["stats"], found[0]["reqs"]), qty)
    # we either left or went through a gathering
    if survived:
        print(rnd.choice(narration[2]))
    return survived

# stairs block
def stairsBlock(narration, party, boss = None):
    completed = False
    survived = True
    # intro
    print(rnd.choice(narration[0]))
    # description
    for sentence in narration[1]:
        print(sentence)
    if boss == None:
        completed = True
    if boss != None: # there is a boss monster
        valid = False
        action = None
        while not valid:
            action = input("Will you try to defeat the boss room or teleport back to town? [Boss] [City] >>> ")
            valid = action.lower() in ['b', "boss", 'c', "city"]
        # depends on action
        if action in ['c', "city"]:
            print("You decide to not take the risk of facing the boss and head back.")
            completed = False
        else:
            i = 0
            while survived and i < len(boss): # fight each form separately
                currentForm = monsterParty([boss[i],])
                if i == 0:
                    print("The boss approaches.")
                elif i == (len(boss) - 1): # last form
                    print("Covered in the wounds you inflicted onto it, the boss furiously faces you for the last time.")
                else:
                    print("The boss roars savagely and attacks you once more!")
                if autoFight(party, currentForm): # win
                    i += 1
                    # experience
                    exp = ceil(expAwarding(party, currentForm, dangerLvl))
                    if len(party) > 1:
                        print("Each party member gained `{:3d} exp`. points.".format(exp))
                    else:
                        print("{} gained `{:3d} exp`. points.".format(party[0].getName(), exp))
                    for unit in party:
                        if(unit.develUp(exp)): # a true will mean they leveled up
                            print("`{}` has reached `lvl {:3d}`!".format(unit.getName(), unit.getLvl()))
                    # loot
                    allLoot = list()
                    for unit in currentForm:
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
            # out of the fight loop
            if survived:
                print("Finally, exhausted, the boss falls down and stops moving, lifeless.")
                completed = True
            else:
                print("You did your best but fell to the power of the boss...")
    # finish the exploration
    for sentence in narration[2]:
        print(sentence)
    # return both survived and completed
    return (survived, completed)

# import dungeon config from file
def readConfig():
    '''Open the isekaiDungeon.json file to recover dungeon config and return it.'''
    FILE = "isekaiDungeon.json"
    config = None
    with open(FILE, 'r') as ioData:
        config =  json.load(ioData)
    return config

# gets the contents of a specific floor
def getFloor(num):
    '''Loads the floor that the user requested into memory and return it.'''
    key = ' '.join(["Floor", str(num)])
    inStratum = num // 5 # 5 floors per stratum
    sKey = str()
    if inStratum == 0:
        sKey = "Verdant Green Stratum"
    else:
        return
    dungeon = readConfig()["Dungeon"]
    floor = dungeon[inStratum][sKey][num - 1]
    return floor

# return a string to identify a party.
def mentionParty(party):
    '''"party" is a list of isekai mobs.'''
    mention = str()
    if len(party) == 1:
        mention = party[0].getName()
    else:
        if party[0].getClass() == ALL_CLASSES[MNST]:
            mention = "The monsters"
        else:
            mention = "The party"
    return mention

if __name__ == "__main__":
    adventurerName = "@myLewysG"
    # same for all blocks
    introSeqs = [
        "As {} walked through the vast greenery, they spotted a wide open clearing.".format(adventurerName),
        "As {} explored the green forest, they saw a cluster of tall bushes.".format(adventurerName),
        "Walking through a patch of tall grass, {} came across a group of tall trees.".format(adventurerName),
    ]
    contSeqs = [
        "{} decided to move on.".format(adventurerName),
        "There was nothing more to do there so {} kept on going.".format(adventurerName),
        "Bored, {} decided to continue their exploration.".format(adventurerName)
    ]
    # description sequences vary per blocks
    emptySeqs = [
        "A carpet of pretty flowers laid there in their sight and their scent filled the air.",
        "The ground was covered in a thick layer of green grass, sparse with moss covered rocks or branches.",
        "The foliage of the trees blocked most of the sunlight but not as much of the heat.",
        "{} stopped to listen to the noises of nature: birdsongs by the dungeon unique birds.".format(adventurerName),
        "A bunch of rocks of different sizes could be seen here and there, and covered in green moss.",
        "A small stream could be seen meandering at the base of what seemed to be a small hill.",
        "There was a huge log in the middle of the clearing, covered in strange mushrooms.",
        "A small breeze rose and blew a bunch of dead leaves all around you but quickly faded away."
    ]
    fightSeqs = [
        "Suddenly, they felt a hostile presence and sure enough {} encountered monsters.".format(adventurerName),
        "Out of nowhere a group of monsters jumped upon the unsuspecting {}.".format(adventurerName),
        "{} just had the chance to take their weapons that they were face to face with monsters.".format(adventurerName)
    ]
    herbSeqs = [
        "They saw that the whole place was covered in various and diverse herbs.",
        "Certainly gathering herbs here could lead to some results."
    ]
    stairsSeqs = [
        "They see a weird light pillar a little bit forward and steadily walk toward it.",
        "Upon realizing it is the teleporter that leads back to the city, they happily run to it."
    ]
    bossSeqs = [
        "Right in front of them, they saw the biggest double doors they've never seen.",
        "They couldn't tell what material it was made of but it glowed of a faint whitish color.",
        "Behind it, an ominous presence could be felt and they knew they will have to fight it to the death.",
        "Also, on the right of the doors, there was a teleporter leading to the city."
    ]
    endSeqs = [
        "It is the end of your exploration.",
        "You are magically transported back to the city."
    ]
    # test adventurers
    mylewysg = isekaiMob("myLewysG", ALL_CLASSES[FIGT], 1, [40, 18, 19, 12, 10, 10, 1, 1])
    deathforron = isekaiMob("Death For Ron", ALL_CLASSES[MAGC], 1, BASE_STATS)
    advParty = [mylewysg, deathforron]
    print(mentionParty(advParty))
    sys.exit()
    # test monsters
    floorMonsters = [
        {
            "name": "Green Slime",
            "class": ALL_CLASSES[MNST],
            "level": 1,
            "stats": [15, 18, 9, 13, 7, 7, 1, 1],
            "loot": [
                {
                    "name": "Green Core Fragments",
                    "type": ALL_ITYPES[N_CONS],
                    "description": "Fragments of the core that once kept a Green Slime alive.",
                    "stats": None,
                    "reqs": None
                }
            ]
        },
        {
            "name": "Punny Bunny",
            "class": ALL_CLASSES[MNST],
            "level": 1,
            "stats": [15, 9, 5, 2, 3, 6, 1, 1],
            "loot": [
                {
                    "name": "White Pelt",
                    "type": ALL_ITYPES[N_CONS],
                    "description": "\"Neige\" coloured pelt of a freshly skinned Punny Bunny.",
                    "stats": None,
                    "reqs": None
                }
            ]
        },
        {
            "name": "Angry Cuckoo",
            "class": ALL_CLASSES[MNST],
            "level": 1,
            "stats": [18, 11, 4, 1, 4, 8, 2, 1],
            "loot": [
                {
                    "name": "Short Down",
                    "type": ALL_ITYPES[N_CONS],
                    "description":  "A feather from a dungeon bird monster.",
                    "stats": None,
                    "reqs": None
                },
                {
                    "name": "Weird Seeds",
                    "type": ALL_ITYPES[N_CONS],
                    "description":  "Often found in dead bird monsters stomach. No one knows where they find them.",
                    "stats": None,
                    "reqs": None
                }
            ]
        }
    ]
    encounter([mylewysg,], [{
            "name": "Punny Bunny",
            "class": ALL_CLASSES[MNST],
            "level": 1,
            "stats": [18, 17, 10, 15, 5, 11, 1, 1],
            "loot": [
                {
                    "name": "White Pelt",
                    "type": ALL_ITYPES[N_CONS],
                    "description": "\"Neige\" coloured pelt of a freshly skinned Punny Bunny.",
                    "stats": None,
                    "reqs": None
                }
            ]
        },], [100,], 5, 1)
    sys.exit()
    monstersProb = [50, 40, 10]
    encounterProb = 70
    maxMonsters = 3
    dangerLvl = 1
    # test gathering
    herbs = [
        {
            "name": "Bittherb",
            "type": ALL_ITYPES[N_CONS],
            "description": "They say it is most bitter herb in the world. Good for making remedies.",
            "stats": None,
            "reqs": None
        },
        {
            "name": "Moon Flower",
            "type": ALL_ITYPES[N_CONS],
            "description": "A flower that grows towards the moon. Often found in forests under tall trees.",
            "stats": None,
            "reqs": None
        },
        {
            "name": "Blade Grass",
            "type": ALL_ITYPES[N_CONS],
            "description": "Beware cuts. Smiths believe that using it in their fire make their weapons sharper.",
            "stats": None,
            "reqs": None
        }
    ]
    herbsProb = [60, 10, 30]
    # test boss
    bosses = [
        {
            "name": "Kingckoo",
            "class": ALL_CLASSES[MNST],
            "level": 3,
            "stats": [23, 15, 10, 6, 6, 8, 5, 5],
            "loot": None
        },
        {
            "name": "Kingckoo",
            "class": ALL_CLASSES[MNST],
            "level": 3,
            "stats": [25, 16, 10, 6, 6, 8, 6, 6],
            "loot": None
        },
        {
            "name": "Kingckoo",
            "class": ALL_CLASSES[MNST],
            "level": 3,
            "stats": [30, 18, 12, 6, 6, 8, 7, 7],
            "loot": [
                {
                    "name": "King Talon",
                    "type": ALL_ITYPES[N_CONS],
                    "description": "Talon of the King of the cuckoos. Elastic yet durable.",
                    "stats": None,
                    "reqs": None
                }
            ]
        }
    ]
    # emptyBlock((introSeqs, emptySeqs, contSeqs))
    # fightBlock((introSeqs, fightSeqs, contSeqs), [mylewysg,],
    #    floorMonsters, monstersProb, maxMonsters, dangerLvl)
    # gatheringBlock((introSeqs, herbSeqs, contSeqs), [mylewysg,], herbs, herbsProb,
    #        floorMonsters, monstersProb, maxMonsters, dangerLvl)
    #if stairsBlock((introSeqs, stairsSeqs, endSeqs), advParty):
    #    print("You completed the exploration with success".format(adventurerName))
    # survived, completed = stairsBlock((introSeqs, bossSeqs, endSeqs), advParty, bosses)
    '''alive = True
    completed = False
    numOfBlocks = 10
    i = 0
    while alive and (i in range(numOfBlocks)):
        print("Bloc {}".format(i + 1))
        if i == 6: # gathering
            alive = gatheringBlock((introSeqs, herbSeqs, contSeqs), advParty,
                herbs, herbsProb, floorMonsters, monstersProb, maxMonsters, dangerLvl)
        elif i == numOfBlocks - 1: # stairs
            alive, completed = stairsBlock((introSeqs, bossSeqs, endSeqs), advParty, bosses)
        else:
            if rnd.randint(0, 99) < encounterProb + dangerLvl: # monsters attack
                alive = fightBlock((introSeqs, fightSeqs, contSeqs), advParty, floorMonsters,
                    monstersProb, maxMonsters, dangerLvl)
            else:
                emptyBlock((introSeqs, emptySeqs, contSeqs))
        if alive:
            i += 1
        else:
            print("The party has fallen... ... ...")
    # out of exploration loop
    if alive and completed:
        print("\nYou completed the exploration with success")
        for unit in advParty:
            print(unit.getBag().reveal())
            print('\n')
    elif alive and not completed:
        print("\nYou didn't complete the exploration but you came back alive. That's great.")
        for unit in advParty:
            print(unit.getBag().reveal())
            print('\n')
    else:
        print("\nMission failed. We will get them next time!")
        print("You lost all you found during the exploration...")'''