import os

TEMP_DIR = os.path.join(os.path.dirname(__file__),"temp")
if not os.path.exists(TEMP_DIR):
	os.path.mkdir(TEMP_DIR)