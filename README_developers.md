# FBI Crime Data API (Developers Only)

`fbi-data-api` is packaged with `uv`, an extremely fast environment management tool that configures both *Python* and *Python library* versions. The only requirement of `uv` is that your system Python must be >= 3.8. There is a two-step process to set up `fbi-data-api` for local development.
1. Using your system pip, do `pip install uv`. Do `uv --version` to verify installation. 
1. From the repo's root directory, do `uv sync --dev` to create a virtual environment `.venv`.
   - The `fbi-data-api` package in this environent is in editable mode, so any changes you make will immediately persist.
   - `ipykernel` is already installed, so feel free to test your changes interactively in a Jupyter notebook (e.g., `./examples/`).

You can now work with `fbi-data-api` as a developer! Do `uv run python path/to/your/file.py` to run Python files. Alternatively (my preference), activate the `.venv` and do `python path/to/your/file.py` as usual.

Lastly, ignore `./ad_hoc/`. The scripts in this directory are for my own invocation only, such as publishing my package to PyPi and tracking daily PyPi downloads through GitHub Actions.
