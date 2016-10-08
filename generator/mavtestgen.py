#!/usr/bin/env python
'''
generate a MAVLink test suite

Copyright Andrew Tridgell 2011
Released under GNU GPL version 3 or later
'''
from __future__ import print_function
from builtins import range

import sys, textwrap
from argparse import ArgumentParser

# mavparse is up a directory level
from . import mavparse

def gen_value(f, i, language):
    '''generate a test value for the ith field of a message'''
    type = f.type

    # could be an array
    if type.find("[") != -1:
        aidx = type.find("[")
        basetype = type[0:aidx]
        if basetype == "array":
            basetype = "int8_t"
        if language == 'C':
            return '(const %s *)"%s%u"' % (basetype, f.name, i)
        return '"%s%u"' % (f.name, i)

    if type == 'float':
        return 17.0 + i*7
    if type == 'char':
        return 'A' + i
    if type == 'int8_t':
        return 5 + i
    if type in ['int8_t', 'uint8_t']:
        return 5 + i
    if type in ['uint8_t_mavlink_version']:
        return 2
    if type in ['int16_t', 'uint16_t']:
        return 17235 + i*52
    if type in ['int32_t', 'uint32_t']:
        v = 963497464 + i*52
        if language == 'C':
            return "%sL" % v
        return v
    if type in ['int64_t', 'uint64_t']:
        v = 9223372036854775807 + i*63
        if language == 'C':
            return "%sLL" % v
        return v



def generate_methods_python(outf, msgs):
    outf.write("""
'''
MAVLink protocol test implementation (auto-generated by mavtestgen.py)

Generated from: %s

Note: this file has been auto-generated. DO NOT EDIT
'''

import mavlink

def generate_outputs(mav):
    '''generate all message types as outputs'''
""")
    for m in msgs:
        if m.name == "HEARTBEAT": continue
        outf.write("\tmav.%s_send(" % m.name.lower())
        for i in range(0, len(m.fields)):
            f = m.fields[i]
            outf.write("%s=%s" % (f.name, gen_value(f, i, 'py')))
            if i != len(m.fields)-1:
                outf.write(",")
        outf.write(")\n")


def generate_methods_C(outf, msgs):
    outf.write("""
/*
MAVLink protocol test implementation (auto-generated by mavtestgen.py)

Generated from: %s

Note: this file has been auto-generated. DO NOT EDIT
*/

static void mavtest_generate_outputs(mavlink_channel_t chan)
{
""")
    for m in msgs:
        if m.name == "HEARTBEAT": continue
        outf.write("\tmavlink_msg_%s_send(chan," % m.name.lower())
        for i in range(0, len(m.fields)):
            f = m.fields[i]
            outf.write("%s" % gen_value(f, i, 'C'))
            if i != len(m.fields)-1:
                outf.write(",")
        outf.write(");\n")
    outf.write("}\n")



######################################################################
'''main program'''

parser = ArgumentParser(description="This tool generate MAVLink test suite")
parser.add_argument("-o", "--output", default="mavtest", help="output folder [default: %(default)s]")
parser.add_argument("definitions", metavar="XML", nargs="+", help="MAVLink definitions")
args = parser.parse_args()

msgs = []
enums = []

for fname in args.definitions:
    (m, e) = mavparse.parse_mavlink_xml(fname)
    msgs.extend(m)
    enums.extend(e)


if mavparse.check_duplicates(msgs):
    sys.exit(1)

print("Found %u MAVLink message types" % len(msgs))

print("Generating python %s" % (args.output+'.py'))
outf = open(args.output + '.py', "w")
generate_methods_python(outf, msgs)
outf.close()

print("Generating C %s" % (args.output+'.h'))
outf = open(args.output + '.h', "w")
generate_methods_C(outf, msgs)
outf.close()

print("Generated %s OK" % args.output)