from __future__ import division
from __future__ import print_function
import data
import math
import time

# Initial logic and code by github.com/Andu2
# Python conversion and github.com/Meteorchestra

class ActiveHero(object):

	def __init__(self, hero):
		self.combatBuffs = {"atk":0,"spd":0,"def":0,"res":0}
		self.combatDebuffs = {"atk":0,"spd":0,"def":0,"res":0}
		self.combatSpur = {"atk":0,"spd":0,"def":0,"res":0}

		self.skillNames = []
		
		self.verbose = (data.options["output"] == "Verbose")

		self.challenger = "challenger" in hero
		self.name = hero["name"]
		self.rarity = hero["rarity"]
		self.merge = hero["merge"]

		self.weapon = hero["weapon"]	
		self.special = hero["special"]
		
		self.skillNames = [self.weapon, self.special, hero["a"], hero["b"], hero["c"], hero["s"]]

		self.boon = hero["boon"]
		self.bane = hero["bane"]
		self.damage = hero["damage"]
		self.maxHp = hero["hp"]

		self.buffs = hero["buffs"]
		self.debuffs = hero["debuffs"]
		self.spur = hero["spur"]
		
		self.stats = {"atk":hero["atk"], 
				"spd":hero["spd"], 
				"def":hero["def"], 
				"res":hero["res"], 
				"hp":max(self.maxHp - hero["damage"], 1)}

		self.moveType = hero["movetype"]
		self.weaponType = hero["weapontype"]
		self.color = hero["color"]

		self.precharge = hero["precharge"]

		#Categorize weapon
		self.range = data.getAttackDistanceFromWeapon(self.weaponType)
		self.attackType = data.getAttackTypeFromWeapon(self.weaponType)

		self.charge = 0
		self.initiator = False
		self.panicked = False
		self.lit = False
		self.didAttack = False
		self.overkill = 0
		self.skillAttributes = {}
			
		#Create a map of attributes for each skill this unit has
		for skill in self.skillNames:
			for attribute in data.skills[skill]:
				if attribute not in self.skillAttributes:
					self.skillAttributes[attribute] = {}
				self.skillAttributes[attribute][skill] = data.skills[skill][attribute]
		
		#Adjust the current values for skills that trigger after a certain number of
		#	turns based on the startTurn option
		if "turnstotrigger" in self.skillAttributes:
			for skill in self.skillAttributes["turnstotrigger"]:
				self.skillAttributes["turnstotrigger"][skill] -= data.options["startTurn"]
				
		#Update precharge with skills that give precharge
		for skill in self.getActiveSkillsWithAttribute("precharge"):
			self.precharge += self.skillAttributes["precharge"][skill]
		
		#Set charge at beginning
		self.resetCharge()
		self.charge += self.precharge
			
	#Reset an ActiveHero for another battle without a full reinitialization
	def reset(self):
		self.combatBuffs = {"atk":0,"spd":0,"def":0,"res":0}
		self.combatDebuffs = {"atk":0,"spd":0,"def":0,"res":0}
		self.stats["hp"] = max(self.maxHp - self.damage, 1)
		self.charge = 0
		self.initiator = False
		self.panicked = False
		self.lit = False
		self.didAttack = False
		self.overkill = 0
		
		#Set charge at beginning
		self.resetCharge()
		self.charge += self.precharge
		
		#Reset the current values for skills that trigger after a certain number of
		#	turns based on the startTurn option
		if "turnstotrigger" in self.skillAttributes:
			for skill in self.skillAttributes["turnstotrigger"]:
				self.skillAttributes["turnstotrigger"][skill] = (data.skills[skill]["turnstotrigger"]
						- data.options["startTurn"])

	def resetCharge(self):
		self.charge = data.skills[self.weapon]["charge"]
		
	def hasWeaponAdvantage(self, enemy):
		if ((self.color == "red" and enemy.color == "green") or
				(self.color == "green" and enemy.color == "blue") or
				(self.color == "blue" and enemy.color == "red")):
			return True
		for skill in self.getSkillsWithAttribute("advantage"):
			if self.skillAttributes["advantage"][skill] == enemy.color:
				return True
		return False
				
	def getNonlethalDamage(self, damage):
		if (self.stats["hp"] - damage < 1):
			return self.stats["hp"] - 1
		else:
			return damage
			
	def getMaximumHealAmount(self, heal):
		if (self.stats["hp"] + heal > self.maxHp):
			return self.maxHp - self.stats["hp"]
		else:
			return heal
		
	def getActiveSkillsWithAttribute(self, attribute, enemy=None):
		if attribute in self.skillAttributes:
			return (skill for skill in self.skillAttributes[attribute].keys()
					if checkCondition(self, skill, enemy, attribute))
		return []
		
	def getSkillsWithAttribute(self, attribute):
		if attribute in self.skillAttributes:
			return self.skillAttributes[attribute].keys()
		return []
		
	def checkHardiness(self, enemy):
		return any(self.getActiveSkillsWithAttribute("hardy")) or any(enemy.getSkillsWithAttribute("hardy"))

	def threaten(self, enemy):
		threatenText = ""
		threatDebuffs = {"atk":0,"spd":0,"def":0,"res":0}
		skillNames = []
		#Don't trigger ploys if the enemy is ranged and the ploy behavior option is set to diagonal
		if (enemy.range == "melee" or data.options["ployBehavior"] != "Diagonal"):
			for skill in self.getActiveSkillsWithAttribute("ploy", enemy):
				for stat in self.skillAttributes["ploy"][skill]:
					if stat in threatDebuffs:
						if self.skillAttributes["ploy"][skill][stat] < enemy.combatDebuffs[stat]:
							enemy.combatDebuffs[stat] = self.skillAttributes["ploy"][skill][stat]
							threatenText += self.generateDebuffText(stat, enemy.combatDebuffs[stat], skill, enemy)
					elif stat == "panic":
						enemy.panicked = True
						if self.verbose:
							threatenText += (self.name + " activates " + skill + ", inflicting panic on "
									+ enemy.name + ".\n")
		
		#All threaten skills are currently unconditional and affect stats only
		for skill in self.getSkillsWithAttribute("threaten"):
			for stat in self.skillAttributes["threaten"][skill]:
				if self.skillAttributes["threaten"][skill][stat] < enemy.combatDebuffs[stat]:
					enemy.combatDebuffs[stat] = self.skillAttributes["threaten"][skill][stat]
					threatenText += self.generateDebuffText(stat, enemy.combatDebuffs[stat], skill, enemy)

		return threatenText
		
	# Checks for skills that trigger based on a certain number of unit turns
	# (Currently, only Renewal variants work this way)
	def checkTurnTriggers(self):
		turnTriggersText = ""
		for skill in self.getSkillsWithAttribute("turnstotrigger"):
			self.skillAttributes["turnstotrigger"][skill] -= 1
			if self.skillAttributes["turnstotrigger"][skill] <= 0:
				triggerEffect = self.skillAttributes["triggereffect"][skill]
				if triggerEffect["type"] == "renew":
					renewalHp = self.getMaximumHealAmount(triggerEffect["value"])
					self.stats["hp"] += renewalHp
					if self.verbose:
						turnTriggersText += self.name + " heals " + str(renewalHp) + " HP with " + skill + ".\n"
				self.skillAttributes["turnstotrigger"][skill] = data.skills[skill]["turnstotrigger"]
		return turnTriggersText
		
	#Helper to generate text from a debuff effect
	def generateDebuffText(self, stat, debuff, skill, enemy):
		if self.verbose:
			return (self.name + " activates " + skill + ", giving " + enemy.name + " " +
					str(debuff) + " " + stat + ".\n")
		else:
			return ""
		
	#Helper to generate text from a buff effect
	def generateBuffText(self, stat, buff, skill):
		if self.verbose:
			return self.name + " gets a buff of +" + str(buff) + " " + stat + " from " + skill + ".\n"
		else:
			return ""
	
	#For buffs at the start of the turn
	def defiant(self):
		defiantText = ""
		
		for skill in self.getActiveSkillsWithAttribute("buff"):
			for stat in self.skillAttributes["buff"][skill]:
				if self.skillAttributes["buff"][skill][stat] > self.combatBuffs[stat]:
					self.combatBuffs[stat] = self.skillAttributes["buff"][skill][stat]
					defiantText += self.generateBuffText(stat, self.combatBuffs[stat], skill)

		return defiantText
		
	#For buffs that act like spur and stack
	def startCombatSpur(self, enemy):
		boostText = ""
		
		for skill in self.getActiveSkillsWithAttribute("spur", enemy):
			spurData = self.skillAttributes["spur"][skill]
			for stat in spurData:
				self.combatSpur[stat] += spurData[stat]
				if self.verbose and spurData[stat] > 0:
					boostText += (self.name + " gets +" + str(spurData[stat]) + " " + stat
							+ " from " + skill + ".\n")

		return boostText
		
	#Helper for poison, pain, and fury, which do basically the same thing
	def applyPostcombatDamage(self, attribute, enemy):
		postcombatDamageText = ""
		
		for skill in self.getActiveSkillsWithAttribute(attribute):
			damage = enemy.getNonlethalDamage(self.skillAttributes[attribute][skill])
			enemy.stats["hp"] -= damage
			if self.verbose:
				postcombatDamageText += (enemy.name + " takes " + str(damage) + " damage after combat from "
						+ skill + ".\n")
		
		return postcombatDamageText
		
	#For post-combat debuffs and other effects (panic/candlelight)
	def seal(self, enemy):
		sealText = ""
		
		for skill in self.getActiveSkillsWithAttribute("seal", enemy):
			for stat in self.skillAttributes["seal"][skill]:
				if (stat in enemy.combatDebuffs
						and self.skillAttributes["seal"][skill][stat] < enemy.combatDebuffs[stat]):
					enemy.combatDebuffs[stat] = self.skillAttributes["seal"][skill][stat]
					if self.verbose:
						sealText += (self.name + " lowers " + enemy.name + "'s " + stat + " by "
								+ str(-enemy.combatDebuffs[stat]) + " after combat with " + skill + ".\n")
				elif stat == "panic":
					enemy.panicked = True
					if self.verbose:
						sealText += self.name + " panics " + enemy.name + ".\n"
				elif stat == "blind":
					enemy.lit = True
					if self.verbose:
						sealText += (self.name + " inflicts " + enemy.name
								+ " with an inability to make counterattacks.\n")

		return sealText

	#For post-combat buff effects
	def postCombatBuff(self):
		postCombatBuffText = ""
		
		for skill in self.getActiveSkillsWithAttribute("postbuff"):
			for stat in self.skillAttributes["postbuff"][skill]:
				if self.skillAttributes["postbuff"][skill][stat] > self.combatBuffs[stat]:
					self.combatBuffs[stat] = self.skillAttributes["postbuff"][skill][stat]
					postCombatBuffText += self.generateBuffText(stat, self.combatBuffs[stat], skill)

		return postCombatBuffText

	#For post-combat healing effects
	def postCombatHeal(self):
		postCombatHealText = ""
		
		#Currently, all skills that heal after combat only activate if the unit initiated
		if self.initiator:
			for skill in self.getSkillsWithAttribute("postheal"):
				healAmount = self.getMaximumHealAmount(self.skillAttributes["postheal"][skill])
				if healAmount > 0:
					self.stats["hp"] += healAmount
					if self.verbose:
						postCombatHealText += (self.name + " heals " + str(healAmount) + " hp with "
								+ skill + ".\n")

		return postCombatHealText
		
	#Get stat modifications for a particular stat
	def getStatMods(self, stat):
		if self.panicked:
			return (0 - max(self.buffs[stat],self.combatBuffs[stat]) 
					+ min(self.debuffs[stat],self.combatDebuffs[stat])
					+ self.spur[stat] + self.combatSpur[stat])
		else:
			return (max(self.buffs[stat],self.combatBuffs[stat]) 
					+ min(self.debuffs[stat],self.combatDebuffs[stat]) 
					+ self.spur[stat] + self.combatSpur[stat])
			

	#Represents one attack of combat
	def doDamage(self, enemy, range, brave=False, AOE=False):
		#Record whether a unit actually attacked for checking daggers and pain
		self.didAttack = True

		enemyDefModifier = 0
		effectiveBonus = 1.0
		dmgMultiplier = 1.0
		dmgBoost = 0
		absorbPct = 0

		damageText = ""
		selfEffectiveStats = {}
		enemyEffectiveStats = {}
		for stat in ["atk", "def", "res"]:
			selfEffectiveStats[stat] = self.stats[stat] + self.getStatMods(stat)
			enemyEffectiveStats[stat] = enemy.stats[stat] + enemy.getStatMods(stat)

		if (self.attackType == "magical"):
			relevantDef = enemyEffectiveStats["res"]
		else:
			relevantDef = enemyEffectiveStats["def"]

		#Blade tomes add atk
		if "blade" in self.skillAttributes:
			for stat in self.combatBuffs:
				selfEffectiveStats["atk"] += max(self.buffs[stat], self.combatBuffs[stat])

		offensiveSpecialActivated = False

		if "special" in self.skillAttributes and self.skillAttributes["charge"][self.special] <= self.charge:
			offensiveSpecialActivated = False
			#Special will fire if it's an attacking special
			effect = self.skillAttributes["special"][self.special]
			if effect["type"] == "offense":
				offensiveSpecialActivated = True
				if effect["effect"] == "multiplier":
					dmgMultiplier = effect["value"]
				elif effect["effect"] == "boostbystat":
					dmgBoost += selfEffectiveStats[effect["stat"]] * effect["value"]
				elif effect["effect"] == "absorb" or effect["effect"] == "aether":
					absorbPct = effect["value"]
				elif effect["effect"] == "pierce" or effect["effect"] == "aether":
					enemyDefModifier = -effect["value"]
				elif effect["effect"] == "vengeance":
					dmgBoost += (self.maxHp - self.stats["hp"]) * effect["value"]

			if (offensiveSpecialActivated):
				self.resetCharge()
				if self.verbose:
					damageText += self.name + " activates " + self.special + ".\n"
			
			if (offensiveSpecialActivated or AOE):
				for skill in self.getSkillsWithAttribute("specialboost"):
					dmgBoost += self.skillAttributes["specialboost"][skill]
					if self.verbose:
						damageText += (self.name + " gains " + str(self.skillAttributes["specialboost"][skill])
									+ " damage from " + skill + ".\n")

			#Do AOE specials
			if (AOE):
				
				#AOE specials don't take spur into effect
				AOEEffectiveAtk = selfEffectiveStats["atk"] - self.spur["atk"] - self.combatSpur["atk"]
				
				multiplier = self.skillAttributes["special"][self.special]["multiplier"]
				AOEDamage = max(enemy.getNonlethalDamage(dmgBoost
						+ math.floor(multiplier * (AOEEffectiveAtk - relevantDef))), 0)
				self.resetCharge()
				enemy.stats["hp"] -= AOEDamage
				if self.verbose:
					damageText += ("Before combat, " + self.name + " hits with " + self.special
							+ " for " + str(AOEDamage) + ".\n")
				
					
		#Don't do anything else if it's just an AOE attack
		if (not AOE):
		
			#Check weapon advantage
			#0 is no advantage, 1 is attacker advantage, -1 is defender advantage
			weaponAdvantage = 0

			if self.hasWeaponAdvantage(enemy):
				weaponAdvantage = 1
			elif enemy.hasWeaponAdvantage(self):
				weaponAdvantage = -1

			#Extra weapon advantage is apparently limited to 0.2 more (doesn't stack)
			extraWeaponAdvantage = 0
			if weaponAdvantage != 0:
				if "negateselfaffinity" not in self.skillAttributes:
					for skill in self.getSkillsWithAttribute("trianglebonus"):
						extraWeaponAdvantage += self.skillAttributes["trianglebonus"][skill]
				if "negateselfaffinity" not in enemy.skillAttributes:
					for skill in enemy.getSkillsWithAttribute("trianglebonus"):
						extraWeaponAdvantage += enemy.skillAttributes["trianglebonus"][skill]
				extraWeaponAdvantage = min(extraWeaponAdvantage, .2)
				
			#Handle Cancel Affinity
			if extraWeaponAdvantage > 0:
				if weaponAdvantage == 1:
					if ("negateenemyaffinity" in enemy.skillAttributes
							or "negateenemydisaffinity" in self.skillAttributes):
						extraWeaponAdvantage = 0
					elif "reverseenemyaffinity" in enemy.skillAttributes:
						extraWeaponAdvantage = -extraWeaponAdvantage
				elif weaponAdvantage == -1:
					if ("negateenemydisaffinity" in enemy.skillAttributes
							or "negateenemyaffinity" in self.skillAttributes):
						extraWeaponAdvantage = 0
					elif "reverseenemyaffinity" in self.skillAttributes:
						extraWeaponAdvantage = -extraWeaponAdvantage

			weaponAdvantageBonus = (0.2 + extraWeaponAdvantage) * weaponAdvantage
			
			if self.verbose and (weaponAdvantage != 0):
				damageText += (self.name + "'s attack is multiplied by "
						+ str(round(1 + weaponAdvantageBonus, 2)) + " because of weapon advantage.\n")

			#Check weapon effective against
			effectiveBonus = 1
			if "shield" not in enemy.skillAttributes:
				for skill in self.getSkillsWithAttribute("effective"):
					if (self.skillAttributes["effective"][skill] == enemy.moveType
							or self.skillAttributes["effective"][skill] == enemy.weaponType):
						effectiveBonus = 1.5

				if self.verbose and (effectiveBonus > 1):
					damageText += (self.name + "'s attack is multiplied by "
							+ str(effectiveBonus) + " from weapon effectiveness.\n")

			#Check damage reducing specials
			defensiveSpecialActivated = False
			dmgReduction = 0
			miracle = False
			if enemy.skillAttributes["charge"][enemy.special] <= enemy.charge:
			
				if "special" in enemy.skillAttributes:
					effect = enemy.skillAttributes["special"][enemy.special]
					if effect["type"] == "defense" and effect["range"] == range:
						defensiveSpecialActivated = True
						#All current defensive specials are damage reduction
						dmgReduction = effect["value"]
						
						for skill in enemy.getSkillsWithAttribute("specialshield"):
							dmgBoost -= enemy.skillAttributes["specialshield"][skill]
							if self.verbose:
								damageText += (enemy.name + " blocks "
										+ str(enemy.skillAttributes["specialshield"][skill]) 
										+ " damage with " + skill + ".\n")

				if "miracle" in enemy.skillAttributes and enemy.stats["hp"] > 1:
					miracle = True

			if defensiveSpecialActivated:
				if self.verbose and (dmgReduction < 1):
					damageText += (enemy.name + " multiplies damage by " + str(1-dmgReduction)
							+ " with " + enemy.special + ".\n")
				enemy.resetCharge()

			#Weapon mod for healers
			if (self.weaponType == "staff"):
				weaponModifier = 0.5
			else:
				weaponModifier = 1
				
			#This is currently just Wrathful Staff
			for skill in self.getActiveSkillsWithAttribute("wrath"):
				weaponModifier = max(weaponModifier, self.skillAttributes["wrath"][skill])
				
			#This is currently just Absorb
			for skill in self.getSkillsWithAttribute("absorb"):
				absorbPct += self.skillAttributes["absorb"][skill]

			#Damage calculation from http://feheroes.wiki/Damage_Calculation
			#Doing calculation in steps to see the formula more clearly
			rawDmg = (math.trunc(selfEffectiveStats["atk"] * effectiveBonus)
					+ math.trunc(math.trunc(selfEffectiveStats["atk"] * effectiveBonus) * weaponAdvantageBonus)
					+ math.trunc(dmgBoost))
			reduceDmg = relevantDef + math.trunc(relevantDef * enemyDefModifier)
			dmg = math.trunc((rawDmg - reduceDmg) * weaponModifier)
			dmg = math.trunc(dmg * dmgMultiplier) - math.trunc(dmg * dmgReduction)
			dmg = max(dmg, 0)
			if self.verbose:
				damageText += self.name + " attacks " + enemy.name + " for " + str(dmg) + " damage.\n"
			if (dmg >= enemy.stats["hp"]):
				if (miracle):
					dmg = enemy.stats["hp"] - 1
					defensiveSpecialActivated = True
					enemy.resetCharge()
					if self.verbose:
						damageText += enemy.name + " survives with 1HP with Miracle.\n"
				else:
					enemy.overkill = dmg - enemy.stats["hp"]
					dmg = min(dmg,enemy.stats["hp"])
			enemy.stats["hp"] -= dmg

			#Add absorbed hp
			absorbHp = self.getMaximumHealAmount(math.trunc(dmg * absorbPct))
			self.stats["hp"] += absorbHp
			if self.verbose and (absorbHp > 0):
				damageText += self.name + " absorbs " + str(absorbHp) + ".\n"

			#Special charge does not increase if special was used on self attack
			if (not offensiveSpecialActivated):
				
				heavy = 0
				for skill in self.getSkillsWithAttribute("heavy"):
					effect = self.skillAttributes["heavy"][skill]
					
					#This condition has to be local because it uses the combat-specific effective stats
					if (selfEffectiveStats[effect["stat"]] - enemyEffectiveStats[effect["stat"]] 
							>= effect["margin"]):
						heavy = max(heavy, effect["value"])

				guard = 0
				for skill in enemy.getActiveSkillsWithAttribute("guard"):
					guard = max(guard, enemy.skillAttributes["guard"][skill])

				self.charge = self.charge + 1 + heavy - guard

			if (not defensiveSpecialActivated):
				
				guard = 0
				for skill in self.getActiveSkillsWithAttribute("guard"):
					guard = max(guard, self.skillAttributes["guard"][skill])

				enemy.charge = enemy.charge + 1 - guard

			#Show hp
			#Make sure challenger is first
			if self.verbose:
				if (self.challenger):
					damageText += (self.name + " " + str(self.stats["hp"]) + " : "
							+ enemy.name + " " + str(enemy.stats["hp"]) + "\n")
				else:
					damageText += (enemy.name + " " + str(enemy.stats["hp"]) + " : "
							+ self.name + " " + str(self.stats["hp"]) + "\n")
		
			#Do damage again if brave weapon
			if (brave and enemy.stats["hp"] > 0):
				if self.verbose:
					damageText += self.name + " attacks again with a brave weapon.\n"
				damageText += self.doDamage(enemy, self.range)

		return damageText

	#Represents a full round of combat
	def attack(self, enemy, turn, galeforce=False):

		#Text is returned by helper functions, so the results from each function are added to roundText
		roundText = ""
		firstTurn = (turn == data.options["startTurn"])
		self.initiator = True
		enemy.initiator = False
		enemy.didAttack = False

		#Remove certain buffs
		self.combatBuffs = {"atk":0,"spd":0,"def":0,"res":0}

		#Only do turn-start effects if it's the first move of a turn
		if (not galeforce):
			#Check self buffs (defiant skills)
			roundText += self.defiant()

			#Check turn for renewal
			#Per wiki, renewal triggers after defiant - http://feheroes.gamepedia.com/Skill_Interaction
			roundText += self.checkTurnTriggers()

			#Check threaten if not first turn or if a first-turn threaten option is set
			if (firstTurn and (data.options["threatenRule"] == "Both"
					or data.options["threatenRule"] == "Attacker")):
				roundText += enemy.threaten(self)
			if ((not firstTurn) or data.options["threatenRule"] == "Both"
					or data.options["threatenRule"] == "Defender"):
				roundText += self.threaten(enemy)

		#Set after renewal
		self.combatStartHp = self.stats["hp"]
		enemy.combatStartHp = enemy.stats["hp"]

		#Check combat effects
		self.combatSpur = {"atk":0,"spd":0,"def":0,"res":0}
		enemy.combatSpur = {"atk":0,"spd":0,"def":0,"res":0}

		roundText += self.startCombatSpur(enemy)
		roundText += enemy.startCombatSpur(self)

		#Adjust speeds
		selfEffSpd = self.stats["spd"] + self.getStatMods("spd")
		enemyEffSpd = enemy.stats["spd"] + enemy.getStatMods("spd")

		#Check for any-distance counterattack
		anyRangeCounter = ("anyrangecounter" in enemy.skillAttributes)
		
		#Check for AOE specials
		if "special" in self.skillAttributes and self.skillAttributes["special"][self.special]["type"] == "AOE":
			roundText += self.doDamage(enemy, self.range, False, True)

		vantage = any(enemy.getActiveSkillsWithAttribute("vantage")) and not self.checkHardiness(enemy)
		desperation = any(self.getActiveSkillsWithAttribute("desperation")) and not enemy.checkHardiness(self)
		
		enemyCanCounter = ((self.range == enemy.range or anyRangeCounter) and not 
				(any(self.getActiveSkillsWithAttribute("noenemycounter", enemy)) 
				or any(enemy.getActiveSkillsWithAttribute("noselfcounter", self)) or enemy.lit))
		
		selfAutoFollow = (any(self.getActiveSkillsWithAttribute("autofollow", enemy))
			or (enemyCanCounter and any(self.getActiveSkillsWithAttribute("brash"))))
		
		enemyAutoFollow = any(enemy.getActiveSkillsWithAttribute("autofollow", self))
		
		selfPreventFollow = (any(self.getActiveSkillsWithAttribute("noselffollow", enemy))
				or any(enemy.getActiveSkillsWithAttribute("noenemyfollow", self)))
		
		enemyPreventFollow = (any(self.getActiveSkillsWithAttribute("noenemyfollow", enemy))
				or any(enemy.getActiveSkillsWithAttribute("noselffollow", self)))

		#check for brave
		#brave will be passed to self.doDamage
		brave = "brave" in self.skillAttributes

		#Cancel things out
		if (selfPreventFollow and selfAutoFollow):
			selfPreventFollow = False
			selfAutoFollow = False
			if self.verbose:
				roundText += self.name + " is affected by conflicting follow-up skills, which cancel out.\n"
		
		if self.verbose:
			if (selfAutoFollow):
				roundText += self.name + " can make an automatic follow-up attack.\n"
			if (selfPreventFollow):
				roundText += self.name + " is prevented from making a follow-up attack.\n"
		
		if (enemyCanCounter):
			#Don't show self text if the enemy can't counter anyway
			if (enemyPreventFollow and enemyAutoFollow):
				enemyPreventFollow = False
				enemyAutoFollow = False
				if self.verbose:
					roundText += enemy.name + " is affected by conflicting follow-up skills, which cancel out.\n"
			if self.verbose:
				if (enemyAutoFollow):
					roundText += enemy.name + " can make an automatic follow-up attack.\n"
				if (enemyPreventFollow):
					roundText += enemy.name + " is prevented from making a follow-up attack.\n"

		selfFollowUp = ((selfEffSpd - enemyEffSpd >= 5) or selfAutoFollow) and (not selfPreventFollow)
		enemyFollowUp = ((enemyEffSpd - selfEffSpd >= 5) or enemyAutoFollow) and (not enemyPreventFollow)

		#Enemy's vantage counter-attack
		if (vantage and enemyCanCounter):
			if self.verbose:
				roundText += enemy.name + " counterattacks first with vantage.\n"
			roundText += enemy.doDamage(self, self.range)

		#Hero's initial attack (if not dead from vantage)
		if (self.stats["hp"] > 0):
			roundText += self.doDamage(enemy, self.range, brave)

		#Hero's desperation follow-up
		if desperation and self.stats["hp"] > 0 and enemy.stats["hp"] > 0 and selfFollowUp:
			if self.verbose:
				roundText += self.name + " attacks again immediately with desperation.\n"
			roundText += self.doDamage(enemy, self.range, brave)

		#Enemy attacks, either vantage follow-up or first attack
		if (enemyCanCounter and enemy.stats["hp"] > 0 and self.stats["hp"] > 0 
				and ((not vantage) or enemyFollowUp)):
			roundText += enemy.doDamage(self, self.range)
			
		#Hero's follow-up (unless it has already happened from desperation)
		if selfFollowUp and self.stats["hp"] > 0 and enemy.stats["hp"] > 0 and (not desperation):
			roundText += self.doDamage(enemy, self.range, brave)

		#Enemy's non-vantage follow-up
		if enemyCanCounter and enemyFollowUp and self.stats["hp"] > 0 and enemy.stats["hp"] > 0 and (not vantage):
			roundText += enemy.doDamage(self, self.range)

		#Do post-combat damage to enemy if enemy isn't dead	
		if (enemy.stats["hp"] > 0):
			roundText += self.applyPostcombatDamage("poison", enemy)
			roundText += enemy.applyPostcombatDamage("fury", enemy)
			if self.didAttack:
				roundText += self.applyPostcombatDamage("pain", enemy)

		#Do post-combat damage to self if self isn't dead
		#No poison because self initiated
		if (self.stats["hp"] > 0):
			roundText += self.applyPostcombatDamage("fury", self)
			if enemy.didAttack:
				roundText += enemy.applyPostcombatDamage("pain", self)

		#Remove old debuffs and combat debuffs
		self.combatDebuffs = {"atk":0,"spd":0,"def":0,"res":0}
		self.panicked = False
		self.lit = False

		#Do stuff if both aren't dead
		if (self.stats["hp"] > 0 and enemy.stats["hp"] > 0):
			#Apply post-combat debuffs (seal)
			roundText += self.seal(enemy)
			roundText += enemy.seal(self)

			#Post-combat buffs
			roundText += self.postCombatBuff()
			roundText += enemy.postCombatBuff()
			roundText += self.postCombatHeal()

			#Finally, Galeforce!
			if ("galeforce" in self.skillAttributes and data.options["useGaleforce"]
					and self.skillAttributes["charge"][self.special] <= self.charge and not galeforce):
				if self.verbose:
					roundText += self.name + " initiates again with Galeforce!\n"
				self.resetCharge()
				roundText += self.attack(enemy,turn,True)

		return roundText
		
