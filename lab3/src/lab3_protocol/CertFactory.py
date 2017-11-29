import os

root = "keys"


def getCertsForAddr(addr):
    chain = []

    # Enter the location of the user's certificate as per the user's system
    with open(root + "/app/cert.crt") as fo:
        chain.append(fo.read())

    # Enter the location of the CA certificate as per the location of the system
    with open(root + "/ca.crt") as fi:
        chain.append(fi.read())

    return chain


def getPrivateKeyForAddr(addr):
    # Enter the location of the Private key as per the location of the system
    with open(root + "/app/private.key")as fp:
        private_key_user = fp.read()

    return private_key_user


def getRootCert():
    # Enter the location of the Root certificate
    with open(root + "/root.crt") as f:
        rootcertbytes = f.read()

    return rootcertbytes