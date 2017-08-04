import heroes
import skills
import math

# Initial logic and code by /r/AnduCrandu
# Python conversion and revisions by /r/Meteorchestra

heroes = heroes.heroList
skills = skills.skillList
#Dummy empty skill
skills["None"] = {
		"sp":-10,
		"slot":"none",
		"inheritrule":""}
		
data = {}
data["weaponTypes"] = ["sword","lance","axe","redtome",
		"bluetome","greentome","dragon","bow","dagger","staff"]
data["rangedWeapons"] = ["redtome","bluetome","greentome","bow","dagger","staff"]
data["meleeWeapons"] = ["sword","lance","axe","dragon"]
data["physicalWeapons"] = ["sword","lance","axe","bow","dagger"]
data["magicalWeapons"] = ["redtome","bluetome","greentome","dragon","staff"]
data["moveTypes"] = ["infantry","armored","flying","cavalry"]
data["colors"] = ["red","blue","green","gray"]
data["skillSlots"] = ["weapon","special","a","b","c","s"]
data["buffTypes"] = ["buffs","debuffs","spur"]
data["buffStats"] = ["atk","spd","def","res"]
data["stats"] = ["hp","atk","spd","def","res"]
data["growths"] = [[6,8,9,11,13,14,16,18,19,21,23,24],
		[7,8,10,12,14,15,17,19,21,23,25,26],
		[7,9,11,13,15,17,19,21,23,25,27,29],
		[8,10,12,14,16,18,20,22,24,26,28,31],
		[8,10,13,15,17,19,22,24,26,28,30,33]]
		
#Holder for options that aren't hero-specific
options = {}
options["autoCalculate"] = True
options["startTurn"] = 0
options["useGaleforce"] = True
options["threatenRule"] = "Neither"
options["ployBehavior"] = "Diagonal"
options["showOnlyMaxSkills"] = True
options["hideUnaffectingSkills"] = True
options["useCustomEnemyList"] = None
options["customEnemyListFormat"] = "Builds"
options["viewFilter"] = "all"
options["sortOrder"] = 1
options["roundInitiators"] = "CE"
options["output"] = "Verbose"
options["stats"] = ["Wins", "Losses", "Inconclusive"]
options["debug"] = None
options["comparebuildsslots"] = data["skillSlots"]
options["comparebuildstopskills"] = 4
options["comparebuildsresultslimit"] = 100
options["exportbuilds"] = 0
options["adjacentallies"] = 0

#Applies some default values to skills
def buildSkillWithDefaults(baseSkill):
	fieldsToDefaultToZero = ["charge", "affectsduel", "ismax", "hp", "atk", "spd",
			"def", "res"]
	for field in fieldsToDefaultToZero:
		if field not in baseSkill:
			baseSkill[field] = 0
	if "condition" not in baseSkill:
		baseSkill["condition"] = {"type":None}
	elif baseSkill["condition"]["type"] == "adjacency":
		#Set up skills that depend on adjacent allies using the option value
		effect = baseSkill["condition"]["effect"]
		baseSkill[effect] = {}
		for field in baseSkill["condition"]["each"]:
			baseSkill[effect][field] = baseSkill["condition"]["each"][field] * options["adjacentallies"]
	return baseSkill
	
#Get a complete mapping of valid skills for each slot for the unit with the given name
def getValidSkills(name):
	validSkills = {}
	for slot in data["skillSlots"]:
		validSkills[slot] = getValidSkillsForSlot(name, slot)
	return validSkills
	