def checkNone(self, enemy, condition, attribute):
	return True
	
def checkHpMax(self, enemy, condition, attribute):
	return self.stats["hp"] / self.maxHp <= condition["value"]
	
def checkHpMin(self, enemy, condition, attribute):
	return self.stats["hp"] / self.maxHp >= condition["value"]
	
def checkHpStartMin(self, enemy, condition, attribute):
	return self.combatStartHp / self.maxHp >= condition["value"]
	
def checkBreaker(self, enemy, condition, attribute):
	return enemy.weaponType == condition["weapon"] and checkHpMin(self, enemy, condition, attribute)

def checkStatComp(self, enemy, condition, attribute):
	phantom = 0
	for skill in self.getSkillsWithAttribute("phantom"):
		if condition["stat"] in self.skillAttributes["phantom"][skill]:
			phantom += self.skillAttributes["phantom"][skill][condition["stat"]]
	return self.stats[condition["stat"]] + phantom - condition["margin"] >= enemy.stats[condition["stat"]]
	
def checkSweep(self, enemy, condition, attribute):
	return ((attribute == "noselffollow" and self.initiator) 
			or (attribute == "noenemycounter" and enemy.attackType == condition["attacktype"] 
					and checkStatComp(self, enemy, condition, attribute)))
	
def checkDidAttack(self, enemy, condition, attribute):
	return self.didAttack
	
