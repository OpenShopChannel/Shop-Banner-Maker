import datetime
import collections
import json
import struct
import subprocess
import sys
import time


"""Packs integers to specific type."""

# Unsigned integers

def u8(data):
    if data < 0 or data > 255:
        data = 0
    return struct.pack(">B", data)


def u16(data):
    if data < 0 or data > 65535:
        data = 0
    return struct.pack(">H", data)


def u32(data):
    if data < 0 or data > 4294967295:
        data = 0
    return struct.pack(">I", data)


def u32_littleendian(data):
    if data < 0 or data > 4294967295:
        data = 0
    return struct.pack("<I", data)


def u64(data):
    if data < 0 or data > 9223372036854775807:
        data = 0
    return struct.pack(">Q", data)


# Signed integers

def s8(data):
    if data < -128 or data > 128:
        data = 0
    return struct.pack(">b", data)


def s16(data):
    if data < -32768 or data > 32768:
        data = 0
    return struct.pack(">h", data)


def s32(data):
    if data < -2147483648 or data > 2147483648:
        data = 0
    return struct.pack(">i", data)


dictionaries = []


def offset_count():
    """Counts offsets."""
    return u32(sum(len(values)
                   for dictionary in dictionaries
                   for values in dictionary.values()
                   if values) - 8)


with open("config.json", "rb") as f:
    config = json.load(f)


def make_csdf():
    csdf = collections.OrderedDict()
    dictionaries.append(csdf)

    csdf["tag"] = "csdf"
    csdf["length"] = u32(0)

    return csdf


def make_dcvd():
    dcvd = collections.OrderedDict()
    dictionaries.append(dcvd)

    dcvd["tag"] = "dcvd"
    dcvd["length"] = u32(8)
    dcvd["timestamp"] = u64(time.time() * 100)

    return dcvd


def make_dltd():
    dltd = collections.OrderedDict()
    dictionaries.append(dltd)

    dltd["tag"] = "dltd"
    dltd["length"] = u32(12)
    dltd["year"] = u32(datetime.datetime.now().year)
    dltd["month"] = u32(datetime.datetime.now().month)
    dltd["day"] = u32(datetime.datetime.now().day)

    return dltd


def make_crmd():
    crmd = collections.OrderedDict()
    dictionaries.append(crmd)

    for i in range(1, 5):
        crmd["tag_%s" % i] = "crmd"
        crmd["length_%s" % i] = u32(0)
        dmsg = make_dmsg(i)
        dtpl = make_dtpl(i)
        crmd.update(dmsg)
        crmd.update(dtpl)
        crmd["length_%s" % i] = u32(sum(len(values) for dictionary in [dmsg, dtpl] for values in dictionary.values() if values))


def make_dmsg(i):
    dmsg = collections.OrderedDict()

    dmsg["tagm_%s" % i] = "dmsg"
    dmsg["lengthm_%s" % i] = u32(len(config["msg_%s" % i].encode("utf-16be")))
    dmsg["msg_%s" % i] = config["msg_%s" % i].encode("utf-16be")

    return dmsg


def make_dtpl(i):
    dtpl = collections.OrderedDict()

    dtpl["tagt_%s" % i] = "dtpl"

    if config["tpl_%s" % i][-4:] == ".png":
        subprocess.call(["wimgt", "ENCODE", config["tpl_%s" % i], "-x", "TPL.CMPR", "-d", config["tpl_%s" % i][:-4] + ".tpl"])

    with open(config["tpl_%s" % i][:-4] + ".tpl", "rb") as source_file:
        data = source_file.read()

    dtpl["lengtht_%s" % i] = u32(30 + len(data))
    dtpl["tpl_%s" % i] = u8(0) * 30 + data

    return dtpl


def write_dictionary():
    """Write everything to the file."""
    for dictionary in dictionaries:
        for values in dictionary.values():
            with open(sys.argv[1] + "-1", "ab") as dest_file:
                dest_file.write(values)


def main():
    if len(sys.argv) != 2:
        print "Usage: wiishop.py <output file>"
        exit()
    
    print "Wii Shop Channel Banner Maker"

    csdf = make_csdf()
    make_dcvd()
    make_dltd()
    make_crmd()

    csdf["length"] = offset_count()

    write_dictionary()


if __name__ == "__main__":
    main()
