# Fixing the `black --check --diff .` GitHub Actions Error

## Why did this error occur?

Your GitHub Actions workflow failed because **Black** (the Python code
formatter) found files that do not follow its formatting rules.

The command being executed was:

``` bash
black --check --diff .
```

-   `--check` checks formatting without modifying files.
-   `--diff` shows the formatting changes Black would make.
-   If any file is not correctly formatted, Black exits with **exit code
    1**, causing the CI workflow to fail.

> **Important:** This is **not a code or logic error**. Your project
> likely works correctly---the formatting simply doesn't match Black's
> style.

------------------------------------------------------------------------

## Files that need formatting

The log indicates these files require formatting:

-   `app/database.py`
-   `scripts/build_router.py`
-   `tests/test_database.py`
-   `scripts/notebook_code.py`

------------------------------------------------------------------------

## Solution

### Option 1 (Recommended): Format the entire project

Run:

``` bash
black .
```

This formats every Python file in the project.

------------------------------------------------------------------------

### Option 2: Format only the affected files

``` bash
black app/database.py scripts/build_router.py tests/test_database.py scripts/notebook_code.py
```

------------------------------------------------------------------------

## After formatting

Commit and push the changes:

``` bash
git add .
git commit -m "Format code using Black"
git push
```

GitHub Actions should pass the Black formatting check on the next run.

------------------------------------------------------------------------

## About the Jupyter warning

You may also see:

``` text
Skipping .ipynb files as Jupyter dependencies are not installed.
```

This is only a warning.

If you want Black to format Jupyter notebooks as well, install:

``` bash
pip install "black[jupyter]"
```

Otherwise, you can safely ignore this warning.

------------------------------------------------------------------------

## Why GitHub Actions failed

Black returns:

-   **Exit Code 0** → All files are correctly formatted ✅
-   **Exit Code 1** → One or more files need formatting ❌

Since your workflow treats any non-zero exit code as a failure, the
GitHub Actions job stopped.

------------------------------------------------------------------------

## Best Practices

-   Run `black .` before every commit.
-   Enable automatic formatting in your editor (VS Code, PyCharm, etc.).
-   Install a pre-commit hook so formatting happens automatically before
    every commit.

Example:

``` bash
pip install pre-commit
pre-commit install
```

Add a `.pre-commit-config.yaml` with Black to automate formatting.

------------------------------------------------------------------------

## Quick Fix Checklist

-   [ ] Run `black .`
-   [ ] Verify there are no formatting changes left
-   [ ] Commit the formatted files
-   [ ] Push to GitHub
-   [ ] Re-run GitHub Actions

Your workflow should now pass the Black formatting stage successfully.