def checkInit(self, enemy, condition, attribute):
	return self.initiator
	
def checkDef(self, enemy, condition, attribute):
	return not self.initiator
	
def checkDefWithHpMin(self, enemy, condition, attribute):
	return checkDef(self, enemy, condition, attribute) and checkHpMin(self, enemy, condition, attribute)

def checkRangedDef(self, enemy, condition, attribute):
	return ((not self.initiator) and enemy.range == "ranged")

def checkMeleeDef(self, enemy, condition, attribute):
	return ((not self.initiator) and enemy.range == "melee")

def checkEcho(self, enemy, condition, attribute):
	return (self.didAttack or attribute == "spur") and (self.combatStartHp >= self.maxHp or attribute == "seal")

def checkChivalry(self, enemy, condition, attribute):
	return enemy.combatStartHp / enemy.maxHp >= condition["value"]
	
def checkAdjacency(self, enemy, condition, attribute):
	#Handled in skill setup
	return True
	
def checkAttackedClass(self, enemy, condition, attribute):
	return self.didAttack and enemy.moveType == condition["value"]

def checkDefensiveSpecial(self, enemy, condition, attribute):
	return "special" in self.skillAttributes and self.skillAttributes["special"][self.special]["type"] == "defense"
	
#Map of functions to avoid a big ugly conditional
#See skills.py for a more complete description of skill conditions
conditionCheckFunctions = {
	None: checkNone,
	"hpmax": checkHpMax,
	"hpmin": checkHpMin,
	"hpstartmin": checkHpStartMin,
	"statcomp": checkStatComp,
	"init": checkInit,
	"def": checkDef,
	"rangeddef": checkRangedDef,
	"meleedef": checkMeleeDef,
	"echo": checkEcho,
	"chivalry": checkChivalry,
	"adjacency": checkAdjacency,
	"didattack": checkDidAttack,
	"attackedclass": checkAttackedClass,
	"breaker": checkBreaker,
	"riposte": checkDefWithHpMin,
	"sweep": checkSweep,
	"defensivespecial": checkDefensiveSpecial,
}

