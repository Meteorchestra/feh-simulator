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

# Step By Step Instructions

1. Install Python, if you don't have it already - the latest 2.x version or the latest 3.x version from https://www.python.org should each work

2. Click the green button on this page to download the files from this repository as a ZIP. Extract the files to some location FILEPATH.

3. Open a Command Prompt / Terminal window and use the command 'cd FILEPATH' to get to the directory where the files are.

4. Use the command 'python battleSim.py' to run the tool with the options from options.txt, or use 'python battleSim.py OPTIONSFILEPATH' to run the tool with options from a file located at OPTIONSFILEPATH.
