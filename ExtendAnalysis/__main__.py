import sys
import argparse
from importlib import import_module

# QApplication is created in ExtendAnalysis
import ExtendAnalysis

# Help
parser = argparse.ArgumentParser(prog='lys', usage="python -m lys (options)", add_help=True)
# Launch local cluster
parser.add_argument("-n", "--ncore", help="Launch local cluster with NCORE", type=int, required=False)
# Plugins
parser.add_argument("-p", "--plugin", help="Import plugins", nargs="*", required=False)
# NoPlugins
parser.add_argument("-np", "--noplugin", help="Do not import local plugins", action="store_true")

# parse args
args = parser.parse_args()

# Launch local cluster
if args.ncore is not None:
    ExtendAnalysis.DaskWave.initWorkers(args.ncore)

# Create main window
print('Welcome to Analysis program lys. Launching main window...')
ExtendAnalysis.plugin._createMainWindow()

# Load local Plugins
if not args.noplugin:
    import ExtendAnalysis.localPlugins

    # Load Plugins
    if args.plugin is not None:
        print("Importing plugins: ", args.plugin)
        for plugin in args.plugin:
            import_module(plugin)
else:
    print("lys is launched wih -np option. No plugin loaded.")


sys.exit(ExtendAnalysis.QtSystem.app.exec())
