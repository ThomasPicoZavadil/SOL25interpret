from lark import Lark
import argparse
import sys
import re

def loadGrammar(grammar_path):
    """Load grammar from file"""
    try:
        with open(grammar_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError: # File of grammar was not found
        print("Chyba: Soubor gramatiky nebyl nalezen.", file=sys.stderr)
    except PermissionError:   # Dont have rights to read grammar
        print("Chyba: Nedostatečná oprávnění pro čtení gramatiky.", file=sys.stderr)
    except Exception as e:  # Error while loading grammar
        print(f"Chyba při načítání gramatiky: {e}", file=sys.stderr)

# ✅ **Create Lark Parser**
parser = Lark(loadGrammar("./grammer.lark"), start='start', parser='lalr')

# ✅ **Nastavení argumentů**
def parse_args():
    # ❌ Kontrola duplicitních argumentů `-h` nebo `--help`
    if sys.argv.count("-h") > 1 or sys.argv.count("--help") > 1 or ("-h" in sys.argv and "--help" in sys.argv):
        print("Neplatná kombinace parametrů: více výskytů --help", file=sys.stderr)
        sys.exit(10)

    arg_parser = argparse.ArgumentParser(description="SOL25 Interpreter", add_help=False)
    arg_parser.add_argument("-h", "--help", action="store_true", help="Zobrazí nápovědu")
    
    args, unknown = arg_parser.parse_known_args()

    # ❌ Zakázaná kombinace argumentů
    if unknown:
        print(f"Neplatná kombinace parametrů: {' '.join(unknown)}", file=sys.stderr)
        sys.exit(10)

    # ✅ Zobrazení nápovědy
    if args.help:
        arg_parser.print_help()
        sys.exit(0)

    return args

# ✅ **Function to parse input file and extract AST**
def parse_file(input_data, from_stdin=False):
    """
    Parses the input from a file or stdin.
    :param input_data: Either file content (if from_stdin=True) or file path.
    :param from_stdin: Boolean flag to distinguish between file input and stdin input.
    :return: Parsed AST and first comment.
    """
    if not from_stdin:
        with open(input_data, 'r') as file:
            input_data = file.read()

    # Extract first comment
    match = re.search(r'"([^"]*)"', input_data)
    first_comment = match.group(1) if match else None

    return parser.parse(input_data), first_comment

