CROSS_COMPILE ?= riscv64-unknown-elf-
.DELETE_ON_ERROR:
CC = $(CROSS_COMPILE)gcc
OBJDUMP = $(CROSS_COMPILE)objdump
READELF = $(CROSS_COMPILE)readelf

COMMON_FLAGS = -O3 -ffreestanding -fno-builtin -march=rv64im_zicsr_zve32x \
	-mabi=lp64 -mcmodel=medany -mno-relax -msmall-data-limit=0

.PHONY: all
all: build/repro.elf build/repro.dis build/repro.attributes

build:
	mkdir -p $@

build/auto_stats.o: auto_stats.c | build
	$(CC) $(COMMON_FLAGS) -fvect-cost-model=unlimited -c $< -o $@

build/main.o: main.c | build
	$(CC) $(COMMON_FLAGS) -fno-tree-vectorize -fno-tree-slp-vectorize -c $< -o $@

build/start.o: start.S | build
	$(CC) $(COMMON_FLAGS) -c $< -o $@

build/repro.elf: build/start.o build/main.o build/auto_stats.o link.ld
	$(CC) $(COMMON_FLAGS) -nostdlib -nostartfiles -Wl,--build-id=none \
		-T link.ld build/start.o build/main.o build/auto_stats.o -o $@

build/repro.dis: build/repro.elf
	$(OBJDUMP) -d $< > $@
	@grep -q 'vredsum.vs' $@ || { echo 'Compiler did not emit vredsum.vs; see README.md.' >&2; exit 1; }
	@grep -q 'vminu.vv' $@ || { echo 'Compiler did not emit vminu.vv; see README.md.' >&2; exit 1; }

build/repro.attributes: build/repro.elf
	$(READELF) -A $< > $@
