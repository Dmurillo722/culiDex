# CuliDex

## Description
CuliDex is an ingredient substitution engine that helps users find substitutes for
ingredients that may not be locally available when outside their home country. It
pairs a Python/Tkinter (customtkinter) desktop GUI with a Rust extension module
(built with PyO3 + maturin) that performs the cosine-similarity ranking used to
match ingredients.

## Repository
https://github.com/Dmurillo722/culiDex

## Build
One-line build command, run from the project root:

    make build


## Install (release / single-command)
    make install

Runs toolchain check and `pip install .`, which builds the Rust extension
and installs the whole project — including the `culidex_app` Python package and
its runtime dependencies — as a single package.

## Installation Package Executable (Desktop)
[TODO: link to the released wheel]

Built for the target systems (WSL2 Ubuntu, Ubuntu 22.04, Linux Mint 21.3) with:

    make package

Produces a wheel at `dist/culidex-<version>-<tag>.whl`. Install it directly on
any of the target systems with a single command:

    pip install dist/culidex-<version>-<tag>.whl

## Run
One-line run command, from the project root, after building:

    make run

This activates the virtualenv and runs `culidex`. 

## Development
After changing Rust code in `src/lib.rs`, rerun:

    make build

To rebuild the bundled seed database from the source CSVs
(`data/japan_foods.csv`, `data/starting_database.csv`) and refresh the copy. Can be updated in the future when adding new data.
shipped in the package:

    make rebuild-seed-db

## Submission Packaging
    make dist

Builds `../culidex-submission.tgz`, excluding build artifacts (`venv/`,
`target/`, `.git/`, `__pycache__/`) and the raw FoodData_Central source JSON files under `data/`.
