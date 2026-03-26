import argparse
import sys

from antlr4 import CommonTokenStream, FileStream

from src.archspec.code_generator import CodeGenerator
from src.archspec.parser_handler import ASTVisitor
from src.archspec.semantic_analyzer import SemanticAnalyzer, SemanticError
from src.grammar.build.ArchLexer import ArchLexer
from src.grammar.build.ArchParser import ArchParser


def compile_arch(filepath: str, output: str):
    print(f"[*] Phase 1: Parsing {filepath}...")

    input_stream = FileStream(filepath)
    lexer = ArchLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = ArchParser(stream)

    tree = parser.program()

    print("[*] Phase 1: Outlining AST Construction...")
    visitor = ASTVisitor()
    ast = visitor.visit(tree)

    if not ast:
        print("[!] Failed to parse AST.")
        sys.exit(1)

    print("[*] Phase 1: Running Outline Semantic Analysis...")
    analyzer = SemanticAnalyzer(ast)
    try:
        analyzer.analyze()
    except SemanticError as e:
        print(f"[!] {e}")
        sys.exit(1)

    print(f"[*] Phase 1: Outlining Code Generation to {output}...")
    generator = CodeGenerator(ast)
    bash_script = generator.generate()

    with open(output, "w") as f:
        f.write(bash_script)

    print(f"[+] Phase 1 Architecture Compilation successful! Outline saved to '{output}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArchSpec Compiler Outline")
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
