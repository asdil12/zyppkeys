
import tempfile
import subprocess
from functools import total_ordering
import requests
import threading
import queue
import os
import sys
import configparser
import re
import datetime
import pytz

REPO_DIR = "/etc/zypp/repos.d/"

keys_download_queue = queue.Queue()
tplock = threading.Lock()

def key_download_queue_handler():
	while True:
		key_url, key_list = keys_download_queue.get()
		try:
			pem = requests.get(key_url).text
			key_list.extend(RPMKey.keys_from_pem(pem))
		except Exception as e:
			tplock.acquire()
			print(f"Error fetching {key_url!r}: {e}", file=sys.stderr)
			tplock.release()
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