#Returns an array of skill names for skills that hero can learn
#If hero not named, returns all skills in slot except unique
#If not given slot, gives skills for all slots
def getValidSkillsForSlot(name, slot):
	validSkills = []
	for skillName in skills:
		skill = skills[skillName]
		#Inherit rules can be comma-separated if multiple rules must be met, thanks to Galeforce
		inheritRules = skill["inheritrule"].split(",")
		#Some skills only require matching some rules
		#Ex: Shield Pulse requires melee attack type and infantry OR armored move type
		if "rulestomatch" in skill:
			rulesToMatch = skill["rulestomatch"]
		else:
			rulesToMatch = len(inheritRules)
		if ((not slot) or (skill["slot"] == slot)):
			if name:
				attackType = getAttackTypeFromWeapon(heroes[name]["weapontype"])
				attackDistance = getAttackDistanceFromWeapon(heroes[name]["weapontype"])
				inheritRuleMatches = 0
				for rule in inheritRules:
					if rule == "unique":
						#Can only use if hero starts with it
						if skillName in heroes[name]["skills"]:
							inheritRuleMatches += 1
					elif (attackType == rule):
						#Inherit if weapon is right attacking type
						inheritRuleMatches += 1
					elif (rule in data["weaponTypes"]):
						#Inherit if weapon is right
						if (heroes[name]["weapontype"] == rule):
							inheritRuleMatches += 1
					elif (rule in data["moveTypes"]):
						#Inherit if movetype is right
						if (heroes[name]["movetype"] == rule):
							inheritRuleMatches += 1
					elif (rule.replace("non","") in data["weaponTypes"]):
						#Inherit if NOT a certain weapon
						if (heroes[name]["weapontype"] != rule.replace("non","")):
							inheritRuleMatches += 1
					elif (rule.replace("non","") in data["moveTypes"]):
						#Inherit if NOT a certain movement type
						if (heroes[name]["movetype"] != rule.replace("non","")):
							inheritRuleMatches += 1
					elif (rule.replace("non","") in data["colors"]):
						#Inherit if not a certain color
						if (heroes[name]["color"] != rule.replace("non","")):
							inheritRuleMatches += 1
					elif (rule == attackDistance):
						#Inherit if attack distance is right
						inheritRuleMatches += 1
					elif (rule == ""):
						#Everyone can inherit!
						inheritRuleMatches += 1

					if (inheritRuleMatches >= rulesToMatch):
						validSkills.append(skillName)
			else:
				#It's the right slot, not given a hero, so it's valid unless unique
				if (inheritRules[0] != "unique"):
					validSkills.append(skillName)
	return validSkills
	
#Check whether a given skill should be included for build comparisons
def isRelevantForBuilds(skillName):
	return skills[skillName]["affectsduel"] and skills[skillName]["ismax"]
	
#Build all possible skillsets from the lists of valid skills for this hero
def buildSkillsets(hero, slots=options["comparebuildsslots"]):
	skillsets = []
	skillsetOptions = {}
	for slot in data["skillSlots"]:
		if slot in slots:
			skillsetOptions[slot] = filter(isRelevantForBuilds, hero["validSkills"][slot])
		else:
			skillsetOptions[slot] = [hero[slot]]
		
	for a in skillsetOptions["a"]:
		for b in skillsetOptions["b"]:
			for c in skillsetOptions["c"]:
				for s in skillsetOptions["s"]:
					for special in skillsetOptions["special"]:
						for weapon in skillsetOptions["weapon"]:
							skillsets.append({
								"a": a,
								"b": b,
								"c": c,
								"s": s,
								"special": special,
								"weapon": weapon})
	return skillsets

def getAttackTypeFromWeapon(weaponType):
	if (weaponType in data["physicalWeapons"]):
		return "physical"
	elif (weaponType in data["magicalWeapons"]):
		return "magical"
	else:
		return "unknown"
		
def getAttackDistanceFromWeapon(weaponType):
	if (weaponType in data["meleeWeapons"]):
		return "melee"
	elif (weaponType in data["rangedWeapons"]):
		return "ranged"
	else:
		return "unknown"

#Finds max skills for a given rarity (based on sp cost)
def getMaxSkills(hero, rarity):	
	maxSkillset = {"weapon":"None","special":"None","a":"None","b":"None","c":"None","s":"None"}
	for skillName in heroes[hero]["skills"]:
		skill = skills[skillName] 
		if (heroes[hero]["skills"][skillName] <= rarity):
			if (skills[maxSkillset[skill["slot"]]]["sp"] < skill["sp"]):
					maxSkillset[skill["slot"]] = skillName
	return maxSkillset
	
#Initialize a hero's information (and skills and skillsets if needed)
def initHero(hero, alreadyHasSkills=False, alreadyHasSkillsets=False):
	name = hero["name"]
	
	setGeneralInfo(hero)
		
	if not alreadyHasSkillsets:
			hero["validSkills"] = getValidSkills(name)

	if alreadyHasSkills:
		#validate that the skills it already has are okay
		for slot in data["skillSlots"]:
			if hero[slot] not in hero["validSkills"][slot]:
				hero[slot] = "None"
			#default empty slots back to normal
			if hero[slot] == "None" and slot != "s":
				hero[slot] = heroes[name]["maxSkills"][hero["rarity"]][slot]
	else:
		setSkills(hero)
	setStats(hero)
	
