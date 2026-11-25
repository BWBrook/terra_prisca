# Builds the haze-world paper's products through makedoc 2 (https://github.com/BWBrook/makedoc),
# pinned by the tag in MAKEDOC. Run from the repository root as
# `make -C models/haze_world/paper/products [target]`.
MAKEDOC := uvx --from git+https://github.com/BWBrook/makedoc@v2.0.1 makedoc
ROOT := ../../../..
LEDGER := ../../synthesis/claims.csv
DOCS := ../esm/esm.md text/main.md text/figures.md text/brief.md text/for-agents.md

.PHONY: all main supplement brief check check-render

all: main supplement brief
	@$(MAKE) --no-print-directory check-render

main:
	$(MAKEDOC) build -p main --strict

supplement:
	$(MAKEDOC) build -p supplement --strict

brief:
	$(MAKEDOC) build -p brief --strict

check:
	cd $(ROOT) && python3 tools/claims.py check models/haze_world/synthesis/claims.csv $(addprefix models/haze_world/paper/,$(subst ../,,$(filter ../%,$(DOCS)))) $(addprefix models/haze_world/paper/products/,$(filter text/%,$(DOCS)))
	$(MAKEDOC) check --all

check-render:
	python3 $(ROOT)/tools/check_render.py --brief build/brief.pdf
