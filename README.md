# ArchSpec

ArchSpec is a declarative DSL for generating Arch Linux installation scripts. It allows you to specify your system configuration (storage, users, software, etc.) in a clean, high-level language and compile it into a robust, idempotent Bash installation script.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)
- Java Runtime Environment (for ANTLR4 compiler generation)

### Installation

Sync dependencies:
```bash
make setup
```

### Usage

1. **Compile Grammar**: If you modify the DSL grammar, regenerate the parser:
   ```bash
   make grammar
   ```

2. **Build Installation Script**:
   ```bash
   make build
   ```
   Or explicitly:
   ```bash
   uv run archspec.py build examples/dev_rig.arch -o install.sh
   ```

## Project Structure

- `src/grammar/`: ANTLR4 grammar definitions (`.g4` files).
- `src/archspec/`: Compiler source code (AST, Semantic Analyzer, Code Generator).
- `examples/`: Sample `.arch` configuration files.
- `archspec.py`: CLI entry point for the compiler.