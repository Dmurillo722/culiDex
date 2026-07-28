# ============================================================================
# CuliDex — build / install / run
# Target platforms: WSL2 (Windows), Ubuntu 22.04, Linux Mint 21.3 Cinnamon
#
# Required toolchain (hard-checked by `make check`):
#   C compiler : GCC 13.x/15.x   OR   Clang 20.x/21.x
#   Python     : 3.12.x or 3.14.x
#   Rust       : 1.91.x, 1.93.x, or 1.95.x (rustc/cargo)
# ============================================================================

SHELL := /bin/bash
VENV  := venv
.PHONY: all help check build install run package rebuild-seed-db dist clean

all: build

help:
	@echo "make check           - verify required GCC/Clang/Python/Rust versions"
	@echo "make build           - dev build: venv + deps + maturin develop"
	@echo "make install         - release path: builds a wheel and 'pip install's it"
	@echo "make run             - run the app (dev build)"
	@echo "make package         - build an installable wheel (dist/*.whl) for release"
	@echo "make rebuild-seed-db - regenerate the bundled seed database from source CSVs"
	@echo "make dist            - build a submission-ready tgz archive"
	@echo "make clean           - remove venv/build artifacts"


check:
	@python3 scripts/check_toolchain.py

.toolchain.env: scripts/check_toolchain.py
	@python3 scripts/check_toolchain.py

build: .toolchain.env
	@set -a && . ./.toolchain.env && set +a && \
	$$PYTHON -m venv $(VENV) && \
	source $(VENV)/bin/activate && \
	pip install --upgrade pip && \
	pip install -r dependencies && \
	CC=$$CC RUSTFLAGS="-C linker=$$CC" maturin develop --release

install: .toolchain.env
	@set -a && . ./.toolchain.env && set +a && \
	$$PYTHON -m venv $(VENV) && \
	source $(VENV)/bin/activate && \
	pip install --upgrade pip && \
	CC=$$CC RUSTFLAGS="-C linker=$$CC" pip install .
	@echo "Installed. From any directory: source $(VENV)/bin/activate && culidex"

run:
	@source $(VENV)/bin/activate && culidex

# Builds a distributable installation package (wheel) for the target systems
# (WSL2 Ubuntu, Ubuntu 22.04, Linux Mint 21.3). Upload dist/*.whl to a GitHub
# Release and link it from README.md.
package: .toolchain.env
	@set -a && . ./.toolchain.env && set +a && \
	$$PYTHON -m venv $(VENV) && \
	source $(VENV)/bin/activate && \
	pip install --upgrade pip maturin && \
	CC=$$CC RUSTFLAGS="-C linker=$$CC" maturin build --release --out dist
	@echo "Installation package built: dist/*.whl"
	@echo "Upload this wheel to a GitHub Release and link it in README.md"

# Dev-only: rebuild the writable runtime DB from the source CSVs, then copy it
# back into the package as the new bundled seed for future builds.
rebuild-seed-db:
	@source $(VENV)/bin/activate && \
	python -c "from culidex_app.db import load_csv_to_db; load_csv_to_db()" && \
	python -c "from culidex_app.db import DB_PATH; import shutil; shutil.copy(DB_PATH, 'python/culidex_app/data/data.db')" && \
	echo "Seed database refreshed at python/culidex_app/data/data.db"

dist:
	tar --exclude='venv' --exclude='.venv' --exclude='target' --exclude='.git' \
	    --exclude='__pycache__' --exclude='.DS_Store' --exclude='tempData' \
	    --exclude='data/FoodData_Central_foundation_food_json_2026-04-30.json' \
	    --exclude='data/FoodData_Central_sr_legacy_food_json_2018-04.json' \
	    -czf ../culidex-submission.tgz -C .. "$$(basename "$$(pwd)")"

clean:
	rm -rf $(VENV) target build dist *.egg-info .toolchain.env
	find . -name '__pycache__' -exec rm -rf {} +