def setGeneralInfo(hero):
	name = hero["name"]
	hero["movetype"] = heroes[name]["movetype"]
	hero["weapontype"] = heroes[name]["weapontype"]
	hero["color"] = heroes[name]["color"]
	hero["range"] = getAttackDistanceFromWeapon(hero["weapontype"])
	hero["attacktype"] = getAttackTypeFromWeapon(hero["weapontype"])

def setSkills(hero):
	for slot in data["skillSlots"]:
		hero[slot] = heroes[hero["name"]]["maxSkills"][hero["rarity"]][slot]

def setStats(hero):
	growthValMod = {"hp":0,"atk":0,"spd":0,"def":0,"res":0}
	if (hero["boon"] != "none"):
		growthValMod[hero["boon"]] += 1
	if (hero["bane"] != "none"):
		growthValMod[hero["bane"]] -= 1

	base = {}
	for stat in data["stats"]:
		base[stat] = heroes[hero["name"]]["bases"][stat] + growthValMod[stat]
		growth = heroes[hero["name"]]["growths"][stat] + growthValMod[stat]
		hero[stat] = base[stat] + data["growths"][hero["rarity"]-1][growth]

	#Add merge bonuses
	mergeBoost = {"hp":0,"atk":0,"spd":0,"def":0,"res":0}

	#Order that merges happen is highest base stats, tiebreakers go hp->atk->spd->def->res
	mergeOrder = ["hp","atk","spd","def","res"]
	boostPriority = {"hp":4,"atk":3,"spd":2,"def":1,"res":0}
	
	def getBoostPriorityKey(stat):
		return base[stat] * -100 - boostPriority[stat]
	
	mergeOrder.sort(key=getBoostPriorityKey)

	mergeBoostCount = hero["merge"]*2
	for i in range(mergeBoostCount):
		mergeBoost[mergeOrder[i%5]] += 1

	if (hero["rarity"] < 5):
		#Modify base stats based on rarity
		#Order that base stats increase by rarity is similar to merge bonuses, 
		#	except HP always happens at 3* and 5*
		#Rarity base boosts don't taken into account boons/banes, so modify bases again and sort again
		base["atk"] -= growthValMod["atk"]
		base["spd"] -= growthValMod["spd"]
		base["def"] -= growthValMod["def"]
		base["res"] -= growthValMod["res"]

		rarityBaseOrder = ["atk","spd","def","res"]
		rarityBaseOrder.sort(key=getBoostPriorityKey)

		rarityBaseOrder.append("hp")
		rarityBoostCount = int(math.floor((hero["rarity"]-1) * 2.5))

		#Just going to dump these stat boosts in mergeBoost
		for i in range(rarityBoostCount):
			mergeBoost[rarityBaseOrder[i%5]] += 1

		#Subtract 2 from every stat since bases are pulled in at 5*
		for stat in data["stats"]:
			mergeBoost[stat] -= 2

	for stat in data["stats"]:
		hero[stat] += mergeBoost[stat]

	boostStatsFromSkills(hero)
			
def boostStatsFromSkills(hero):
	for slot in data["skillSlots"]:
		for stat in data["stats"]:
			hero[stat] += skills[hero[slot]][stat]
			
def getDefaultEnemyWithName(name):
	return {
			"hp":0,
			"atk":0,
			"spd":0,
			"def":0,
			"res":0,
			"weapon":"None",
			"special":"None",
			"a":"None",
			"b":"None",
			"c":"None",
			"s":"None",
			"buffs": fl["buffs"],
			"debuffs": fl["debuffs"],
			"spur": fl["spur"],
			"boon": fl["boon"],
			"bane": fl["bane"],
			"merge": fl["merge"],
			"rarity": fl["rarity"],
			"precharge": fl["precharge"],
			"damage": fl["damage"],
			"name":name
		}
	
