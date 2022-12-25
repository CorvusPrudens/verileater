TARGET = eater
BUILD = build

VERILOG_INCLUDES = \
-I.

VERILOG_DEFS = 

.PHONY: all arch next lint clean

all: lint arch next

arch: $(BUILD)
	yosys -p 'verilog_defaults -add $(VERILOG_INCLUDES) $(VERILOG_DEFS); read_verilog $(TARGET).v; synth_ice40 -dsp -abc9 -top $(TARGET) -json $(BUILD)/$(TARGET).json'

TARGET_FREQ = 48
NEXT_ARCH_FLAGS = --freq $(TARGET_FREQ) --lp8k --package bg121
NEXT_SETTINGS = 

next: $(BUILD) $(BUILD)/$(TARGET).json
	nextpnr-ice40 $(NEXT_ARCH_FLAGS) $(NEXT_SETTINGS) --report $(BUILD)/report.json --top $(TARGET) --json $(BUILD)/$(TARGET).json --asc $(BUILD)/$(TARGET).asc
	icepack $(BUILD)/$(TARGET).asc $(BUILD)/$(TARGET).bin
	python3 pretty_timing.py $(BUILD)/report.json > $(BUILD)/timing.txt

lint:
	verilator --lint-only $(VERILOG_INCLUDES) -DSIM $(TARGET).v

$(BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)
