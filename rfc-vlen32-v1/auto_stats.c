/* Plain C diagnostic: GCC, not this source, selects vector instructions. */
#include <stddef.h>
#include <stdint.h>

__attribute__((noinline, noclone))
uint32_t auto_stats(const uint32_t *left, const uint32_t *right, size_t count)
{
    uint32_t sum = 0, minimum = UINT32_MAX;
    for (size_t i = 0; i < count; ++i) {
        sum += left[i];
        if (right[i] < minimum) {
            minimum = right[i];
        }
    }
    return sum + 3 * minimum;
}
