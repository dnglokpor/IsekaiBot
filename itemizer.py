import json
from copy import copy, deepcopy

# files
CONSUMABLES_FILE = "consumable.json"
NON_CONSUMABLES_FILE = "n_consumable.json"
EQUIPMENT_FILE = "equipment.json"

# items constants
CONS = 0
N_CONS = 1
EQPT = 2
ALL_ITYPES = ["consumable", "n_consumable", "equipment"]
BODY_PARTS = ["head", "larm", "rarm", "chest", "legs", "feet", "accessory"]
LIT_BODY_PARTS = ["the Head", "the Left arm", "the Right arm", "the Chest", "the Legs", "Feet", "as an Accessory"]
# stats
HP = 0
ATK = 1
DEF = 2
SPATK = 3
SPDEF = 4
AGI = 5
CRIT = 6
LUCK = 7
STATS_LIST = ["HP", "ATK", "DEF", "SPATK", "SPDEF", "AGI", "CRIT", "LUCK"]

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

# helper functions
# read a yes or no answer
def yesOrNo():
    valid = False
    userInput = None
    while not valid:
        userInput = input("[YES] / [NO]: ")
        if userInput.lower() in ["yes", "no"]:
            valid = True
    return userInput

# read a string
def readString():
    valid = False
    userInput = None
    while not valid:
        userInput = input()
        if len(userInput) > 1:
            try:
                int(userInput)
            except ValueError: # not a number
                valid = True
            else:
                print("You need to enter a string of more than 1 character!")
                userInput = None
    return userInput

# read a number
def readNum():
    valid = False
    userInput = None
    while not valid:
        userInput = input()
        if len(userInput) > 0:
            try:
                int(userInput)
            except ValueError:
                print("You need to enter a number!")
                userInput = None
            else:
                valid = True
    return int(userInput)

# read the stat list of the item
def readStats():
    stats = list()
    valid = False
    while not valid:
        print("Please enter the values on each stats.\nHow much does this item affect...")
        for i in range(len(STATS_LIST)):
            print("...{}?".format(STATS_LIST[i]))
            stats.append(readNum())
        print("Stats: HP: {}|ATK: {}|DEF: {}|SPATK: {}|SPDEF: {}|AGI: {}|CRIT: {}|LUCK: {}"\
            .format(stats[HP], stats[ATK], stats[DEF], stats[SPATK], stats[SPDEF], stats[AGI],
            stats[CRIT], stats[LUCK]))
        if yesOrNo() == "yes":
            valid = True
        else:
            print("\nOkay let's start over.")
            stats = list() # clean the current list
    return stats

# read gear requirements
def readReqs():
    reqs = list()
    valid = False
    while not valid:
        print("\nGear can be equiped in {} possible places: head, left arm, right arm, chest, legs, feet and an accessory.".format(len(BODY_PARTS)))
        print("A gear can only be equipped to up to 2 body parts.")
        i = 0
        complete = False
        while not complete and i < len(BODY_PARTS):
            print("Will it be equiped on [{}]?".format(LIT_BODY_PARTS[i]))
            if yesOrNo() == "yes":
                reqs.append(BODY_PARTS[i])
                complete = len(reqs) == 2
            i += 1
        print("\n{}\nSave these?".format(reqs))
        if yesOrNo() == "yes":
            valid = True
    return reqs
    
# write names with first letters capitalized
def nameCapitalize(name):
    i = 0
    foundSpace = False
    while i < len(name) and not foundSpace: # looks for spacing
        if name[i] == ' ':
            foundSpace = True
        else:
            i += 1
    if foundSpace: # name is composite
        wordList = name.split(' ')
        i = 0
        while i < len(wordList): 
            capitalized = wordList[i][0].upper()
            for char in wordList[i][1:]:
                capitalized += char.lower()
            wordList[i] = capitalized
            i += 1
        name = ' '.join(wordList)
    else: # we got a simple one word mame
        capitalized = name[0].upper()
        for char in name[1:]:
            capitalized += char.lower()
        name = capitalized 
    # done we return it
    return name

