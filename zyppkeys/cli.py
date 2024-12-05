import os
import sys
import argparse
from textwrap import dedent

import requests

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/.'))
from zyppkeys import *
from zyppkeys.version import __version__

cli = argparse.ArgumentParser(
	description="Management of RPM signing keys",
	epilog=dedent("""
		The -h option can be used on subcommands as well
		to show the available option flags.
	"""))
cli.add_argument('-v', '--version', action='version', version=(f"{os.path.basename(sys.argv[0])} version {__version__}"))
subparsers = cli.add_subparsers(dest="subcommand")

def argument(*name_or_flags, **kwargs):
	"""Convenience function to properly format arguments to pass to the
	subcommand decorator.
	"""
	return (list(name_or_flags), kwargs)


def subcommand(name, args=[], parent=subparsers):
	"""Decorator to define a new subcommand in a sanity-preserving way.
	The function will be stored in the ``func`` variable when the parser
	parses arguments so that it can be called directly like so::
		args = cli.parse_args()
		args.func(args)
	Usage example::
		@subcommand([argument("-d", help="Enable debug mode", action="store_true")])
		def subcommand(args):
			print(args)
	Then on the command line::
		$ python cli.py subcommand -d
	"""
	def decorator(func):
		parser = parent.add_parser(name, description=func.__doc__, help=func.__doc__)
		for arg in args:
			parser.add_argument(*arg[0], **arg[1])
		parser.set_defaults(func=func)
	return decorator


@subcommand("list", [])
def cmd_list(args):
	"""List keys in RPM database"""
	list_keys(RPMKey.keys_from_rpmdb())


@subcommand("repokeys", [
	argument("-d", "--rpmdb", action="store_true", help="Show if key is in rpmdb"),
	argument("-a", "--add", action="store_true", help="Add keys to rpmdb")
])
def cmd_repokeys(args):
	"""List keys referenced by .repo files"""
	repokeys =  RPMKey.keys_from_repos().items()
	rows = []
	for r, keys in repokeys:
		for k in keys:
			if args.rpmdb:
				rows.append((r, k.kid, 'Yes' if k.is_in_rpmdb() else 'No', k.uid))
			else:
				rows.append((r, k.kid, k.uid))
	if args.rpmdb:
		print_table(["Repo", "Key", "Added", "Vendor"], rows, limit_col=3)
	else:
		print_table(["Repo", "Key", "Vendor"], rows, limit_col=2)
	if args.add:
		for r, keys in repokeys:
			for key in keys:
				if not key.is_in_rpmdb():
					print(f"Adding key {key.kid!r} ({key.uid})")
					key.import_to_rpmdb()


@subcommand("show", [
	argument("-r", "--repos", action="store_true", help="List repos using this key"),
	argument("-p", "--pem", action="store_true", help="Show key PEM"),
	argument("kid", help="Key id")
])
def cmd_show(args):
	"""Show RPM key details"""
	keys = [k for k in RPMKey.keys_from_rpmdb() if k.kid == args.kid]
	if keys:
		show_key(keys[0], pem=args.pem, repos=args.repos)
	else:
		print(f"ERROR: Key {args.kid!r} not found")
		sys.exit(1)


@subcommand("add", [argument("key", help="URL, path or '-' for STDIN of PEM formatted key")])
def cmd_add(args):
	"""Add RPM key"""
	if args.key == '-':
		pem = sys.stdin.read()
	elif args.key.startswith('http://') or args.key.startswith('https://'):
		r = requests.get(args.key)
		r.raise_for_status()
		pem = r.text
	elif os.path.isfile(args.key):
		pem = open(args.key, 'r').read()
	else:
		pem = ""
	no_key_found = True
	for key in RPMKey.keys_from_pem(pem):
		no_key_found = False
		print(f"Adding key {key.kid!r} ({key.uid})")
		key.import_to_rpmdb()
	if no_key_found:
		print("ERROR: No key found")


@subcommand("remove", [
	argument("kid", help="Key id"),
	argument("-r", "--repos", action="store_true", help="Keep keys that are referenced by a .repo file")
])
def cmd_remove(args):
	"""Remove RPM key"""
	keys = [k for k in RPMKey.keys_from_rpmdb() if k.kid == args.kid]
	if keys:
		key = keys[0]
		if args.repos and list(key.used_by_repos()):
			print(f"Keeping key {key.kid!r} ({key.uid}) used by repos {', '.join(key.used_by_repos())}")
		else:
			print(f"Removing key {key.kid!r} ({key.uid})")
			key.remove_from_rpmdb()
	else:
		print(f"ERROR: Key {args.kid!r} not found")
		sys.exit(1)


def entry():
	args = cli.parse_args()
	if args.subcommand is None:
		cli.print_help()
	else:
		args.func(args)
