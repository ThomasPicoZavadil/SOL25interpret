import sys
from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken, UnexpectedEOF
from grammar import parse_file, parse_args
from asttoxml import ASTToXML, save_to_file
from semantic import SemanticAnalyzer

if __name__ == "__main__":
    try:
        # Read input from stdin
        content = sys.stdin.read().strip()  # Odstraníme mezery na konci

        # Parse command line arguments
        parse_args()

        # Try parsing the input
        parse_tree, first_comment = parse_file(content, from_stdin=True)

        # Save AST to a file
        ast_str = parse_tree.pretty()
        save_to_file("ast.txt", ast_str)

        # ✅ **Spustíme sémantickou analýzu**
        analyzer = SemanticAnalyzer()
        analyzer.analyze(parse_tree)

        # ✅ **Pokračujeme s převodem do XML pouze pokud analýza neukončila program**
        xml_converter = ASTToXML(comment=first_comment)
        xml_converter.convert(parse_tree)

        # Save XML to a file
        xml_str = xml_converter.to_pretty_xml()
        save_to_file("output.xml", xml_str)

        # Print XML output
        print(xml_str)

    except UnexpectedToken as e:
        # Syntaktická chyba
        print(f"Syntaktická chyba na řádku {e.line}, sloupci {e.column}: {e.get_context(content)}", file=sys.stderr)
        sys.exit(22)

    except UnexpectedCharacters as e:
        # Lexikální chyba - neplatný znak v kódu
        print(f"Lexikální chyba na řádku {e.char} {e.line}, sloupci {e.column}: {e.get_context(content)}", file=sys.stderr)
        sys.exit(21)

    except Exception as e:
        # Obecná chyba
        print(f"Neznámá chyba: {e}", file=sys.stderr)
        sys.exit(99)