#Sets enemy list based on include rules
def initEnemyList():
	fl = enemies["fl"]
	includes = fl["include"]
	
	if options["useCustomEnemyList"]:
		enemyFile = open(options["useCustomEnemyList"])
		enemyList = enemyFile.read().splitlines()
		if options["customEnemyListFormat"] == "Names":
			for enemyName in enemyList:
				print enemyName
				fl["list"][enemyName] = getDefaultEnemyWithName(enemyName)
		elif options["customEnemyListFormat"] == "Builds":
			alreadyHasSkills = True
			for enemy in enemyList:
				enemyDetails = enemy.split(",")
				fl["list"][enemyDetails[0]] = {
					"hp":0,
					"atk":0,
					"spd":0,
					"def":0,
					"res":0,
					"weapon":enemyDetails[10],
					"special":enemyDetails[9],
					"a":enemyDetails[5],
					"b":enemyDetails[6],
					"c":enemyDetails[7],
					"s":enemyDetails[8],
					"buffs": fl["buffs"],
					"debuffs": fl["debuffs"],
					"spur": fl["spur"],
					"boon":enemyDetails[2],
					"bane":enemyDetails[3],
					"merge":int(enemyDetails[4]),
					"rarity": fl["rarity"],
					"precharge": fl["precharge"],
					"damage": fl["damage"],
					"name":enemyDetails[1]
				}
		elif options["customEnemyListFormat"] == "Legacy":
			alreadyHasSkills = True
			#Parse a custom enemy list from the original mass duel simulator
			for line in enemyList:
				if "*" in line:
					splitData = line.split("*")
					name = splitData[0].rstrip(" (12345")
					parenSplits = splitData[0].split("(")
					rarity = parenSplits[len(parenSplits) - 1]
					index = name + str(len(fl["list"]))
					fl["list"][index] = getDefaultEnemyWithName(name)
					fl["list"][index]["rarity"] = int(rarity)
					firstLineData = splitData[1].rstrip(" ").split(" ")
					mergeValue = firstLineData[0].rstrip(")").lstrip("+")
					if len(mergeValue) > 0:
						fl["list"][index]["merge"] = int(mergeValue)
					if len(firstLineData) > 1:
						#Boon and bane are present
						fl["list"][index]["boon"] = firstLineData[1].lstrip("+")
						fl["list"][index]["bane"] = firstLineData[2].rstrip(")").lstrip("-")
				elif ":" in line:
					keyvalue = line.split(": ")
					if keyvalue[0].lower() in data["skillSlots"]:
						fl["list"][index][keyvalue[0].lower()] = keyvalue[1].rstrip(" ")
			
	else:
		for hero in heroes:
			fl["list"][hero] = getDefaultEnemyWithName(hero)
		
	for hero in fl["list"]:
		enemy = fl["list"][hero]
			
		setGeneralInfo(enemy)

		confirmed = True
		#Check color
		if (not includes[enemy["color"]]):
			confirmed = False
		#Check move type
		elif (not includes[enemy["movetype"]]):		
			confirmed = False
		#Check weapon range
		elif (not includes[enemy["range"]]):
			confirmed = False
		#Check weapon attack type
		elif (not includes[enemy["attacktype"]]):
			confirmed = False
		elif (not includes["staff"] and enemy["weapontype"] == "staff"):
			confirmed = False
		elif (not includes["nonstaff"] and enemy["weapontype"] != "staff"):
			confirmed = False
		enemy["included"] = confirmed
		
		if(confirmed):
			if not alreadyHasSkills:
				setSkills(enemy)

			#Find if skill needs replacement based on inputs
			for slot in data["skillSlots"]:
				if (enemies["fl"][slot] != "None"
						and (enemies["fl"]["replace"][slot] == 1 or enemy[slot] == "None")):
					if enemies["fl"][slot] in heroes[enemy["name"]]["possibleSkills"]:
						enemy[slot] = enemies["fl"][slot]
			
			setStats(enemy)
	
for skill in skills:
	skills[skill] = buildSkillWithDefaults(skills[skill])

#Find hero skills
for hero in heroes:
	heroes[hero]["possibleSkills"] = getValidSkillsForSlot(hero, None)
	heroes[hero]["maxSkills"] = {}
	for j in range(1,6):
		heroes[hero]["maxSkills"][j] = getMaxSkills(hero,j)
		
trackedCalls = {}

#Holder for challenger options and pre-calculated stats
challenger = {}

challenger["challenger"] = True
challenger["index"] = -1
challenger["merge"] = 0
challenger["rarity"] = 5
challenger["boon"] = "none"
challenger["bane"] = "none"

challenger["validSkills"] = {}

challenger["weapon"] = "None"
challenger["special"] = "None"
challenger["a"] = "None"
challenger["b"] = "None"
challenger["c"] = "None"
challenger["s"] = "None"

challenger["hp"] = 0
challenger["atk"] = 0
challenger["spd"] = 0
challenger["def"] = 0
challenger["res"] = 0

