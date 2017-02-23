#!/usr/bin/env python2.7
# encoding:utf-8
# Created on 2017-02-15, by dozysun
import sys
import imp
import traceback
import marshal

import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

ENCRYPT_START_STR = 'DSENCRYPT===:'
AES_RANDOM_KEY = 'sdfsdfssdfjsdoiewrjsdioafjlekjw'
AES_RANDOM_IV = '\x0f\xe1\x0c\x87Na\xa1D\x86$Z\x155\x8e\x82\x80' #Random.new().read(AES.block_size)


class DSImportHook(object):
    """
    use imp module to  make find and load module
    see doc: https://docs.python.org/2/library/imp.html#imp.find_module
    """
    def __init__(self):
        self._modules = {}
        self.aes_cipher = AESCipher()

    def register_module(self, name, pathname, description, is_package=False):
        self._modules[name] = (pathname, description, is_package)

    def find_module(self, name, path=None):
        try:
            full_name = name
            if '.' in name:   # imp.find_module  can't work with dot
                if not path:
                    return None
                name = name.rpartition('.')[-1]
            f, pathname, description = imp.find_module(name, path)

            if f:
                if description[0].startswith('.py') and self.aes_cipher.is_encrypt_py(f):
                    self.register_module(full_name, pathname, description)
                    return self

        except ImportError,e:
            pass
        else:
            if f:
                f.close()
        return None

    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]
        if name not in self._modules:
            raise ImportError
        try:
            pathname, description, is_package = self._modules[name]
            code = self.get_code(pathname)
            ispkg = is_package
            if ispkg:
                code = marshal.loads(code[8:])
            else:
                if pathname.endswith(('pyc', 'pyo')):
                    code = marshal.loads(code[8:])

            mod = sys.modules.setdefault(name, imp.new_module(name))
            mod.__name__ = name
            mod.__file__ = pathname
            mod.__loader__ = self
            if ispkg:
                mod.__path__ = []
                mod.__package__ = name
            else:
                mod.__package__ = name.rpartition('.')[0]
            exec(code, mod.__dict__)

            return mod
        except Exception:
            traceback.print_exc()
            raise ImportError

    def get_code(self, pathname):
        f = open(pathname)
        return self.decrypt_py(f.read())

    def decrypt_py(self, code_str):
        return self.aes_cipher.decrypt(code_str.replace(ENCRYPT_START_STR, '', 1))

    def is_package(self, name):
        return False
        # return self._modules[name][-1][0] and False or True


class AESCipher(object):

    def __init__(self, key=AES_RANDOM_KEY, iv=AES_RANDOM_IV):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()
        self.iv = iv
        self.cipher = AES.new(self.key, AES.MODE_CBC, self.iv)

    # def encrypt(self, raw):
    #     raw = self._pad(raw)
    #     return base64.b64encode(self.cipher.encrypt(raw))
    #
    # def decrypt(self, enc):
    #     return self._unpad(self.cipher.decrypt(base64.b64decode(enc)))
    #
    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def is_encrypt_py(f):
        if isinstance(f, file):
            f = f.read(20)
        if f.startswith(ENCRYPT_START_STR):
            return True

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

aes_cipher = AESCipher()


def encrypt_file(file_):
    if file_.endswith('pyc'):
        mod = 'rb+'
    else:
        mod = 'r+'
    with open(file_, mod) as f:
        s = f.read()
        if aes_cipher.is_encrypt_py(s):
            return
    with open(file_, 'w') as f:
        es = aes_cipher.encrypt(s)
        f.write(ENCRYPT_START_STR)
        f.write(es)

if __name__ == '__main__':
    sys.meta_path.insert(0, DSImportHook())
