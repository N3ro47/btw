.PHONY: all setup grammar lint format build clean

# Python environment manager
UV = uv

# ANTLR settings
ANTLR_JAR = jar/antlr-4.13.2-complete.jar
GRAMMAR_DIR = src/grammar
GEN_DIR = $(GRAMMAR_DIR)/build

all: setup grammar build

setup:
	@echo "Syncing python dependencies..."
	$(UV) sync

grammar:
	@echo "Compiling ANTLR4 Grammars..."
	mkdir -p $(GEN_DIR)
	touch $(GEN_DIR)/__init__.py
	cd $(GRAMMAR_DIR) && java -jar ../../$(ANTLR_JAR) -Dlanguage=Python3 -visitor -no-listener -o build ArchLexer.g4
	cd $(GRAMMAR_DIR) && java -jar ../../$(ANTLR_JAR) -Dlanguage=Python3 -visitor -no-listener -lib build -o build ArchParser.g4

lint:
	@echo "Running Ruff linter..."
	$(UV) run ruff check .

format:
	@echo "Running Ruff formatter..."
	$(UV) run ruff format .

build:
	@echo "Transpiling dev_rig.arch to install.sh..."
	$(UV) run python archspec.py build examples/dev_rig.arch

clean:
	@echo "Cleaning up..."
	rm -rf $(GEN_DIR)
	rm -f install.sh
