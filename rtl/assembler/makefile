
BUILD = build
GRAMMAR = eater

ANTLR4_ROOT = /usr/local/lib/antlr-4.9.1-complete.jar
ANTLR4 = java -jar $(ANTLR4_ROOT)
GRUN = java org.antlr.v4.gui.TestRig

EXAMPLE = examples/eater.asm

.PHONY: all build_java test_java

all: $(BUILD) build_python

test: $(BUILD) build_java test_java build_python test_python

build_python: $(BUILD)
	$(ANTLR4) -Dlanguage=Python3 -visitor -o $(BUILD) $(GRAMMAR).g4

build_java: $(BUILD)/eaterParser.java $(BUILD)/eaterLexer.java
	$(ANTLR4) -o $(BUILD) $(GRAMMAR).g4
	javac -d $(BUILD) $(BUILD)/$(GRAMMAR)*.java

test_java:
	cd $(BUILD); \
	$(GRUN) $(GRAMMAR) parse ../$(EXAMPLE) -gui

$(BUILD):
	mkdir -p $@
	touch $@/__init__.py

clean:
	rm -rf $(BUILD)
