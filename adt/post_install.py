#!/usr/bin/python
# _*_ coding: utf-8 _*_

import errno
import importlib
import os
import shutil
from glob import glob

try:
    is_admin = os.getuid() == 0
except AttributeError:
    is_admin = 1

if not is_admin:
    raise RuntimeError(
        "post_install::is_admin : (RuntimeError) run as root or administrator."
    )


def make_dirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):  # exist_ok
            pass


def copy_files(src, dst):
    for file in glob(src):
        if not os.path.exists(os.path.join(dst, os.path.basename(file))):
            shutil.copy2(file, dst)


os_symlink: object = getattr(os, "symlink", None)

if is_admin:
    working_root = "/"
else:
    working_root = os.path.join(os.path.expanduser("~"), "adt")

installed_package_name = "adt"
print(f"post_install::initialize : (installed_package_name: {installed_package_name})")
print(f"initialize ")

package_path, _ = os.path.split(
    importlib.import_module(installed_package_name).__file__
)

print(f"post_install::package_path : {package_path}")

# create packages symbolic link
if is_admin:
    program_path = os.path.join(working_root, "opt", "adt")
else:
    program_path = working_root

try:
    os.symlink(package_path, program_path)
except OSError as e:
    if e.errno == errno.EEXIST:
        print(
            f"post_install::create packages symbolic link : (OSError) (package_path: ${package_path}, program_path: ${program_path})"
        )
        os.symlink(package_path, program_path)
    else:
        raise e

print("post_install::all : done")
