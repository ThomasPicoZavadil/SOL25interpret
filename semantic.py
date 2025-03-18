import sys

class SemanticAnalyzer:
    def __init__(self):
        self.classes = {}  # Uložíme mapu tříd { "ClassName": ["method1", "method2", ...] }
        self.variables = {}  # { "method_name": {"var1", "var2", ...} }
        self.builtin_classes = {"Object", "Integer", "String", "Nil", "Block", "True", "False"}  # Vestavěné třídy
        self.errors_found = False

    def analyze(self, node):
        """ Hlavní funkce pro analýzu AST """
        self._collect_classes(node)  # Nejprve shromáždíme všechny třídy a metody
        self._check_main_class_and_run()  # Pak provedeme kontrolu existence Main a run
        #self._check_undefined_classes(node)
        self._check_block_arity(node)
        #if self.errors_found:
        #    sys.exit(33)

    def _collect_classes(self, node):
        """ Projde AST a shromáždí názvy tříd a jejich metod """
        if node.data == "class_def":
            class_name = node.children[0]  # Název třídy
            self.classes[class_name] = set()  # Inicializujeme prázdnou množinu metod

            # Projdeme děti, abychom získali metody
            for child in node.children[2:]:  # Metody jsou po jménu třídy a rodičovské třídě
                if child.data == "method":
                    if len(child.children) > 0 and len(child.children[0].children) > 0:
                        method_name = child.children[0].children[0]
                        self.classes[class_name].add(method_name)

        # Rekurzivně projdeme celý strom
        for child in node.children:
            if hasattr(child, 'data'):  # Zajistíme, že je to platný uzel
                self._collect_classes(child)

    def _check_main_class_and_run(self):
        """ Ověří, zda existuje třída Main a obsahuje metodu run """
        if "Main" not in self.classes:
            print("Sémantická chyba: Chybí třída Main", file=sys.stderr)
            sys.exit(31)

        if "run" not in self.classes["Main"]:
            print("Sémantická chyba: Třída Main neobsahuje metodu run", file=sys.stderr)
            sys.exit(31)

    def _check_undefined_classes(self, node):
        """ Prochází AST a hledá použití nedefinovaných tříd """
        if node.data == "expr_base":
            class_name = node.children[0]  # Může být CID (třída)

            # Pokud je to třída, zkontrolujeme její existenci
            if class_name not in self.classes and class_name not in self.builtin_classes:
                print(f"Sémantická chyba: Použití nedefinované třídy '{class_name}'", file=sys.stderr)
                sys.exit(32)

        # Rekurzivní průchod AST
        for child in node.children:
            if hasattr(child, 'data'):
                self._check_undefined_classes(child)

    def _check_block_arity(self, node):
            """ Ověří, zda arita bloku odpovídá selektoru metody """
            if node.data == "method":
                selector = node.children[0].children[0]  # Název selektoru (např. `compute:and:and:`)
                expected_arity = selector.count(":")  # Počet `:` udává očekávanou aritu
                block_node = node.children[1]  # Blok v metodě

                if block_node.data == "block":
                    actual_arity = len(block_node.children[0].children) if block_node.children else 0

                    if expected_arity != actual_arity:
                        print(f"Sémantická chyba: Metoda '{selector}' očekává blok s aritou {expected_arity}, ale dostala {actual_arity}",
                            file=sys.stderr)
                        self.errors_found = True  # Označíme, že jsme našli chybu

            # Rekurzivní průchod AST
            for child in node.children:
                if hasattr(child, 'data'):
                    self._check_block_arity(child)