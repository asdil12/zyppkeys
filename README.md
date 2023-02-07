# zypper-keys

This tool allows managing RPM keys.

```
$ zypper keys list
 Key                 | Added               | Vendor
---------------------+---------------------+--------------------------------------------------------------
 gpg-pubkey-17280ddf | 2022-09-23 13:43:42 | network OBS Project <network@build.opensuse.org>
 gpg-pubkey-c862b42c | 2023-01-24 10:51:17 | games OBS Project <games@build.opensuse.org>
 gpg-pubkey-29b700a4 | 2022-09-12 14:11:42 | openSUSE Project Signing Key <opensuse@opensuse.org>
 gpg-pubkey-3dbdc284 | 2022-09-12 14:11:42 | openSUSE Project Signing Key <opensuse@opensuse.org>
 gpg-pubkey-be1229cf | 2022-09-12 14:38:34 | Microsoft (Release signing) <gpgsecurity@microsoft.com>
 gpg-pubkey-8a7c64f9 | 2022-09-28 11:41:27 | Unsupported <unsupported@suse.de>
 gpg-pubkey-cbdf5e8f | 2022-09-27 12:05:36 | devel:openQA OBS Project <devel:openQA@build.opensuse.org>
 gpg-pubkey-edf0d733 | 2022-11-12 14:47:56 | devel:languages:python OBS Project <devel:languages:python@…
 gpg-pubkey-a89c3a8a | 2022-09-28 22:49:49 | devel:languages:nodejs OBS Project <devel:languages:nodejs@…
 gpg-pubkey-d6d11ce4 | 2022-12-27 19:51:28 | hardware OBS Project <hardware@build.opensuse.org>
 gpg-pubkey-72174fc2 | 2023-01-30 10:44:24 | Virtualization OBS Project <Virtualization@build.opensuse.o…
 gpg-pubkey-dcef338c | 2023-01-30 10:44:24 | devel:languages:perl OBS Project <devel:languages:perl@buil…
 gpg-pubkey-65176565 | 2023-01-30 10:44:24 | openSUSE:Backports OBS Project <openSUSE:Backports@build.op…
 gpg-pubkey-f23c6aa3 | 2023-01-30 10:44:24 | multimedia OBS Project <multimedia@build.opensuse.org>
 gpg-pubkey-780504e9 | 2023-01-30 10:44:24 | X11 OBS Project <X11@build.opensuse.org>
 gpg-pubkey-00e006f2 | 2023-01-30 10:44:24 | network:chromium OBS Project <network:chromium@build.opensu…
 gpg-pubkey-33eaab8e | 2023-02-02 00:00:01 | Vivaldi Package Composer KEY09 <packager@vivaldi.com>
 gpg-pubkey-4218647e | 2023-02-06 14:51:10 | Vivaldi Package Composer KEY08 <packager@vivaldi.com>
 ```

 ```
 $ zypper keys repokeys -d
 Repo                             | Key                 | Added | Vendor
----------------------------------+---------------------+-------+-----------------------------------------
 vivaldi                          | gpg-pubkey-4218647e | Yes   | Vivaldi Package Composer KEY08 <packag…
 games                            | gpg-pubkey-c862b42c | Yes   | games OBS Project <games@build.opensus…
 hardware_sdr                     | gpg-pubkey-d6d11ce4 | Yes   | hardware OBS Project <hardware@build.o…
 download.opensuse.org-oss        | gpg-pubkey-29b700a4 | Yes   | openSUSE Project Signing Key <opensuse…
 download.opensuse.org-tumbleweed | gpg-pubkey-3dbdc284 | Yes   | openSUSE Project Signing Key <opensuse…
 devel-openqa                     | gpg-pubkey-cbdf5e8f | Yes   | devel:openQA OBS Project <devel:openQA…
 download.opensuse.org-non-oss    | gpg-pubkey-29b700a4 | Yes   | openSUSE Project Signing Key <opensuse…
 vscode                           | gpg-pubkey-be1229cf | Yes   | Microsoft (Release signing) <gpgsecuri…
 slack                            | gpg-pubkey-038651bd | Yes   | https://packagecloud.io/slacktechnolog…
 ```

 ```
$ zypper keys show gpg-pubkey-29b700a4

Information for key gpg-pubkey-29b700a4:
----------------------------------------
Key          : gpg-pubkey-29b700a4
Added        : 2022-09-12 14:11:42
Vendor       : openSUSE Project Signing Key <opensuse@opensuse.org>
Fingerprints : AD485664E901B867051AB15F35A2F86E29B700A4

```
