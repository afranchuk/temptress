#!/usr/bin/env python

from functools import partial
import re
import sys


FILL_END_MARKER=r"end"
TEMPLATE_END_MARKER=r"==="

def split_fields(s):
    i = 0
    out = []
    curstr = ""
    escape = False
    string = False
    for i in range(0,len(s)):
        if s[i] == '\\':
            if escape:
                curstr += '\\'
            escape = not escape
        elif s[i] == '"':
            if escape:
                curstr += '"'
                escape = False
            else:
                string = not string
        elif s[i] == ' ':
            if string:
                curstr += ' '
            else:
                out.append(curstr)
                curstr = ""
        else:
            curstr += s[i]
    if len(curstr) > 0:
        out.append(curstr)
    return out

def parse_template_macro(s):
    m = re.search(r":(.*)", s)
    arr = []
    if m:
        ids = split_fields(m.group(1))
        lines = s[m.end(0):].split("\n")
        for line in lines:
            vals = split_fields(line)
            if len(vals) == len(ids):
                arr.append(dict(zip(ids,vals)))
    else:
        raise Exception("Missing indices")
    return arr

def get_line(inp, pos):
    i = pos
    while inp[i] != '\n' and i >= 0:
        i -= 1
    s = i+1

    i = pos
    while inp[i] != '\n' and i < len(inp):
        i += 1
    e = i
    return (s, e)

def get_lines(inp, arr):
    if isinstance(arr,list):
        return [get_line(inp, k) for k in arr]
    else:
        return get_line(inp, arr)

def fill_template(template, data):
    nline = template
    for l in data.keys():
        nline = nline.replace("{%s}" % l, data[l])
    return nline + "\n"

def extract_block(inp, start, end, col):
    i = start
    st = ""
    while i < end:
        e = i
        while e < end and inp[e] != '\n':
            e += 1

        if e == end and inp[e] != '\n':
            break
        st += inp[i+col:e+1]
        i = e+1
    return st[:-1]

def run_input(defs, inp):
    for k in defs.keys():
        n = 0
        while True:
            p = re.compile(r"(%s).*\n" % k).search(inp, n)
            if not p:
                break
            
            (begin, end) = get_line(inp,p.start(0))
            column = p.start(0) - begin
            prefix = inp[begin:p.start(0)]
            pre_whitespace = re.match(r"\s*", prefix).group(0)

            templ = re.compile(r"[ \t]+(.*)\s*").search(inp, p.end(1), p.end(0))
            if not templ:
                e = re.compile(TEMPLATE_END_MARKER).search(inp, p.end(0))
                if not e:
                    break
                
                [(ps, pe), (es, ee)] = get_lines(inp, [p.end(1), e.start(0)])
                template = extract_block(inp, pe+1, es, column)
                temp_end = ee
            else:
                template = inp[templ.start(1):templ.end(1)]
                temp_end = templ.end(0)-1

            e = re.compile(FILL_END_MARKER+r"\s+%s" % k).search(inp, temp_end)
            if e:
                endpos = e.start(0)
                endadd = ""
            else:
                endpos = temp_end
                endadd = prefix+FILL_END_MARKER+" %s\n" % k

            [(_,inp_begin), (inp_end,end_end)] = get_lines(inp, [temp_end, endpos])

            filled_lines = map(partial(fill_template,pre_whitespace+template),defs[k])
            to_insert = ''.join(filled_lines) + endadd
            inp = inp[:inp_begin+1] + to_insert + inp[inp_end:]
            n = inp_begin+1+len(to_insert)
            if e:
                n += end_end - inp_end + 1
    return inp

def get_defs(data):
    m_defs = {}
    for p in re.finditer(r"within (.*?) {(.*?)}", tdata, re.S):
        m_defs[p.group(1)] = parse_template_macro(p.group(2))
    return m_defs

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: %s def_file template_file [template_file ...]\n" % sys.argv[0]
        sys.exit(-1)

    tvalfile = sys.argv[1]

    with open (tvalfile, "r") as f:
        tdata = f.read()

    m_defs = get_defs(tdata)

    for i in range(2,len(sys.argv)):
        # Match the template macros in the file(s)!
        f = open (sys.argv[i], "r+")
        fdata = f.read()

        fdata = run_input(m_defs, fdata)

        f.seek(0)
        f.truncate()
        f.write(fdata)
        f.close()