if __name__ == "__main__":
    # app start
    running = True
    while running: # infinite loop
        print("Hi! This is a helper app to make items for IsekaiBot game!\n")
        userChoice = None
        # menu loop
        while userChoice == None:
            print("[1] - make consumable item\n[2] - make non consumable item\n[3] - make equipment\n[0] - exit program")
            userChoice = input("What do you want to do? [1]/[2]/[3]/[0]: ")
            print('\n')
            try:
                userChoice = int(userChoice)
            except ValueError:
                userChoice = None
            else:
                if userChoice not in range(4):
                    userChoice = None
            # confirmation
            if userChoice == 0:
                print("Quit the program? ")
            if userChoice == 1:
                print("Consumables are items like potions that can be used to give immediate effect. ")
                print("Is this what you wish to make?")
            if userChoice == 2:
                print("Non-consumables are items that can be collected but not directly used like monsters drops. ")
                print("Is this what you wish to make?")
            if userChoice == 3:
                print("Equipment is gear that can be equiped by an isekaiMob like a sword. ")
                print("Is this what you wish to make?")
            if userChoice in range(4):
                if yesOrNo() == "no":
                        userChoice = None
        # out of menu loop
        # action loop
        if userChoice == 0: # quit
            print("Understood. Bye!")
            running = False
        if userChoice in [1, 2, 3]: # making something
            itemName = None
            itemType = None
            itemDescription = None
            itemStats = None
            itemRequirements = None
            #1 get type
            if userChoice == 1: # making item
                print("Understood. Let's make some consumables!\n")
                itemType = ALL_ITYPES[CONS] # set type
            elif userChoice == 2: # making non cons
                print("Understood. Let's make some non-consumables!\n")
                itemType = ALL_ITYPES[N_CONS] # set type
            else: # gear
                print("Understood. Let's make some equipment!\n")
                itemType = ALL_ITYPES[EQPT] # set type
            #2 get the name for anything
            print("What's the name of the item?: ")
            itemName = nameCapitalize(readString())
            #3 get requirements for gear
            if userChoice == 3:
                itemRequirements = readReqs()
            #4 get stats for consumables or gear
            if userChoice in [1, 3]:
                itemStats = readStats()
            #5 get a trivia description for anything
            print("\nEnter a short description that will be displayed as trivia for your item. This can be more than one sentence.")
            itemDescription = readString()
            # print for completion
            print("\nCongrats you just made this item:\n")
            print(item(itemName, itemType, itemDescription, itemStats, itemRequirements).descr())
            '''print("Name: {}".format(itemName))
            print("Type: {}".format(itemType))
            print("Description: {}".format(itemDescription))
            if itemStats != None:
                print("Stats: HP: {}|ATK: {}|DEF: {}|SPATK: {}|SPDEF: {}|AGI: {}".format(itemStats[HP],
                    itemStats[ATK], itemStats[DEF], itemStats[SPATK], itemStats[SPDEF],
                    itemStats[AGI]))
            if itemRequirements != None:
                print("Requirements: {}".format(itemRequirements))'''
            print("Save it? ")
            if yesOrNo() == "yes":
                if itemType == ALL_ITYPES[CONS]:
                    filename = CONSUMABLES_FILE
                elif itemType == ALL_ITYPES[N_CONS]:
                    filename = NON_CONSUMABLES_FILE
                else:
                    filename = EQUIPMENT_FILE
                itemList = None
                try:
                    with open(filename, 'r') as jsonData:
                        try:
                            itemList = json.load(jsonData) # load current contents as a dict
                        except json.JSONDecodeError: # the file is unreadable
                            itemList = {
                                itemType: [
                                    {
                                        "name": itemName,
                                        "description": itemDescription,
                                        "stats": itemStats,
                                        "requirements": itemRequirements
                                    }
                                ]
                            } # add this item
                        else:
                            itemList[itemType].append(
                                {
                                    "name": itemName,
                                    "description": itemDescription,
                                    "stats": itemStats,
                                    "requirements": itemRequirements
                                }
                            )# append new user
                except FileNotFoundError: # the file is empty
                    itemList = {
                        itemType: [
                            {
                                "name": itemName,
                                "description": itemDescription,
                                "stats": itemStats,
                                "requirements": itemRequirements
                            }
                        ]
                    } # add this item
                with open(filename, "w") as jsonData: # reset the file before writing
                    json.dump(itemList, jsonData, indent = 4) # save the new list
                print("\nYour item was saved to {}.".format(filename))
            else:
                print("\nOkay let's discard all this and start over.")