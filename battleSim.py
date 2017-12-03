from __future__ import division
from __future__ import print_function
import data
import battle
import sys

#If there's another argument, set it as the challenger name
if len(sys.argv) > 2:
	data.options["heronames"] = [sys.argv[2]]

#Initialize enemies
data.initEnemyList()

for enemy in data.enemies["fl"]["list"]:
		data.enemies["fl"]["activeHeroes"][enemy] = battle.ActiveHero(data.enemies["fl"]["list"][enemy])
		
if "comparebuildsslots" in data.options:
	if "consecutive" in data.options["comparebuildsslots"][0]:
		slotsToKeep = data.options["comparebuildsslots"][0].split("-")
		slotsToKeep.remove("consecutive")
		finalSlots = []
		for slot in data.data["skillSlots"]:
			if slot not in slotsToKeep:
				finalSlots.append(slot)
	
#Process input hero names
if "allheroes" in data.options["heronames"]:
	data.options["heronames"] = list(data.heroes.keys())
	
for heroname in data.options["heronames"]:
	data.challenger["name"] = heroname

	hero = data.challenger
	for slot in data.data["skillSlots"]:
		data.challenger[slot] = data.options[slot]
	data.initHero(data.challenger, True)
	data.challenger["activeHero"] = battle.ActiveHero(data.challenger)
			
	if data.options["output"] == "CompareBuilds":
		#Run each slot individually and track top results, then calculate for skillsets from the top slot results
		if "consecutive" in data.options["comparebuildsslots"][0]:
			topresults = {}
			for slot in data.data["skillSlots"]:
				if slot in slotsToKeep:
					topresults[slot] = [data.challenger[slot]]
				else:
					data.initHero(data.challenger)
					slotresults = battle.calculateForEachBuild([slot])
					topresults[slot] = slotresults[0:data.options["comparebuildstopskills"]]
			for slot in data.data["skillSlots"]:
				data.challenger["validSkills"][slot] = topresults[slot]
			
			data.initHero(data.challenger, False, True)
			battle.calculateForEachBuild(finalSlots)
		
		#Otherwise build all the skillsets
		else:
			battle.calculateForEachBuild()
	else:
		battle.calculateForEachScenario(data.options["scenarios"])
	
#Print debug data if it has been generated
for function in data.trackedCalls:
	totalTime = sum(data.trackedCalls[function])
	calls = len(data.trackedCalls[function])
	print(function + ": " + str(totalTime/calls) + " average over " + str(calls) + " calls (" + str(totalTime) + " total)")
