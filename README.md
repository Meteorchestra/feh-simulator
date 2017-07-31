# FEH Build Evaluator
A mass dueling simulator and build evaluator for Fire Emblem Heroes.

Forked from https://github.com/Andu2/FEH-Mass-Simulator and converted to a Python command-line tool.

Current features:
- Calculate mass duel results based on character information and options stored in local input files
- Evaluate results across multiple scenarios at once (offensive ORKOs, defensive ORKOs, extended duels, etc.)
- Find optimal builds for a character with one command (based on provided criteria)
- Evaluate results against custom enemy lists with multiple builds for the same hero

Upcoming features:
- More statistics to evaluate
- Additional modes to better evaluate resiliency of builds over multiple battles
- Team evaluation capabilities

Run with 'python battleSim.py OPTIONSFILEPATH' - will default to options.txt if no filepath is given.

Also try 'python battleSim.py findbuilds.txt HERONAME' - you can specify the hero name as an additional argument to easily use the same options for multiple heroes.

The provided options.txt is a sample options file and contains information about the currently available options.
