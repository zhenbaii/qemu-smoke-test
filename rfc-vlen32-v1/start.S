/* Local diagnostic startup, separate from the C vector computation. */
.option norvc
.option norelax
.section .text.init,"ax",@progbits
.globl _start
_start:
    la sp, stack_top
    la t0, trap
    csrw mtvec, t0
    li t0, 0x600
    csrs mstatus, t0
    call main
1:  wfi
    j 1b
.align 2
trap:
    call trap_handler
    j 1b
.section .bss,"aw",@nobits
.align 4
    .space 16384
stack_top:
