#!/usr/bin/python3

import tempfile
import subprocess
from functools import total_ordering
import requests
import threading
import queue
import os
import configparser
import re
import datetime
import pytz

REPO_DIR = "/etc/zypp/repos.d/"


kid = "gpg-pubkey-29b700a4"
pem = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: rpm-4.17.1 (NSS-3)

mQINBGKwfiIBEADe9bKROWax5CI83KUly/ZRDtiCbiSnvWfBK1deAttV+qLTZ006
090eQCOlMtcjhNe641Ahi/SwMsBLNMNich7/ddgNDJ99H8Oen6mBze00Z0Nlg2HZ
VZibSFRYvg+tdivu83a1A1Z5U10Fovwc2awCVWs3i6/XrpXiKZP5/Pi3RV2K7VcG
rt+TUQ3ygiCh1FhKnBfIGS+UMhHwdLUAQ5cB+7eAgba5kSvlWKRymLzgAPVkB/NJ
uqjz+yPZ9LtJZXHYrjq9yaEy0J80Mn9uTmVggZqdTPWx5CnIWv7Y3fnWbkL/uhTR
uDmNfy7a0ULB3qjJXMAnjLE/Oi14UE28XfMtlEmEEeYhtlPlH7hvFDgirRHN6kss
BvOpT+UikqFhJ+IsarAqnnrEbD2nO7Jnt6wnYf9QWPnl93h2e0/qi4JqT9zw93zs
fDENY/yhTuqqvgN6dqaD2ABBNeQENII+VpqjzmnEl8TePPCOb+pELQ7uk6j4D0j7
slQjdns/wUHg8bGE3uMFcZFkokPv6Cw6Aby1ijqBe+qYB9ay7nki44OoOsJvirxv
p00MRgsm+C8he+B8QDZNBWYiPkhHZBFi5GQSUY04FimR2BpudV9rJqbKP0UezEpc
m3tmqLuIc9YCxqMt40tbQOUVSrtFcYlltJ/yTVxu3plUpwtJGQavCJM7RQARAQAB
tDRvcGVuU1VTRSBQcm9qZWN0IFNpZ25pbmcgS2V5IDxvcGVuc3VzZUBvcGVuc3Vz
ZS5vcmc+iQI+BBMBAgAoBQJisH4iAhsDBQkHhM4ABgsJCAcDAgYVCAIJCgsEFgID
AQIeAQIXgAAKCRA1ovhuKbcApKRrEACJMhZhsPJBOkYmANvH5mqlk27brA3IZoM4
8qTzERebzKa0ZH1fgRI/3DhrfBYL0M5XOb3+26Ize0pujyJQs61Nlo1ibtQqCoyu
dvP/pmY1/Vr374wlMFBuCfAjdad4YXkbe7q7GGjo6cF89qtBfTqEtaRrfDgtPLx/
s9/WXLGo0XYqCCSPVoU66jQYNcCt3pH+hqytvntXJDhU+DveOnQCOSBBHhCMST3E
QvriN/GnHf+sO19UmPpyHH0TM5Ru4vDrgzKYKT/CzbllfaJSk9cEuTY8Sv1sP/7B
Z7YvOE0soIgM1sVg0u3R/2ROx0MKoLcq7EtLw64eE+wnw9bHYZQNmS+J/18p7Bo8
I7e+8WRi+m/pus5FEWsIH1uhxKLgJGFDTHHGZtW+myjnUzXVIkpJGrKoolzYjHdK
lRYM2fVuNI1eq6CZ6PFXg2UxovVczSnGMO33HZE09vpgkRDBrw1vF0o/Wnm02kig
V6xYHk5wJx8vL74wPvCbw73UNT9OSdxYAz7JPqGOD6cpKe7XcAH2sYmlGpggAIUz
Rq/lROEF5lx4SxB838JU4ezxD++BJXfBTE8JZmlGscXv74y9nCtSOZza8KOKj8ou
WRl739FMnx9jRd7HHj3TIyymoveODnZ7f3IElyyFsjBW3XuQ9XfpZrIkwHuaZV5M
6q2h+hgWNQ==
=nMh8
-----END PGP PUBLIC KEY BLOCK-----
"""

keys_download_queue = queue.Queue()

def key_download_queue_handler():
	while True:
		key_url, key_list = keys_download_queue.get()
		pem = requests.get(key_url).text
		key_list.extend(RPMKey.keys_from_pem(pem))
		keys_download_queue.task_done()
for i in range(15):
	threading.Thread(target=key_download_queue_handler, daemon=True).start()


@total_ordering
class RPMKey(object):
	_repo_keys_cache = {}
	@classmethod
	def keys_from_pem(cls, pem):
		"""
			Gets all keys from pem and returns an iterable
		"""
		for askey in pem.split('-----BEGIN PGP PUBLIC KEY BLOCK-----')[1:]:
			yield cls(None, '-----BEGIN PGP PUBLIC KEY BLOCK-----' + askey)

	@classmethod
	def keys_from_rpmdb(cls):
		"""
			Gets all keys from rpmdb and returns an iterable
		"""
		s = subprocess.check_output(["rpm", "-q", "gpg-pubkey", "--qf",
			'%{NAME}-%{VERSION}\n%{PACKAGER}\n%{INSTALLTIME}\n%{DESCRIPTION}\nSPLIT-TOKEN-TO-TELL-KEY-PACKAGES-APART\n'])
		for raw_kpkg in s.decode().strip().split("SPLIT-TOKEN-TO-TELL-KEY-PACKAGES-APART"):
			raw_kpkg = raw_kpkg.strip()
			if not raw_kpkg:
				continue
			kid, name, added, pubkey = raw_kpkg.strip().split("\n", 3)
			yield cls(kid, pubkey, int(added))

	@classmethod
	def keys_from_repos(cls):
		"""
			Gets keys for each repo and returns a dict of lists of keys
		"""
		if cls._repo_keys_cache:
			return cls._repo_keys_cache
		repokeys = {}
		for repo_file in os.listdir(REPO_DIR):
			if not repo_file.endswith('.repo'):
				continue
			try:
				cp = configparser.ConfigParser()
				cp.read(os.path.join(REPO_DIR, repo_file))
				mainsec = cp.sections()[0]
				if not bool(int(cp.get(mainsec, "enabled"))):
					continue
				name = re.sub(r"\.repo$", "", repo_file)
				if cp.has_option(mainsec, "gpgkey"):
					gpgkey_url = cp.get(mainsec, "gpgkey")
					repokeys[name] = []
					keys_download_queue.put((gpgkey_url, repokeys[name]))
			except Exception as e:
				print("Error parsing '%s': %r" % (repo_file, e))
		# wait for threads
		keys_download_queue.join()
		cls._repo_keys_cache = repokeys
		return repokeys

	def __init__(self, kid, pem, added=None):
		self.kid = kid
		self.pem = pem
		self.uid = None
		self.fingerprints = []
		self.added = None
		for line in subprocess.check_output(["gpg", "--quiet", "--show-keys", "--with-colons", "-"],
			input=self.pem.encode()).decode().strip().split("\n"):
			if line.startswith("uid:"):
				self.uid = line.split(':')[9].replace('\\x3a', ':')
			if line.startswith("fpr:"):
				self.fingerprints.append(line.split(':')[9])
		assert self.uid
		assert self.fingerprints and self.fingerprints[0]
		if not self.kid:
			self.kid = f"gpg-pubkey-{self.fingerprints[0][-8:].lower()}"
		if added:
			dt = datetime.datetime.utcfromtimestamp(added)
			self.added = dt.replace(tzinfo=pytz.timezone('UTC')).astimezone()

	
	def import_to_rpmdb(self):
		tf = tempfile.NamedTemporaryFile('w')
		tf.file.write(self.pem)
		tf.file.flush()
		subprocess.call(['sudo', 'rpm', '--import', tf.name])
		tf.file.close()
		type(self)._repo_keys_cache = {}
	
	def remove_from_rpmdb(self):
		subprocess.call(['sudo', 'rpm', '-e', self.kid])
		type(self)._repo_keys_cache = {}
	
	def is_in_rpmdb(self):
		return self in type(self).keys_from_rpmdb()
	
	def used_by_repos(self):
		"""
			Returns an iterable of all repos using this key
		"""
		for repo, keys in type(self).keys_from_repos().items():
			if self in keys:
				yield repo

	def __repr__(self):
		return f"<RPMKey({self.kid}, {self.fingerprints[0]}, {self.uid!r})>"
	
	def __eq__(self, other):
		if not isinstance(other, RPMKey):
			raise NotImplemented
		return (self.uid, self.fingerprints) == (other.uid, other.fingerprints)
	
	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other):
		if not isinstance(other, RPMKey):
			raise NotImplemented
		return self.uid < other.uid


def rpms_by_key(key):
	# this command outputs the last 16 hex digits of the fingerprint
	fp16s = [fingerprint[-16:].lower() for fingerprint in key.fingerprints]
	for pkgline in subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME}-%{VERSION}-%{RELEASE} %{SIGPGP:pgpsig}\n']).decode().split("\n"):
		pkgline = pkgline.split(' ')
		pkg = pkgline[0]
		package_key_id = pkgline[-1]
		if package_key_id in fp16s:
			yield pkg



# https://unix.stackexchange.com/questions/17368/how-do-i-tell-which-gpg-key-an-rpm-package-was-signed-with
# rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE} %{SIGPGP:pgpsig}\n'