def checkCondition(self, skill, enemy=None, attribute=None):
		condition = self.skillAttributes["condition"][skill]
		return conditionCheckFunctions[condition["type"]](self, enemy, condition, attribute)

#Enacts a complete battle between the challenger and the named enemy
#Returns object with: rounds, fightText, resultText, enemy, challenger, and outcome
def fight(enemyName):
	
	fightText = ""

	#Find the challenger and enemy and prepare them for battle
	ahChallenger = data.challenger["activeHero"]
	ahChallenger.reset()

	ahEnemy = data.enemies["fl"]["activeHeroes"][enemyName]
	ahEnemy.reset()

	rounds = 0

	#For each round, have the proper unit initiate an attack
	for round in range(len(data.options["roundInitiators"])):
		turn = data.options["startTurn"] + round
		fightText += "-- Round " + str(round + 1) + ": "
		if (data.options["roundInitiators"][round] == "C"):
			fightText += ahChallenger.name + " initiates --\n"
			fightText += ahChallenger.attack(ahEnemy, turn)
		else:
			fightText += ahEnemy.name + " initiates --\n"
			fightText += ahEnemy.attack(ahChallenger, turn)
		#If someone is dead, record how many rounds it took and break
		if (ahEnemy.stats["hp"] <= 0 or ahChallenger.stats["hp"] <= 0):
			rounds = round + 1
			break

	#Determine the winner (if one exists)
	resultText = ""
	if (ahChallenger.stats["hp"] <= 0):
		outcome = "loss"
		resultText += "LOSS, " + str(rounds)
	elif (ahEnemy.stats["hp"] <= 0):
		outcome = "win"
		resultText += "WIN, " + str(rounds)
	else:
		outcome = "inconclusive"
		resultText += "Inconclusive"

	#Add in some extra info to the result text if it's going to be displayed
	if (outcome != "inconclusive") and data.options["output"] != "CompareBuilds":
		if (rounds == 1):
			resultText += " round"
		else:
			resultText += " rounds"
		if (ahEnemy.overkill):
			resultText += ", " + str(ahEnemy.overkill) + " overkill"
		elif (ahChallenger.overkill):
			resultText += ", " + str(ahChallenger.overkill) + " overkill"

	return {
		"rounds":rounds,
		"resultText":resultText,
		"fightText":fightText,
		"enemy":ahEnemy,
		"challenger":ahChallenger,
		"outcome":outcome}
		
