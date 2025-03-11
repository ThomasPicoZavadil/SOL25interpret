from lark import Lark
from xml.dom import minidom
import xml.etree.ElementTree as ET

# ✅ **Definice gramatiky SOL25**
grammar = """
start: program

program: class_def program |  // Podpora více tříd

class_def: "class" CID (":" CID)? "{" method "}"

method: selector block method | 

selector: ID | IDSELECT selector_tail
selector_tail: IDSELECT selector_tail |

block: "[" block_par "|" block_stat "]"
block_par: (parameter)*
parameter: ":" IDDEF
block_stat: (assign)*
assign: ID ":=" expr "."


expr: expr_base (expr_sel)?
expr_tail: ID | expr_sel
expr_sel: IDSELECT expr (expr_sel)?

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
        # ✅ Vytvoření hlavního XML elementu <program>
        self.root = ET.Element("program", language="SOL25", description=" ")

    def convert(self, node):
        # ✅ Spuštění rekurzivního převodu AST → XML
        self._convert_node(node, self.root)
        return self.root

    def _convert_node(self, node, parent_elem):
        if isinstance(node, str):
            ET.SubElement(parent_elem, "var", {"name": node})
            return

        # ✅ Převod třídy na <class name="Main" parent="Object">
        if node.data == "class_def":
            class_name = node.children[0]  # Název třídy (CID)
            parent_name = node.children[1] if len(node.children) > 1 else "Object"  # Nadřazená třída
            class_elem = ET.SubElement(parent_elem, "class", name=class_name, parent=parent_name)
            for method in node.children[2:]:  # Metody
                self._convert_node(method, class_elem)
            return class_elem

        # ✅ Převod metody na <method selector="run">
        if node.data == "method":
            method_elem = ET.SubElement(parent_elem, "method", selector=node.children[0].children[0])
            
            # ✅ Každá metoda obsahuje blok kódu
            self._convert_node(node.children[1], method_elem)
            return method_elem

        if node.data == "block":
            # Počet parametrů = počet dětí v `block_par`
            arity = len(node.children[0].children) if node.children else 0
            block_elem = ET.SubElement(parent_elem, "block", arity=str(arity))

            # Přidání parametrů bloku
            for idx, param in enumerate(node.children[0].children, start=1):
                ET.SubElement(block_elem, "parameter", name=param.children[0], order=str(idx))

            # Přidání příkazů v bloku (block_stat)
            for idx, stat in enumerate(node.children[1:], start=1):
                stat_elem = self._convert_node(stat, block_elem)
                if stat_elem is not None:
                    stat_elem.set("order", str(idx))

            return block_elem

        if node.data == "assign":
            assign_elem = ET.SubElement(parent_elem, "assign")

            # Převod proměnné (var)
            ET.SubElement(assign_elem, "var", name=node.children[0])

            # Převod výrazu (expr)
            expr_elem = ET.SubElement(assign_elem, "expr")
            self._convert_node(node.children[1], expr_elem)

            return assign_elem

        if node.data == "expr_sel":
            send_elem = ET.SubElement(parent_elem, "send", selector=node.children[0])

            # Přidání výrazu pro příjemce zprávy
            self._convert_node(node.children[1], send_elem)  # 🔹 Už neukládáme do `expr`, ale rovnou do `send`

            # Přidání argumentů
            for idx, arg in enumerate(node.children[2:], start=1):
                arg_elem = ET.SubElement(send_elem, "arg", order=str(idx))
                self._convert_node(arg, arg_elem)  # 🔹 Argumenty se vkládají přímo do `arg`, ne do dalšího `expr`

            return send_elem

        if node.data == "expr_base":
            if isinstance(node.children[0], str):
                if node.children[0] in ["Integer", "String", "Object", "Nil", "Block", "True", "False"]:
                    ET.SubElement(parent_elem, "literal", {"class": node.children[0], "value": node.children[0]})
                else:
                    ET.SubElement(parent_elem, "var", name=node.children[0])
            else:
                self._convert_node(node.children[0], parent_elem)
            return

        # ✅ Rekurzivní zpracování ostatních uzlů
        elem = ET.SubElement(parent_elem, node.data)
        for child in node.children:
            self._convert_node(child, elem)

    def to_pretty_xml(self):
        rough_string = ET.tostring(self.root, encoding="unicode")
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
