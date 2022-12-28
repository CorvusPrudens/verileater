
#include <cstdio>

#include "Veater.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

#include "eater_display.h"

#define CLOCK_FREQUENCY 1024

#define CLOCK_SECS (1. / CLOCK_FREQUENCY)

#define CLOCK_NS CLOCK_SECS * 1e9
#define CLOCK_PS CLOCK_SECS * 1e12

void tick(Veater* tb, VerilatedVcdC *tfp, unsigned logicStep)
{

    tb->clk_i = 0;
    tb->eval();

    #ifdef TRACE
        if (tfp) tfp->dump(logicStep * CLOCK_PS - CLOCK_PS*0.2);
    #endif

    tb->clk_i = 1;
    tb->eval();

    #ifdef TRACE
        if (tfp){
        tfp->dump(logicStep * CLOCK_PS + CLOCK_PS*0.5);
        tfp->flush();
        }
    #endif
}

int main(int argc, char** argv)
{
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    Veater *tb = new Veater;
    VerilatedVcdC* tfp = new VerilatedVcdC;

    EaterDisplay<600, 300, 5> display(
        CLOCK_FREQUENCY,
        tb->seven_seg_o,
        tb->seven_seg_com_o
    );

    uint32_t logicStep = 0;

    #ifdef TRACE
        tb->trace(tfp, 99);
        tfp->open("trace.vcd");
    #endif

    tb->reset_i = 1;
    tick(tb, tfp, ++logicStep);
    tb->reset_i = 0;
    tick(tb, tfp, ++logicStep);

    for (int i = 0; i < 65536; i++)
    {
        tick(tb, tfp, ++logicStep);
        display.Process();
    }

    tb->final();
    delete tb;
    delete tfp;
}