def sortByName(fightResult):
	return fightResult["enemy"].name

#Calculate results from duels with each enemy
def calculate():

	wins = 0
	losses = 0
	inconclusive = 0

	fightResults = []

	enemyList = data.enemies["fl"]["list"]
	
	for enemy in enemyList:
		if enemyList[enemy]["included"]:
			fightResults.append(fight(enemy))
	
	#Clean up output if each result is being displayed
	if data.options["output"] == "Verbose" or data.options["output"] == "Summary":
		print("-- " + data.challenger["name"] + " vs. ALL --")
		fightResults.sort(key=sortByName)

	#Print results as necessary and calculate summary stats
	for result in fightResults:
		if data.options["output"] == "Verbose":
			print("\n\n" + data.challenger["name"].upper() + " vs. " + result["enemy"].name.upper())
			print(result["fightText"])
			print(result["resultText"])
		elif data.options["output"] == "Summary":
			print(result["enemy"].name + ": " + result["resultText"])
		if (result["outcome"] == "loss"):
			losses += 1
		elif (result["outcome"] == "win"):
			wins += 1
		else:
			inconclusive += 1

	statsByName = {
		"Wins": wins,
		"Losses": losses,
		"Inconclusive": inconclusive
	}
	statsHeader = "SCENARIO\t"
	stats = data.options["roundInitiators"] + "\t\t"
	for stat in data.options["stats"]:
		statsHeader = statsHeader + stat + "\t"
		stats = stats + str(statsByName[stat]) + "\t"

	if data.options["output"] == "Verbose" or data.options["output"] == "Summary":
		print("\nTOTAL STATS")
		print(statsHeader)
	if data.options["output"] != "CompareBuilds":
		print(stats)
	return statsByName
		
