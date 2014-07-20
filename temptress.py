#!/usr/bin/env python

from functools import partial
import re
import sys

def parse_template_macro(s):
    m = re.search(r":(.*)", s)
    arr = []
    if m:
        ids = m.group(1).split(" ")
        lines = s[m.end(0):].split("\n")
        for line in lines:
            vals = line.split(" ")
            if len(vals) == len(ids):
                arr.append(dict(zip(ids,line.split(" "))))
    else:
        raise Exception("FAIL")
    return arr

def remove_lines_between(st, sindex, eindex):
    i = sindex
    while st[i] != '\n':
        i += 1
    s = i+1
    e = s
    while i != eindex:
        if st[i] == '\n':
            e = i+1
        i += 1

    return (st[:s], st[e:])

def fill_template(template, data):
    nline = template
    for l in data.keys():
        nline = nline.replace("{%s}" % l, data[l])
    return nline + "\n"

def run_input(defs, inp):
    for k in defs.keys():
        for p in re.finditer(r"%s\w*\((.*)\)" % k, inp):
            e = re.compile(r"END %s" % k).search(inp, p.end(0))
            if not e:
                raise Exception("Unmatched start of template: %s" % k)

            (inp_begin, inp_end) = remove_lines_between(inp, p.end(0), e.start(0))
            template = p.group(1)

            filled_lines = map(partial(fill_template,template),defs[k])
            return inp_begin + ''.join(filled_lines) + inp_end

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s def_file template_file\n" % sys.argv[0]
        sys.exit(-1)

    tvalfile = sys.argv[1]
    tfile = sys.argv[2]

    m_defs = {}

    with open (tvalfile, "r") as f:
        tdata = f.read()

    for p in re.finditer(r"within (.*) {(.*)}", tdata, re.S):
        m_defs[p.group(1)] = parse_template_macro(p.group(2))

    # Match the template macros in the file!
    f = open (tfile, "r+")
    fdata = f.read()

    fdata = run_input(m_defs, fdata)

    f.seek(0)
    f.truncate()
    f.write(fdata)
    f.close()
