#!/usr/bin/env python3

import os
import re
import sys
import subprocess
import platform


def sys_str():
    if sys.platform == "linux" or sys.platform == "linux2":
        return "linux"
    elif sys.platform == "darwin":
        return "mac"
    elif sys.platform == "win32":
        return "windows"
    else:
        raise Exception("unknown system")


def in_windows():
    return sys.platform == "win32"


def in_unix():
    return sys.platform in ("linux", "linux2", "darwin")


def in_64bit():
    """return True if in a 64-bit architecture"""
    # http://stackoverflow.com/a/12578715/5875572
    machine = platform.machine()
    if machine.endswith('64'):
        return True
    elif machine.endswith('86'):
        return False
    raise Exception("unknown platform architecture")
    # return (struct.calcsize('P') * 8) == 64


def in_32bit():
    """return True if in a 32-bit architecture"""
    # http://stackoverflow.com/a/12578715/5875572
    machine = platform.machine()
    if machine.endswith('64'):
        return False
    elif machine.endswith('86'):
        return True
    raise Exception("unknown platform architecture")
    # return (struct.calcsize('P') * 8) == 32


def splitesc(string, split_char, escape_char=r'\\'):
    """split a string at the given character, allowing for escaped characters
    http://stackoverflow.com/a/21107911"""
    rx = r'(?<!{}){}'.format(escape_char, split_char)
    s = re.split(rx, string)
    return s


def cslist(arg):
    '''transform comma-separated arguments into a list of strings.
    commas can be escaped with backslash, \\'''
    return splitesc(arg, ',')


def which(cmd):
    """look for an executable in the current PATH environment variable"""
    if os.path.exists(cmd):
        return cmd
    exts = ("", ".exe", ".bat") if sys.platform == "win32" else ""
    for path in os.environ["PATH"].split(os.pathsep):
        for e in exts:
            j = os.path.join(path, cmd+e)
            if os.path.exists(j):
                return j
    return None


def chkf(*args):
    """join the args as a path and check whether that path exists"""
    f = os.path.join(*args)
    if not os.path.exists(f):
        raise Exception("path does not exist: " + f + ". Current dir=" + os.getcwd())  # nopep8
    return f


def cacheattr(obj, name, function):
    """add and cache an object member which is the result of a given function.
    This is for implementing lazy getters when the function call is expensive."""
    if hasattr(obj, name):
        val = getattr(obj, name)
    else:
        val = function()
        setattr(obj, name, val)
    return val


def ctor(cls, args):
    if not isinstance(args, list):
        args = [args]
    l = []
    for i in args:
        l.append(cls(i))
    return l


def nested_lookup(dictionary, *entry):
    """get a nested entry from a dictionary"""
    try:
        if isinstance(entry, str):
            v = dictionary[entry]
        else:
            v = None
            for e in entry:
                # print("key:", e, "value:", v if v is not None else "<none yet>")
                v = v[e] if v is not None else dictionary[e]
    except:
        raise Exception("could not find entry '" +
                        "/".join(list(entry)) + "' in the dictionary")
    return v


# -----------------------------------------------------------------------------
class setcwd:
    """temporarily change into a directory inside a with block"""

    def __init__(self, dir_, silent=False):
        self.dir = dir_
        self.silent = silent

    def __enter__(self):
        self.old = os.getcwd()
        if self.old == self.dir:
            return
        if not self.silent:
            print("Entering directory", self.dir, "(was in {})".format(self.old))
        chkf(self.dir)
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old == self.dir:
            return
        if not self.silent:
            print("Returning to directory", self.old, "(currently in {})".format(self.dir))
        chkf(self.old)
        os.chdir(self.old)

# -----------------------------------------------------------------------------

# subprocess.run() was introduced only in Python 3.5,
# so we provide a replacement implementation to use in older Python versions.
# See http://stackoverflow.com/a/40590445
if sys.version_info >= (3,5):
    run_replacement = subprocess.run
else:
    class CompletedProcess:
        def __init__(self, returncode, args, stdout, stderr):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
        def check_returncode(self):
            if self.returncode:
                raise subprocess.CalledProcessError(
                    self.returncode, self.args, self.stdout, self.stderr)

    def subprocess_run_impl(*popenargs, input=None, check=False, **kwargs):
        if input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not both be used.')
            kwargs['stdin'] = subprocess.PIPE
        process = subprocess.Popen(*popenargs, **kwargs)
        try:
            stdout, stderr = process.communicate(input)
        except:
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
        if check and retcode:
            raise subprocess.CalledProcessError(
                retcode, process.args, output=stdout, stderr=stderr)
        return CompletedProcess(args=process.args, returncode=retcode,
                                stdout=stdout, stderr=stderr)

    # point run_replacement to our implementation
    run_replacement = subprocess_run_impl


def runsyscmd(arglist, echo_cmd=True, echo_output=True, capture_output=False, as_bytes_string=False):
    """run a system command. Note that stderr is interspersed with stdout"""

    # issue the command as a string to prevent problems with quotes
    if isinstance(arglist, list):
        cmd = " ".join(arglist)
    elif isinstance(arglist, str):
        cmd = arglist
    else:
        raise Exception("the command must be either a list or a string")

    if echo_cmd:
        print('$', cmd)

    if as_bytes_string:
        if capture_output:
            result = run_replacement(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDERR)
            result.check_returncode()
            return result.stdout
        else:
            result = run_replacement(cmd)
            result.check_returncode()
    else:
        if not echo_output:
            result = run_replacement(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True)
            result.check_returncode()
            if capture_output:
                return str(result.stdout)
        elif echo_output:
            if capture_output:
                result = run_replacement(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        universal_newlines=True)
                result.check_returncode()
                return str(result.stdout)
            else:
                result = run_replacement(cmd, universal_newlines=True)
                result.check_returncode()
