from lark import Lark
from xml.dom import minidom
import xml.etree.ElementTree as ET

# ✅ **Definice gramatiky SOL25**
grammar = """
start: program

program: class program |  // Podpora více tříd

class: "class" CID ":" parent_class "{" method "}"

parent_class: CID |

method: selector block method | 

selector: ID | IDSELECT selector_tail
selector_tail: IDSELECT selector_tail |

block: "[" block_par "|" block_stat "]"
block_par: (parameter)*
parameter: ":" IDDEF
block_stat: (ID ":=" expr ".")*

expr: expr_base expr_tail
expr_tail: ID | expr_sel
expr_sel: IDSELECT expr_base expr_sel |

expr_base: INT | STR | ID | CID | block | "(" expr ")" | KEYWORD

IDSELECT: /[a-z][a-zA-Z0-9]*/ ":"
IDDEF: /[a-z][a-zA-Z0-9]*/ 
CID: "Object" | "Integer" | "String" | "Nil" | "Block" | "True" | "False" | /[A-Z][a-zA-Z0-9]*/  
ID: /[a-z][a-zA-Z0-9_]*/
INT: /[0-9]+/
STR: /'[^"]*'/

KEYWORD: "self" | "super" | "nil" | "true" | "false"

%import common.WS
%ignore WS
"""

# ✅ **Vytvoření parseru**
parser = Lark(grammar, start='start', parser='earley')

# ✅ **Funkce pro parsování souboru**
def parse_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return parser.parse(content)

# ✅ **Třída pro převod AST na XML**
class ASTToXML:
    def __init__(self):
        self.root = ET.Element('program', language='SOL25', description=' ')

    def convert(self, node):
        return self._convert_node(node, self.root)

    def _convert_node(self, node, parent_elem):
        if isinstance(node, str):
            elem = ET.SubElement(parent_elem, "token")
            elem.text = node
            return elem
        
        elem = ET.SubElement(parent_elem, node.data)
        for child in node.children:
            self._convert_node(child, elem)

        return elem

    def to_pretty_xml(self):
        rough_string = ET.tostring(self.root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

# ✅ **Spuštění programu**
if __name__ == "__main__":
    file_path = 'test.sol25'
    try:
        parse_tree = parse_file(file_path)
        print(parse_tree.pretty())

        xml_converter = ASTToXML()
        xml_converter.convert(parse_tree)

        # ✅ **Použití minidom pro formátování výstupu**
        print(xml_converter.to_pretty_xml())

    except Exception as e:
        print(f"Error parsing file: {e}")
