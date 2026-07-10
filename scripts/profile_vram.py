import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from scripts.notebook_code import run_system_check, run_notebook_test_suite

if __name__ == "__main__":
    run_system_check()
    run_notebook_test_suite()