challenger["buffs"] = {"atk":0,"spd":0,"def":0,"res":0}
challenger["debuffs"] = {"atk":0,"spd":0,"def":0,"res":0}
challenger["spur"] = {"atk":0,"spd":0,"def":0,"res":0}

challenger["damage"] = 0
challenger["precharge"] = 0

#Holder for enemy options and pre-calculated stats
enemies = {}
#Full list
fl = {}
fl["list"] = {}

fl["include"] = {
	"melee":1,
	"ranged":1,
	"red":1,
	"blue":1,
	"green":1,
	"gray":1,
	"physical":1,
	"magical":1,
	"infantry":1,
	"cavalry":1,
	"flying":1,
	"armored":1,
	"staff":1,
	"nonstaff":1}

fl["merge"] = 0
fl["rarity"] = 5
fl["boon"] = "none"
fl["bane"] = "none"

fl["validSkills"] = getValidSkills(None)

fl["weapon"] = "None"
fl["special"] = "None"
fl["a"] = "None"
fl["b"] = "None"
fl["c"] = "None"
fl["s"] = "None"
fl["replace"] = {"weapon":0,"special":0,"a":0,"b":0,"c":0,"s":0}

fl["buffs"] = {"atk":0,"spd":0,"def":0,"res":0}
fl["debuffs"] = {"atk":0,"spd":0,"def":0,"res":0}
fl["spur"] = {"atk":0,"spd":0,"def":0,"res":0}

fl["damage"] = 0
fl["precharge"] = 0

fl["activeHeroes"] = {}
enemies["fl"] = fl

