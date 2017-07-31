import data
import battle
import sys

#Process options from the specified file or fallback to options.txt
if len(sys.argv) > 1:
	data.parseOptions(sys.argv[1])
else:
	data.parseOptions()
	
#If there's another argument, set it as the challenger name
if len(sys.argv) > 2:
	data.challenger["name"] = sys.argv[2]

#Initialize hero and enemies
hero = data.challenger
data.initHero(data.challenger, True)
data.challenger["activeHero"] = battle.ActiveHero(data.challenger)
data.initEnemyList()

for enemy in data.enemies["fl"]["list"]:
		data.enemies["fl"]["activeHeroes"][enemy] = battle.ActiveHero(data.enemies["fl"]["list"][enemy])
		
if data.options["output"] == "CompareBuilds":
	#Run each slot individually and track top results, then calculate for skillsets from the top slot results
	if "consecutive" in data.options["comparebuildsslots"][0]:
		slotsToKeep = data.options["comparebuildsslots"][0].split("-")
		slotsToKeep.remove("consecutive")
		topresults = {}
		for slot in data.data["skillSlots"]:
			if slot in slotsToKeep:
				topresults[slot] = [data.challenger[slot]]
			else:
				data.options["comparebuildsslots"] = [slot]
				data.initHero(data.challenger)
				slotresults = battle.calculateForEachBuild(data.buildSkillsets(data.challenger))
				topresults[slot] = slotresults[0:data.options["comparebuildstopskills"]]
		for slot in data.data["skillSlots"]:
			data.challenger["validSkills"][slot] = topresults[slot]
		data.options["comparebuildsslots"] = []
		for slot in data.data["skillSlots"]:
			if slot not in slotsToKeep:
				data.options["comparebuildsslots"].append(slot)
		data.initHero(data.challenger, False, True)
		battle.calculateForEachBuild(data.buildSkillsets(data.challenger))
	
	#Otherwise build all the skillsets
	else:
		battle.calculateForEachBuild(data.buildSkillsets(data.challenger))
else:
	battle.calculateForEachScenario(data.options["scenarios"])
	
#Print debug data if it has been generated
for function in data.trackedCalls:
	totalTime = sum(data.trackedCalls[function])
	calls = len(data.trackedCalls[function])
	print function + ": " + str(totalTime/calls) + " average over " + str(calls) + " calls (" + str(totalTime) + " total)"