#Calculate duel results for each specified scenario and determine summary stats
def calculateForEachScenario(scenarios):
	if data.options["output"] == "Totals":
		print("-- " + data.challenger["name"].upper() + " vs. ALL --")
		statsHeader = "SCENARIO\t"
		for stat in data.options["stats"]:
			statsHeader = statsHeader + stat + "\t"
		print("\nTOTAL STATS")
		print(statsHeader)
		
	totalStats = {}
	statsByScenario = {}
	for stat in data.options["stats"]:
		totalStats[stat] = 0
		
	for scenario in scenarios:
		statsByScenario[scenario] = {}
		data.options["roundInitiators"] = scenario
		statsForScenario = wrapWithTimer("calculate", calculate)
		for stat in data.options["stats"]:
			totalStats[stat] += statsForScenario[stat]
			statsByScenario[scenario][stat] = statsForScenario[stat]
			
	totalsLine = "\nTOTAL\t\t"
	for stat in data.options["stats"]:
		totalsLine = totalsLine + str(totalStats[stat]) + "\t"
	if data.options["output"] != "CompareBuilds":
		print(totalsLine)
	return statsByScenario
	
#Track how long a function call takes if the debug flag is set
def wrapWithTimer(name, function, *args):
	if data.options["debug"] == "full":
		startTime = time.clock()
		result = function(*args)
		endTime = time.clock()
		if name not in data.trackedCalls:
			data.trackedCalls[name] = []
		data.trackedCalls[name].append(endTime - startTime)
		return result
	else:
		return function(*args)
		
