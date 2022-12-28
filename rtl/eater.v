`ifndef DEFAULT_INSTR_HEX
`define DEFAULT_INSTR_HEX "hex/instructions.hex"
`endif

`ifndef DEFAULT_OUTPUT_HEX
`define DEFAULT_OUTPUT_HEX "hex/output.hex"
`endif

`ifndef DEFAULT_PROGRAM_HEX
`define DEFAULT_PROGRAM_HEX "build/program.hex"
`endif

module eater #(
        parameter RESET_PC        = 0,
        parameter INSTRUCTION_HEX = `DEFAULT_INSTR_HEX,
        parameter OUTPUT_HEX      = `DEFAULT_OUTPUT_HEX,
        parameter PROGRAM_HEX     = `DEFAULT_PROGRAM_HEX,
        parameter OUTPUT_DIVIDE   = 1
    ) 
    (
        input wire clk_i,
        input wire reset_i,

        output wire [7:0] seven_seg_o,
        output wire [3:0] seven_seg_com_o
    );

    ///////////////////////////////
    // Control Signals
    ///////////////////////////////

    // This is a technique called double-flopping. It helps
    // prevent glitches when a signal crosses what you might
    // call a "clock domain" (i.e. cross-domain-clocking).
    // Since the reset input would likely be a button,
    // it's not syncronized to the system clock, and
    // should therefore be double-flopped.
    reg [1:0] reset_cdc;
    always @(posedge clk_i) begin
        reset_cdc[0] <= reset_i;
        reset_cdc[1] <= reset_cdc[0];
    end

    wire reset = reset_cdc[1]; // CLR
    wire c_halt;               // HLT
    wire c_memory_in;          // ~MI
    wire c_ram_in;             // RI
    wire c_ram_out;            // ~RO
    wire c_instruction_out;    // ~IO
    wire c_instruction_in;     // ~II
    wire c_a_in;               // ~AI
    wire c_a_out;              // ~AO
    wire c_sum_out;            // ~EO
    wire c_subtract;           // SU
    wire c_b_in;               // ~BI
    wire c_output_in;          // OI
    wire c_counter_enable;     // CE
    wire c_counter_out;        // ~CO
    wire c_jump;               // ~J
    wire c_flags_in;           // ~FI

    wire [7:0] bus;

    ///////////////////////////////
    // Program Counter
    ///////////////////////////////

    reg [3:0] program_counter;

    always @(posedge clk_i) begin
        if (reset)
            program_counter <= RESET_PC;
        else if (c_jump)
            program_counter <= bus[3:0];
        else if (c_counter_enable)
            program_counter <= program_counter + 1'b1;
    end

    ///////////////////////////////
    // ALU (and flags)
    ///////////////////////////////

    reg [7:0] a_reg;
    reg [7:0] b_reg;

    // A 9-bit sum register allows us to easily get at the
    // carry-out signal of this adder (sum_reg[8]). It also 
    // means we need to use 9-bit operands if we want to be
    // totally explicit.
    wire [8:0] sum_reg = c_subtract   ? 
        {1'b0, a_reg} - {1'b0, b_reg} :
        {1'b0, a_reg} + {1'b0, b_reg} ;

    always @(posedge clk_i) begin
        if (reset) begin
            a_reg <= 0;
            b_reg <= 0;
        end else begin
            if (c_a_in)
                a_reg <= bus;
            
            if (c_b_in)
                b_reg <= bus;
        end
    end

    reg flag_zero;
    reg flag_carry;

    always @(posedge clk_i) begin
        if (reset) begin
            flag_zero  <= 1'b0;
            flag_carry <= 1'b0;
        end else if (c_flags_in) begin
            // One of the nice features of verilog is the
            // ability to describe logic in a behavioral way.
            // Rather than describing chains of OR operations,
            // we can simply make a higher-level arithmetic assertion.
            flag_zero  <= sum_reg[7:0] == 0;
            flag_carry <= sum_reg[8];
        end
    end
    
    ///////////////////////////////
    // Memory
    ///////////////////////////////

    reg [7:0] ram [15:0];
    reg [3:0] ram_address;

    reg [7:0] ram_output;

    // Verilator doesn't like coercing a string into a
    // boolean expression, so the width warning is turned off.
    // yosys can have issues with synthesizing ROMs if the
    // module doesn't have a valid path in its file.
    // verilator lint_off WIDTH
    initial if (PROGRAM_HEX) $readmemh(PROGRAM_HEX, ram);
    // verilator lint_on WIDTH

    always @(posedge clk_i) begin
        if (c_memory_in)
            ram_address <= bus[3:0];
    end

    always @(posedge clk_i) begin
        if (c_ram_in)
            ram[ram_address] <= bus;
        
        ram_output <= ram[ram_address];
    end

    ///////////////////////////////
    // Output
    ///////////////////////////////

    // This block mimics the behavior of Ben Eater's
    // muxed display, with the addition of a
    // clock divider in case the system clock is
    // in the MHz.

    reg [7:0] output_reg;
    reg [3:0] output_com_reg;
    reg [1:0] output_mux;

    always @(posedge clk_i) begin
        if (reset)
            output_reg <= 0;
        else if (c_output_in)
            output_reg <= bus;
    end

    wire [9:0] output_address = {output_mux, output_reg};
    reg  [7:0] output_memory [(2**10)-1:0];
    reg  [7:0] output_memory_out;

    // verilator lint_off WIDTH
    initial if (OUTPUT_HEX) $readmemh(OUTPUT_HEX, output_memory);
    // verilator lint_on WIDTH

    always @(posedge clk_i) begin
        output_memory_out <= output_memory[output_address];
        output_com_reg <= 4'b0001 << output_mux;
    end

    assign seven_seg_o     = output_memory_out;
    assign seven_seg_com_o = output_com_reg;

    reg [OUTPUT_DIVIDE:0] output_divide;

    always @(posedge clk_i) begin
        output_divide <= output_divide[OUTPUT_DIVIDE-1:0] + 1'b1;

        if (output_divide[OUTPUT_DIVIDE])
            output_mux <= output_mux + 1'b1;
    end

    ///////////////////////////////
    // Control Logic
    ///////////////////////////////

    reg [7:0] instruction_reg;
    reg [2:0] micro_instruction;
    reg       halt;

    wire [3:0] opcode = instruction_reg[7:4];

    always @(posedge clk_i) begin
        if (reset)
            instruction_reg <= 0;
        else if (c_instruction_in)
            instruction_reg <= bus;
    end
        
    wire [8:0]  instruction_address;
    reg  [15:0] instruction_memory [(2**9)-1:0];
    reg  [15:0] instruction_out;

    always @(posedge clk_i)
        instruction_out <= instruction_memory[instruction_address];

    // verilator lint_off WIDTH
    initial if (INSTRUCTION_HEX) $readmemh(INSTRUCTION_HEX, instruction_memory);
    // verilator lint_on WIDTH

    assign instruction_address = {flag_zero, flag_carry, opcode, micro_instruction};

    reg instruction_ready;

    always @(posedge clk_i) begin
        if (reset | halt) begin
            instruction_ready <= 1'b0;
            micro_instruction <= 0;
        end else if (instruction_ready == 0) begin
            instruction_ready <= 1'b1;
        end else begin
            instruction_ready <= 1'b0;
            micro_instruction <= micro_instruction + 1'b1;
        end
    end

    // The halt signal is separately registered so that
    // any change to the control state machine (and instruction address)
    // does not immediately deassert the halt.
    always @(posedge clk_i) begin
        if (reset)
            halt <= 1'b0;
        else if (c_halt)
            halt <= 1'b1;
    end

    // In Verilog, vectors like this can be manipulated
    // like regular variables, which is really nice.
    assign {
        c_sum_out,
        c_subtract,
        c_b_in,
        c_output_in,
        c_counter_enable,
        c_counter_out,
        c_jump,
        c_flags_in,
        c_halt,
        c_memory_in,
        c_ram_in,
        c_ram_out,
        c_instruction_out,
        c_instruction_in,
        c_a_in,
        c_a_out
    } = instruction_ready ? instruction_out : 16'b0;

    ///////////////////////////////
    // Bus Management
    ///////////////////////////////

    // This ORed mux mostly mimics the behavior of the
    // Ben Eater bus, excluding actual tri-state interactions.
    // Tri-state buffers are generally not supported within the
    // fabric of an FPGA.
    assign bus =
        (c_ram_out         ? ram_output                   : 8'b0) |
        (c_instruction_out ? {4'b0, instruction_reg[3:0]} : 8'b0) |
        (c_a_out           ? a_reg                        : 8'b0) |
        (c_sum_out         ? sum_reg[7:0]                 : 8'b0) |
        (c_counter_out     ? {4'b0, program_counter}      : 8'b0) ;

endmodule
