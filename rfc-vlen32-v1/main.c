/* Local bare-metal diagnostic harness; not an upstream contribution. */
#include <stdint.h>
#include <stddef.h>

static void puts_uart(const char *text)
{
    volatile uint8_t *uart = (volatile uint8_t *)0x10000000UL;
    while (*text) {
        while (!(uart[5] & 0x20)) {
        }
        uart[0] = (uint8_t)*text++;
    }
}

static void hex_uart(uint32_t value)
{
    char text[9];
    const char *digits = "0123456789abcdef";
    for (unsigned int i = 0; i < 8; ++i) {
        text[i] = digits[(value >> (28 - 4 * i)) & 15];
    }
    text[8] = 0;
    puts_uart(text);
}

__attribute__((noreturn))
static void finish(unsigned int error)
{
    *(volatile uint32_t *)0x100000UL = error ? (error << 16) | 0x3333 : 0x5555;
    for (;;) {
        __asm__ volatile("wfi");
    }
}

__attribute__((noreturn))
void trap_handler(void)
{
    uintptr_t cause, pc;
    __asm__ volatile("csrr %0, mcause" : "=r"(cause));
    __asm__ volatile("csrr %0, mepc" : "=r"(pc));
    puts_uart("TRAP cause=");
    hex_uart((uint32_t)cause);
    puts_uart(" pc=");
    hex_uart((uint32_t)pc);
    puts_uart("\n");
    finish(125);
}

int main(void)
{
    uint32_t actual, expected;
    extern uint32_t auto_stats(const uint32_t *, const uint32_t *, size_t);
    static const uint32_t left[] = { 1, 2, 3, 4 };
    static const uint32_t right[] = { 10, 20, 30, 40 };
    puts_uart("BEGIN Zve32x plain C sum and minimum\n");
    actual = auto_stats(left, right, 4);
    expected = 40;
    puts_uart("actual=0x");
    hex_uart(actual);
    puts_uart(" expected=0x");
    hex_uart(expected);
    puts_uart(actual == expected ? " PASS\n" : " FAIL\n");
    finish(actual == expected ? 0 : 1);
}
