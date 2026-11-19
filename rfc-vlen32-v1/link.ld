OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS
{
    . = 0x80000000;
    .text : { *(.text.init) *(.text*) }
    . = ALIGN(4096);
    .data : { *(.rodata*) *(.sdata*) *(.data*) }
    .bss : { *(.sbss*) *(.bss*) *(COMMON) }
}
