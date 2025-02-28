
import streamlit as st
import importlib
import sys
import os

# Add the current directory to the path so Python can find our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Redirect to the valuation page
from pages.valuation import *
