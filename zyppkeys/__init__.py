import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/.'))
from keys import *
from table import *

def format_timestamp(dt):
	return dt.strftime("%Y-%m-%d %H:%M:%S")

def list_keys(keys):
	print_table(["Key", "Added", "Vendor"], [
		(k.kid, format_timestamp(k.added), k.uid) for k in keys
	], limit_col=2)


def show_key(key, pem=False, repos=False):
	print()
	print_table([f"Information for key {key.kid}:"], rows=[], outer_space=False)
	rows = [
		('Key', key.kid),
		('Added', format_timestamp(key.added)),
		('Vendor', key.uid),
		('Fingerprints', key.fingerprints),
	]
	if repos:
		r = list(key.used_by_repos())
		if r:
			rows.append(('Repos', ', '.join(r)))
	if pem:
		rows.append(('PEM', key.pem.split("\n")))
	print_table([], rows,
	    separator=':', outer_space=False, separator_on_extra_rows=False, limit_col=1)
	print()
