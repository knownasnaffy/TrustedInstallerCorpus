# Project Rules

- **Virtual Environment:** Always create and use a Python virtual environment located at `.venv` in the project root. Do not install packages globally. Run `.venv/bin/pip install` and use `.venv/bin/python` for execution.
- **Dependencies:** Keep dependencies documented in `requirements.txt` or `pyproject.toml`. Update them when installing new packages.
- **Python Version:** Use python3 for commands and assume modern Python (3.9+). Prefer typing annotations.
- **Consistency:** Document major architectural choices in project documentation. Verify code with tests and format/lint before completing tasks.
