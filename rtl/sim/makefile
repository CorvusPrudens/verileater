# TODO -- we need to set up dead code stripping
UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
NPROC = $$(nproc)
else
NPROC = 4
endif

PYVAR = python3

CC = g++
BUILD = build
TRACE_FILE = $(BUILD)/trace.vcd
VERILATION = $(BUILD)/verilation
VERILATOR = verilator
VERILATOR_FLAGS = -j -Wall --compiler gcc --cc -O3 --x-assign fast --x-initial fast --noassert -Wno-UNUSED -Wno-UNSIGNED -CFLAGS "-O3" --Mdir $(VERILATION)
VERILATOR_FLAGS_TRACE = -j -Wall --compiler gcc --cc --trace  -Wno-UNUSED -Wno-UNSIGNED -CFLAGS "-O3" --Mdir $(VERILATION)
# --trace-max-array 64
VERILOG_INCLUDES = \
-I$(CORISC_PATH)/rv32im \
-I$(CORISC_PATH)/blocks \
-I../driver/serv \
-I../driver \
-I../bootloader/common \
-I../

VERILOG_DEFS = \
-DSIM \
-DDEFAULT_INSTR_HEX=\"../hex/instructions.hex\" \
-DDEFAULT_OUTPUT_HEX=\"../hex/output.hex\" \
-DDEFAULT_PROGRAM_HEX=\"../build/program.hex\"

TARGET = eater

CPP_SOURCES = sim.cpp \
${VERILATOR_INCL}/include/verilated.cpp \
${VERILATOR_INCL}/include/verilated_vcd_c.cpp

CPP_INCLUDES = \
-Imodules \
-I$(BUILD) \
-I$(VERILATION) \
-I${VERILATOR_INCL}/include

CPP_FLAGS += \
-std=c++2a \
-DTRACE_FILE=\"$(TRACE_FILE)\" \
-DPROG_BIN=\"$(PROGRAM_DIR)/target/riscv32i-unknown-none-elf/release/epaper-rust\"

ifeq ($(UNAME), Linux)
# LINKER_FLAGS = -lglfw -lGLEW -lGL -lm -lX11 -lpthread -lXi -lXrandr -ldl
LINKER_FLAGS = -lglfw -lGLEW -lGL -lsndfile
else
LINKER_FLAGS = -framework OpenGL -lglfw -lGLEW -lsndfile
endif

ifeq ($(DEBUG), 1)
OPT = -O0
CPP_FLAGS += -g
else
OPT = -O3
endif

OBJECTS = $(addprefix $(BUILD)/,$(CPP_SOURCES:.cpp=.o))
vpath %.cpp $(sort $(dir $(CPP_SOURCES)))
SORTED_OBJECTS = $(sort $(OBJECTS))

.PHONY: all compile_example clean verilate \
	compile verilate_trace compile_trace trace \
	debug verilate_debug compile_debug compile_bootloader

all: $(VERILATION)
	$(MAKE) verilate
	$(MAKE) -j$(NPROC) $(BUILD)/$(TARGET) CLOCK_COUNT="-DNUM_FRAMES=2000"

trace: $(VERILATION)
	$(MAKE) verilate_trace
	$(MAKE) -j$(NPROC) $(BUILD)/$(TARGET) TRACE="-DTRACE" CLOCK_COUNT="-DNUM_FRAMES=8"

debug: $(VERILATION)
	$(MAKE) verilate_debug
	$(MAKE) -j$(NPROC) $(BUILD)/$(TARGET) DEBUG=1

$(BUILD):
	mkdir -p $@

$(VERILATION): $(BUILD)
	mkdir -p $@

$(BUILD)/%.o: %.cpp makefile | $(BUILD)
	mkdir -p $(@D)
	$(CC) $(OPT) $(CPP_FLAGS) $(CLOCK_COUNT) $(CPP_INCLUDES) $(TRACE) -c $< -o $@

$(BUILD)/$(TARGET): $(SORTED_OBJECTS) makefile
	$(CC) $(SORTED_OBJECTS) $(VERILATION)/V$(TARGET)__ALL.a -o $@ $(LINKER_FLAGS)

verilate: $(CPP_SOURCES)
	$(VERILATOR) $(VERILATOR_FLAGS) $(VERILOG_INCLUDES) ../$(TARGET).v $(VERILOG_DEFS)
	$(MAKE) -j$(NPROC) -f V$(TARGET).mk -C $(VERILATION)

verilate_trace: $(CPP_SOURCES)
	$(VERILATOR) $(VERILATOR_FLAGS_TRACE) $(VERILOG_INCLUDES) ../$(TARGET).v $(VERILOG_DEFS)
	$(MAKE) -j$(NPROC) OPT_FAST="-O3 -march=native" -f V$(TARGET).mk -C $(VERILATION)

verilate_debug: $(CPP_SOURCES)
	$(VERILATOR) $(VERILATOR_FLAGS_TRACE) $(VERILOG_INCLUDES) ../$(TARGET).v $(VERILOG_DEFS) -CFLAGS "-g"
	$(MAKE) OPT_GLOBAL="-O0" -f V$(TARGET).mk -C $(VERILATION)

verilate_lint: $(CPP_SOURCES)
	$(VERILATOR) --lint-only -Wpedantic $(VERILATOR_FLAGS) $(VERILOG_INCLUDES) ../$(TARGET).v $(VERILOG_DEFS)

run:
	./$(BUILD)/$(TARGET)

view:
	gtkwave $(TRACE_FILE)

clean:
	rm -rf $(BUILD)