def parseOptions(optionsFile="options.txt"):
	optionsFile = open(optionsFile)
	optionList = optionsFile.read()
	optionList = optionList.splitlines()
	for option in optionList:
		opt = option.split(" = ")
		if len(opt) == 2:
			if opt[0] == "challengers":
				options["heronames"] = opt[1].split(",")
			elif opt[0] == "boon":
				challenger["boon"] = opt[1]
			elif opt[0] == "bane":
				challenger["bane"] = opt[1]
			elif opt[0] == "merge":
				challenger["merge"] = int(opt[1])
			elif opt[0] == "A":
				challenger["a"] = opt[1]
			elif opt[0] == "B":
				challenger["b"] = opt[1]
			elif opt[0] == "C":
				challenger["c"] = opt[1]
			elif opt[0] == "S":
				challenger["s"] = opt[1]
			elif opt[0] == "Special":
				challenger["special"] = opt[1]
			elif opt[0] == "Weapon":
				challenger["weapon"] = opt[1]
			elif opt[0] == "enemymerge":
				enemies["fl"]["merge"] = int(opt[1])
			elif opt[0] == "output":
				options["output"] = opt[1]
			elif opt[0] == "stats":
				options["stats"] = opt[1].split(",")
			elif opt[0] == "scenarios":
				options["scenarios"] = opt[1].split(",")
			elif opt[0] == "comparebuildsslots":
				options["comparebuildsslots"] = opt[1].split(",")
			elif opt[0] == "comparebuildsstatformat":
				options["comparebuildsstatformat"] = opt[1]
			elif opt[0] == "comparebuildstopskills":
				options["comparebuildstopskills"] = int(opt[1])
			elif opt[0] == "comparebuildsresultslimit":
				options["comparebuildsresultslimit"] = int(opt[1])
			elif opt[0] == "debug":
				options["debug"] = opt[1]
			elif opt[0] == "adjacentallies":
				options["adjacentallies"] = int(opt[1])
			elif opt[0] == "defaultA":
				enemies["fl"]["a"] = opt[1]
			elif opt[0] == "defaultB":
				enemies["fl"]["b"] = opt[1]
			elif opt[0] == "defaultC":
				enemies["fl"]["c"] = opt[1]
			elif opt[0] == "defaultS":
				enemies["fl"]["s"] = opt[1]
			elif opt[0] == "defaultSpecial":
				enemies["fl"]["special"] = opt[1]
			elif opt[0] == "defaultWeapon":
				enemies["fl"]["weapon"] = opt[1]
			elif opt[0] == "overrideA":
				enemies["fl"]["a"] = opt[1]
				enemies["fl"]["replace"]["a"] = 1
			elif opt[0] == "overrideB":
				enemies["fl"]["b"] = opt[1]
				enemies["fl"]["replace"]["b"] = 1
			elif opt[0] == "overrideC":
				enemies["fl"]["c"] = opt[1]
				enemies["fl"]["replace"]["c"] = 1
			elif opt[0] == "overrideS":
				enemies["fl"]["s"] = opt[1]
				enemies["fl"]["replace"]["s"] = 1
			elif opt[0] == "overrideSpecial":
				enemies["fl"]["special"] = opt[1]
				enemies["fl"]["replace"]["special"] = 1
			elif opt[0] == "overrideWeapon":
				enemies["fl"]["weapon"] = opt[1]
				enemies["fl"]["replace"]["weapon"] = 1
			elif opt[0] == "atkbuff":
				challenger["buffs"]["atk"] = int(opt[1])
			elif opt[0] == "spdbuff":
				challenger["buffs"]["spd"] = int(opt[1])
			elif opt[0] == "defbuff":
				challenger["buffs"]["def"] = int(opt[1])
			elif opt[0] == "resbuff":
				challenger["buffs"]["res"] = int(opt[1])
			elif opt[0] == "enemyatkbuff":
				enemies["fl"]["buffs"]["atk"] = int(opt[1])
			elif opt[0] == "enemyspdbuff":
				enemies["fl"]["buffs"]["spd"] = int(opt[1])
			elif opt[0] == "enemydefbuff":
				enemies["fl"]["buffs"]["def"] = int(opt[1])
			elif opt[0] == "enemyresbuff":
				enemies["fl"]["buffs"]["res"] = int(opt[1])
			elif opt[0] == "atkdebuff":
				challenger["debuffs"]["atk"] = int(opt[1])
			elif opt[0] == "spddebuff":
				challenger["debuffs"]["spd"] = int(opt[1])
			elif opt[0] == "defdebuff":
				challenger["debuffs"]["def"] = int(opt[1])
			elif opt[0] == "resdebuff":
				challenger["debuffs"]["res"] = int(opt[1])
			elif opt[0] == "enemyatkdebuff":
				enemies["fl"]["debuffs"]["atk"] = int(opt[1])
			elif opt[0] == "enemyspddebuff":
				enemies["fl"]["debuffs"]["spd"] = int(opt[1])
			elif opt[0] == "enemydefdebuff":
				enemies["fl"]["debuffs"]["def"] = int(opt[1])
			elif opt[0] == "enemyresdebuff":
				enemies["fl"]["debuffs"]["res"] = int(opt[1])
			elif opt[0] == "atkspur":
				challenger["spur"]["atk"] = int(opt[1])
			elif opt[0] == "spdspur":
				challenger["spur"]["spd"] = int(opt[1])
			elif opt[0] == "defspur":
				challenger["spur"]["def"] = int(opt[1])
			elif opt[0] == "resspur":
				challenger["spur"]["res"] = int(opt[1])
			elif opt[0] == "enemyatkspur":
				enemies["fl"]["spur"]["atk"] = int(opt[1])
			elif opt[0] == "enemyspdspur":
				enemies["fl"]["spur"]["spd"] = int(opt[1])
			elif opt[0] == "enemydefspur":
				enemies["fl"]["spur"]["def"] = int(opt[1])
			elif opt[0] == "enemyresspur":
				enemies["fl"]["spur"]["res"] = int(opt[1])
			elif opt[0] == "rarity":
				challenger["rarity"] = int(opt[1])
			elif opt[0] == "enemyrarity":
				enemies["fl"]["rarity"] = int(opt[1])
			elif opt[0] == "damage":
				challenger["damage"] = int(opt[1])
			elif opt[0] == "enemydamage":
				enemies["fl"]["damage"] = int(opt[1])
			elif opt[0] == "precharge":
				challenger["precharge"] = int(opt[1])
			elif opt[0] == "enemyprecharge":
				enemies["fl"]["precharge"] = int(opt[1])
			elif opt[0] in enemies["fl"]["include"]:
				if opt[1] == "exclude":
					enemies["fl"]["include"][opt[0]] = 0
			elif opt[0] == "threatenrule":
				options["threatenRule"] = opt[1]
			elif opt[0] == "ployangle":
				options["ployBehavior"] = opt[1]
			elif opt[0] == "usegaleforce":
				if opt[1] == "True":
					options["useGaleforce"] = True
				else:
					options["useGaleforce"] = False
			elif opt[0] == "usecustomenemylist":
				options["useCustomEnemyList"] = opt[1]
			elif opt[0] == "customenemylistformat":
				options["customEnemyListFormat"] = opt[1]
			elif opt[0] == "exportbuilds":
				options["exportbuilds"] = int(opt[1])
			