import argparse
import sys
import os

from antlr4 import CommonTokenStream, FileStream

from src.archspec.code_generator import CodeGenerator
from src.archspec.parser_handler import ASTVisitor, CompilerErrorListener
from src.archspec.semantic_analyzer import SemanticAnalyzer, SemanticError
from src.grammar.build.ArchLexer import ArchLexer
from src.grammar.build.ArchParser import ArchParser

class Console:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    GRAY = "\033[90m"

    @classmethod
    def info(cls, msg):
        print(f"{cls.BLUE}{cls.BOLD}[*]{cls.RESET} {msg}")

    @classmethod
    def success(cls, msg):
        print(f"{cls.GREEN}{cls.BOLD}[+]{cls.RESET} {msg}")

    @classmethod
    def error(cls, msg):
        print(f"{cls.RED}{cls.BOLD}[!] {msg}{cls.RESET}")

    @classmethod
    def print_snippet(cls, filepath, line_num, col_num, error_msg):
        cls.error(f"{filepath}:{line_num}:{col_num} - {error_msg}")
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if 0 < line_num <= len(lines):
                target_line = lines[line_num - 1].rstrip('\n')
                
                # Print contextual lines (1 before, the line itself)
                if line_num > 1:
                    print(f"  {cls.GRAY}{line_num - 1:3} | {lines[line_num - 2].rstrip()}{cls.RESET}")
                
                print(f"  {cls.YELLOW}{line_num:3} | {cls.RESET}{target_line}")
                
                # Pointer
                if col_num is not None:
                    pointer = " " * (col_num + 8) + f"{cls.RED}^{cls.RESET}"
                    print(pointer)
        except Exception:
            pass
        print()


def compile_arch(filepath: str, output: str):
    Console.info(f"Parsing {filepath}...")

    if not os.path.exists(filepath):
        Console.error(f"File not found: {filepath}")
        sys.exit(1)

    input_stream = FileStream(filepath)
    lexer = ArchLexer(input_stream)
    
    error_listener = CompilerErrorListener()
    
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)
    
    stream = CommonTokenStream(lexer)
    parser = ArchParser(stream)
    
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    tree = parser.program()

    if error_listener.errors:
        Console.error(f"Failed to parse '{filepath}' with {len(error_listener.errors)} syntax errors:\n")
        for line, col, msg in error_listener.errors:
            Console.print_snippet(filepath, line, col, msg)
        sys.exit(1)

    Console.info("Building AST...")
    visitor = ASTVisitor()
    ast = visitor.visit(tree)

    if not ast:
        Console.error("Failed to build AST from syntax tree.")
        sys.exit(1)

    Console.info("Running Semantic Analysis...")
    analyzer = SemanticAnalyzer(ast)
    try:
        analyzer.analyze()
    except SemanticError as e:
        errors = e.args[0]
        Console.error(f"Semantic Validation Failed with {len(errors)} errors:\n")
        for line, col, msg in errors:
            Console.print_snippet(filepath, line, col, msg)
        sys.exit(1)

    Console.info(f"Generating Code to {output}...")
    generator = CodeGenerator(ast)
    bash_script = generator.generate()

    with open(output, "w") as f:
        f.write(bash_script)

    Console.success(f"Compilation successful! Output saved to '{output}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArchSpec Compiler")
    parser.add_argument("command", choices=["build"], help="Command to run")
    parser.add_argument("file", help="The .arch file to compile")
    parser.add_argument(
        "-o",
        "--output",
        default="install.sh",
        help="Output Bash script file (default install.sh)",
    )

    args = parser.parse_args()

    if args.command == "build":
        compile_arch(args.file, args.output)
