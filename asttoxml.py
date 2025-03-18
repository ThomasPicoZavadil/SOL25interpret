from lark.lexer import Token
from xml.dom import minidom
import xml.etree.ElementTree as ET
import sys

RESERVED_KEYWORDS = ["self", "super", "nil", "true", "false", "class"]

# ✅ **Třída pro převod AST na XML**
class ASTToXML:
    def __init__(self, comment=None):
        """ Vytvoří hlavní XML element program s volitelným description. """
        attributes = {"language": "SOL25"}
        if comment:
            attributes["description"] = comment.replace("\n", " ")  # Převod odřádkování na mezery
        
        self.root = ET.Element("program", **attributes)

    def convert(self, node):
        # ✅ Spuštění rekurzivního převodu AST → XML
        self._convert_node(node, self.root)
        return self.root

    def _convert_node(self, node, parent_elem):
        if isinstance(node, str):
            if node in RESERVED_KEYWORDS:
                print("Syntax error: Cannot use reserved keyword as method name", file=sys.stderr)
                sys.exit(22)                
            ET.SubElement(parent_elem, "var", {"name": node})
            return
        
        if node.data == "start":
            for child in node.children:
                self._convert_node(child, parent_elem)  # Přidáme děti přímo pod rodiče
            return

        # ✅ Převod třídy na <class name="Main" parent="Object">
        if node.data == "class_def":
            class_name = node.children[0]  # Název třídy (CID)
            parent_name = node.children[1] if len(node.children) > 1 else "Object"  # Nadřazená třída
            class_elem = ET.SubElement(parent_elem, "class", name=class_name, parent=parent_name)
            for method in node.children[2:]:  # Metody
                if len(method.children) > 1:
                    self._convert_node(method, class_elem)
            return class_elem

        # ✅ Převod metody na <method selector="run">
        if node.data == "method":
            #print(node.children[0])
            if node.children[0].children[0] in RESERVED_KEYWORDS:
                print("Syntax error: Cannot use reserved keyword as method name", file=sys.stderr)
                sys.exit(22)
            method_elem = ET.SubElement(parent_elem, "method", selector=node.children[0].children[0])
            # ✅ Každá metoda obsahuje blok kódu
            self._convert_node(node.children[1], method_elem)
            return method_elem

        if node.data == "block":
            # Počet parametrů = počet dětí v `block_par`
            arity = len(node.children[0].children) if node.children else 0
            block_elem = ET.SubElement(parent_elem, "block", arity=str(arity))

            # Přidání parametrů bloku (block_par)
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
            if node.children[0] in RESERVED_KEYWORDS:
                print("Syntax error: Cannot assign to reserved keyword", file=sys.stderr)
                sys.exit(22)

            # Převod proměnné (var)
            ET.SubElement(assign_elem, "var", name=node.children[0])

            # Převod výrazu (expr)
            self._convert_node(node.children[1], assign_elem)

            return assign_elem
        
        #if node.data == "expr":
        #    expr_elem = ET.SubElement("expr")
        #    parent_elem =  expr_elem



            #return expr_elem

        if node.data == "expr_base":

            if isinstance(node.children[0], Token):
                value = node.children[0].value
                token_type = node.children[0].type


                literal = ET.Element('literal', value=value)

                if value in RESERVED_KEYWORDS:
                    ET.SubElement(parent_elem, "literal", {"class": value.capitalize(), "value": value})

                else:
                    match token_type:
                        case 'INT':
                            literal.set('class', 'Integer')
                            parent_elem.append(literal)
                        case 'STR':
                            literal.set('class', 'String')
                            literal.set('value', value[1:-1])
                            parent_elem.append(literal)
                        case 'ID':
                            ET.SubElement(parent_elem, "var", {"name": value})
                        case 'CID':
                            #ET.SubElement(parent_elem, "class", {"name": value})
                            literal.set('class', 'Class')
                            parent_elem.append(literal)
                        case _:
                            self._convert_node(value, parent_elem)
            else:
                self._convert_node(node.children[0], parent_elem)

            return
        
        if node.data == "expr_tail":
            for child in node.children:
                self._convert_node(child, parent_elem)  # Přidáme děti přímo pod rodiče
            return

        # ✅ Rekurzivní zpracování ostatních uzlů
        elem = ET.SubElement(parent_elem, node.data)
        for child in node.children:
            self._convert_node(child, elem)


    def to_pretty_xml(self):
        rough_string = ET.tostring(self.root, encoding="utf-8").decode("utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(encoding="UTF-8").decode("utf-8")

# ✅ **Funkce pro zápis do souboru**
def save_to_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)