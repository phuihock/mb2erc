#!/bin/env python
import os
import re

class Line(object):

    def __init__(self, line_no, para):
        self.line_no = line_no
        self.para = para
        self.placeholder = ['|'] * sum([p['repeat'] for p in self.para])
        self.data = []

        for i, p in enumerate(self.para):
            if p['default']:
                for repeat_index in range(p['repeat']):
                    self.data.append(p['default'])
                    self.placeholder[i * repeat_index] = len(self.data) - 1

    def get(self, name, repeat_index=1):
        for i, p in enumerate(self.para):
            if p['name'] != name:
                continue

            data_index = self.placeholder[i * repeat_index]
            return p['conv'](self.data[data_index])

    def set(self, name, v):
        for i, p in enumerate(self.para):
            if p['name'] != name:
                continue

            conv, format_spec, length = p['conv'], p['format_spec'], p['length']
            repeat = p['repeat']

            for repeat_index in range(1, repeat + 1):
                out = format_spec.format(conv(v)).strip()
                out = out[:length]
                self.data.append(out)
                self.placeholder[i * repeat_index] = len(self.data) - 1
            break

    def hash(self):
        return 0

    def out(self):
        s = []
        for p in self.placeholder:
            if p != '|':
                d = self.data[p]
                s.append(d)
            else:
                s.append('')
        return '|'.join(s)


class PaymentFile(object):
    def __init__(self):
        self.content = {'header': None, 'record': [], 'footer': None}
        self.line_no = 0

        self.header = []
        self.record = []
        self.footer = []

        fmt_file = os.path.join(os.path.dirname(__file__), 'payment_file.fmt')
        with open(fmt_file, 'r') as f:
            for para in [self.header, self.record, self.footer]:
                while True:
                    line = f.readline().strip()
                    if line == '':
                        break
                    try:
                        pos, length, kind, cond, name, remarks, default, repeat = line.split('|')
                    except ValueError, e:
                        print line
                        raise e

                    conv = str
                    if kind == 'N':
                        if length.find('v') != -1:
                            mo = re.match(r'9\((\d+)\)v9\((\d+)\)', length)
                            if mo:
                                conv, format_spec = float, "{:<%d.%df}" % tuple(map(int, mo.groups()))
                                length = mo.group(1)
                        elif length == 'DDMMYYYY':
                            conv, format_spec = lambda d: d.strftime('%d%m%Y'), "{:<%ds}" % len(length)
                        else:
                            conv, format_spec = int, "{:<%dd}" % int(length)
                    else:
                        format_spec = "{:<%ds}" % int(length)
                    descriptor = {"length": int(length), "kind": kind, "cond": cond, "name": name, "remarks": remarks, "default": default, "conv": conv, "format_spec": format_spec, 'repeat': int(repeat)}
                    if pos.find('-') != -1:
                        begin, end = [int(i) for i in pos.split('-')]
                        for p in range(begin, end + 1):
                            para.append(descriptor)
                    else:
                        para.append(descriptor)

    def incr_line_no(self):
        self.line_no += 1
        return self.line_no

    def set_header(self):
        h = Line(self.incr_line_no(), self.header)
        self.content['header'] = h
        return h

    def add_record(self):
        r = Line(self.incr_line_no() - 1, self.record)
        self.content['record'].append(r)
        return r

    def set_footer(self):
        f = Line(self.incr_line_no(), self.footer)
        self.content['footer'] = f
        return f

    def set_footer_hash(self):
        total_hash = 0

        for l in self.content['record']:
            total_hash += l.hash()

        footer = self.content['footer']
        footer.set('Hashing Value', total_hash)

    def finalize(self):
        self.set_footer_hash()

    def out(self):
        self.finalize()

        s = []
        for p in ['header', 'record', 'footer']:
            line = self.content[p]
            if line:
                if isinstance(line, list):
                    for l in line:
                        s.append(l.out())
                else:
                    s.append(line.out())
        return s