import sys
import os

# ensure `src` is on sys.path so imports like `from uictlapi import cli` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