def sumStatAcrossScenarios(statsByScenario, stat):
	statTotal = 0
	for scenario in statsByScenario:
		statTotal += statsByScenario[scenario][stat]
	return statTotal
	
#Calculate and evaluate duel results for each possible build
def calculateForEachBuild(slots=data.options["comparebuildsslots"]):
	results = {}
	startTime = time.clock()
	focusSlot = None
	#If we're specifically looking at options for one slot, note it
	if len(slots) == 1:
		focusSlot = slots[0]
		slotresults = {}
	skillsets = data.buildSkillsets(data.challenger, slots)
	for skillset in skillsets:
		for slot in data.data["skillSlots"]:
			data.challenger[slot] = skillset[slot]
		data.setStats(data.challenger)
		data.challenger["activeHero"] = ActiveHero(data.challenger)
		skillsetString = (skillset["a"] + "," + skillset["b"] + "," + skillset["c"] + ","
				+ skillset["s"] + "," + skillset["special"] + "," + skillset["weapon"])
		results[skillsetString] = calculateForEachScenario(data.options["scenarios"])
		if focusSlot:
			slotresults[skillset[focusSlot]] = results[skillsetString]
		if data.options["compareBuildsOutputFormat"] == "complete":
			print("Calculating... (" + str(len(results)) + "/" + str(len(skillsets)) + ")")
	skillsetStrings = list(results.keys())
	endTime = time.clock()
	
	def getStatTotalAcrossScenariosToSort(skillsetString):
		#For this output mode, we only care about the primary stat
		return sumStatAcrossScenarios(results[skillsetString], data.options["stats"][0])
	
	def getStatTotalAcrossScenariosToSortForSlotOptions(skill):
		return sumStatAcrossScenarios(slotresults[skill], data.options["stats"][0])
	
	if data.options["comparebuildsstatformat"] == "StatTotalAcrossScenarios":
		skillsetStrings.sort(key=getStatTotalAcrossScenariosToSort, reverse=True)
		if focusSlot:
			slotoptions = list(slotresults.keys())
			slotoptions.sort(key=getStatTotalAcrossScenariosToSortForSlotOptions, reverse=True)
		
	resultsHeader = ""
	for scenario in data.options["scenarios"]:
		resultsHeader = resultsHeader + scenario + "\t"
	resultsHeader += "TOTAL\tBUILD"
	if data.options["compareBuildsOutputFormat"] != "exportsonly":
		print(resultsHeader)
		
	for i in range(min(len(skillsetStrings), data.options["comparebuildsresultslimit"])):
		skillsetString = skillsetStrings[i]
		resultsString = ""
		if data.options["comparebuildsstatformat"] == "StatTotalAcrossScenarios":
			for scenario in data.options["scenarios"]:
				resultsString += str(results[skillsetString][scenario][data.options["stats"][0]]) + "\t"
			resultsString += str(getStatTotalAcrossScenariosToSort(skillsetString))
			resultsString = resultsString + "\t" + skillsetString
		if data.options["compareBuildsOutputFormat"] != "exportsonly":
			print(resultsString)
		
	for i in range(min(len(skillsetStrings), data.options["exportbuilds"])):
		print (data.challenger["name"] + "Build" + str(i) + "," + data.challenger["name"] + ","
				+ data.challenger["boon"] + "," + data.challenger["bane"] + "," + str(data.challenger["merge"])
				+ "," + skillsetStrings[i] + ","
				+ str(getStatTotalAcrossScenariosToSort(skillsetStrings[i])))
	
	if data.options["debug"] == "full":
		print("DEBUG INFO")
		print("Builds Analyzed: " + str(len(skillsets)))
		print("Time Taken: " + str(endTime - startTime))
		print("Average Time per Build: " + str((endTime - startTime) / len(skillsets)))
	if focusSlot:
		return slotoptions
