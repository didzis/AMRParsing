#!/usr/bin/env python
# encoding=utf-8

# for Python 3 compatibility
from __future__ import print_function

import sys, re, os, json
from collections import defaultdict

if sys.version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

try:

    # load wiki database
    with open(os.path.join(os.path.dirname(__file__), 'wiki.jsons')) as f:
        wikidb = {}
        wikidb2 = defaultdict(list)
        opre = re.compile(r':(op\d+) \"([^"]+)\"')
        for line in f:
            concept, wiki, name_ops = json.loads(line.strip())
            wikidb[(concept, name_ops.lower())] = wiki
            wikidb2[concept].append({
                "wiki": None if wiki == "-" else wiki.strip('"'),
                "name_ops": { op:value for op,value in opre.findall(name_ops.lower()) }
            })

    # load nationalities database
    with open(os.path.join(os.path.dirname(__file__), 'nationalities.json')) as f:
        nationalities = json.load(f)
        # workaround the old nationalities format with :opN words in-between (remove them and strip quotes from remaining)
        # separate multi-word input (left/key) nationalities
        max_nat_words = 1
        multi_word_nationalities = defaultdict(dict)
        for key,value in nationalities.items():
            parts = value.split(' ')
            if len(parts) > 1:
                nationalities[key] = ' '.join(v.strip('"') for v in parts if not v.startswith(':op'))
            parts = key.split(' ')
            if len(parts) > max_nat_words:
                max_nat_words = len(parts)
            multi_word_nationalities[parts[0]][tuple(parts)] = nationalities[key]

    # amr fragment locating regexps
    invalid_quotes = re.compile(r'(?<=[^"])?"{3,}(?=[^"]|$)')
    nationality = re.compile(r'(%s)(?=\W|$)' % '|'.join(nationalities.keys()))
    number_variable = re.compile(r'\(\s*(\d+)\s*/')
    null_edge_null_tag = re.compile(r':null_edge \(x\d+ / null_tag\)')
    empty_and_concept = re.compile(r':x \(x\d+ / and\)')
    closing_brackets = re.compile(r'^\s*\)+\s*$')
    opN = re.compile(r'op(\d+)')

    def postprocess(amr):
        from common.util import StrLiteral, Literal, Polarity

        # fix variables starting with number
        for var in list(amr.node_to_concepts.keys()):
            if var[0] >= '0' and var[0] <= '9':
                newvar = 'number'+var
                for i,root in enumerate(list(amr.roots)):
                    if root == var:
                        amr.roots[i] = newvar
                amr.node_to_concepts[newvar] = amr.node_to_concepts[var]
                del amr.node_to_concepts[var]
                for source,edges in list(amr.items()):
                    if source == var:
                        del amr[source]
                        amr[newvar] = edges
                    else:
                        for edge,targets in edges.items():
                            if len(targets) != 1:
                                # print('WARNING: unknown targets format:', targets)
                                continue
                            if targets[0] == var:
                                edges.remove(edge, targets)
                                edges.append(edge, (newvar,))
        # empty "and" concept/variable
        empty_and = set(v for v,concept in amr.node_to_concepts.items() if concept == 'and' and not amr.get(v))
        # variables with null_tag concept and any outgoint edges
        null_tag_vars = set(v for v,concept in amr.node_to_concepts.items() if concept == 'null_tag' and not amr.get(v))
        # remove edges, fix targets
        for source,edges in amr.items():
            # extract opNs and replace nationalities
            opNs = { int(opN.match(edge).group(1)):targets for edge,targets in edges.items() if opN.match(edge) and \
                                                                                        type(targets[0]) in (StrLiteral, Literal) }
            if opNs:
                Ns = sorted(opNs.keys())
                values = [ opNs[n][0][:] for n in Ns ]
                for i,value in enumerate(values):
                    if value not in multi_word_nationalities:
                        continue
                    mwnats = multi_word_nationalities[value]
                    repl_words = None
                    for n in range(2, min(max_nat_words, len(values)-i)+1):
                        input_words = tuple(values[i:i+n])
                        repl_words = mwnats.get(input_words)
                        if not repl_words:
                            continue
                        repl_Ns = Ns[i:i+n]
                        after_Ns = Ns[i+n:]
                    if not repl_words:
                        continue
                    # replace multiple
                    parts = repl_words.split(' ')
                    delta = len(parts) - len(input_words)
                    after_Ns.sort(reverse=True)
                    for n in after_Ns:
                        edges.remove('op%i' % n, opNs[n])
                        edges.append('op%i' % (n+delta), opNs[n])
                    repl_Ns.sort()
                    # remove current opNs
                    for n in repl_Ns:
                        edges.remove('op%i' % n, opNs[n])
                    # set opN+i to i-th element of parts
                    for i,part in enumerate(parts):
                        edges.append('op%i' % (repl_Ns[0]+i), (type(opNs[repl_Ns[0]][0])(part),))
                    # end
                    break

            for edge,targets in list(edges.items()):
                if len(targets) != 1:
                    # print('WARNING: unknown targets format:', targets)
                    continue
                if type(targets[0]) in (StrLiteral, Literal):
                    repl = None
                    if '""' in targets[0]:
                        repl = '__invalid_quotes__'
                    if targets[0][:] in nationalities:
                        repl = nationalities[targets[0][:]]
                    if repl:
                        # if replacement contains multiple words and the edge replaced is in form :opN
                        # for each replaced word a separate :opN edge must be created and :opN edges that were after
                        # the replaced one, must be renamed to :opNs with higher N values
                        parts = repl.split(' ')
                        if len(parts) > 1 and opN.match(edge): # this is an opN edge, reenumerate if more than one word
                            delta = len(parts) - 1
                            # N = int(edge[2:])
                            N = int(opN.match(edge).group(1))
                            if ('op%i' % (N+1)) in edges:
                                # there are opNs after current
                                # move ops after N to a higher position (+delta)
                                # first get all op numbers larger than N
                                ops = [int(match.group(1)) for match in (opN.match(op) for op in edges.keys()) if match and int(match.group(1)) > N]
                                ops.sort(reverse=True)  # from higher to lower
                                for op in ops:
                                    op_name = 'op%i' % op
                                    op_targets = edges[op_name]
                                    edges.remove(op_name, op_targets)
                                    edges.append('op%i' % (op+delta), op_targets)
                            # remove current opN
                            edges.remove(edge, targets)
                            # set opN+i to i-th element of parts
                            for i,part in enumerate(parts):
                                edges.append('op%i' % (N+i), (type(targets[0])(part),))
                        else:
                            # simple replacement
                            edges.remove(edge, targets)
                            edges.append(edge, (type(targets[0])(repl),))
                elif edge == 'null_edge':
                    if targets[0] in null_tag_vars:
                        edges.remove(edge, targets)
                elif edge == 'x':
                    if targets[0] in empty_and:
                        edges.remove(edge, targets)
                elif edge == 'name':
                    name_edges = amr.get(targets[0], {})
                    name_ops = set(name_edges.keys())
                    for data in wikidb2.get(amr.node_to_concepts.get(source, None), []):
                        # existing wiki ?
                        # stop = False
                        # for t in edges.get('wiki', []):
                        #     if len(t) == 1 and t[0] == data['wiki']:
                        #         stop = True
                        # if stop:
                        #     break
                        # replace existing wiki
                        for t in edges.get('wiki', []):
                            edges.remove('wiki', t)
                        # check if name :opN edges match
                        expected_name_edges = data['name_ops']
                        expected_name_ops = set(data['name_ops'].keys())
                        if expected_name_ops <= name_ops and expected_name_ops >= name_ops:
                            match = True
                            for op in name_ops:
                                if len(name_edges[op]) != 1 or expected_name_edges[op] != name_edges[op][0][:].lower():
                                    match = False
                                    break
                            if match:
                                edges.append('wiki', (StrLiteral(data['wiki']) if data['wiki'] else Polarity('-'),))
                                break
        return amr


except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(1)


def read_amr(lines):
    before = []
    after = []
    amr = []
    # possible_and_root = False
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith('#'):
            # Comment or empty line
            if amr:
                after.append(line)
                break
            else:
                before.append(line)
        else:
            # AMR line
            # Some CAMR specific fixes:
            # - invalid quotes
            line = invalid_quotes.sub('"__invalid_quotes__"', line)
            # - remove null_edges with a sole "null_tag" concept inside and edges to empty "and" concepts
            line = null_edge_null_tag.sub('', line)
            line = empty_and_concept.sub('', line)
            if not line.rstrip():
                continue
            elif closing_brackets.match(line):
                if amr:
                    amr[-1] += line.strip()
                    continue
            # # - and concept at root
            # if not amr and line.startswith('(x / xconcept'):
            # - fix number variable names
            line = number_variable.sub(r'(number\1 /', line)
            # - update nationalities
            for nationality_before in nationality.findall(line):
                line = line.replace(nationality_before, nationalities[nationality_before])
            amr.append(line)
    return before, amr, after

def extract_backwards(lines, pos):
    # TODO: how to determine if in quotes at start ?
    in_quotes = False
    in_braces = 0
    chars = []
    for line in lines:
        if pos != 0:
            line = line[:pos]
        for c in reversed(line):
            if c == '"':
                chars.append(c)
                in_quotes = not in_quotes
            elif in_quotes:
                chars.append(c)
            else:
                # update brace depth, because going left, ")" will increase and "(" will decrease depth
                if c == ')':
                    in_braces += 1
                elif c == '(':
                    in_braces -= 1
                # act depending on brace depth
                if in_braces >= 0:
                    chars.append(c)
                elif in_braces < 0:
                    # out of starting brace level - exit
                    return ''.join(reversed(chars))
        pos = 0
    print('warning: extract_backwards reached unexpected end of data', file=sys.stderr)
    return ''.join(reversed(chars))

def extract_forwards(lines, pos):
    # TODO: how to determine if in quotes at start ?
    in_quotes = False
    in_braces = 0
    chars = []
    for line in lines:
        if pos > 0:
            line = line[pos:]
        for c in line:
            if c == '"':
                chars.append(c)
                in_quotes = not in_quotes
            elif in_quotes:
                chars.append(c)
            else:
                # update brace depth, because going right, "(" will increase and ")" will decrease depth
                if c == ')':
                    in_braces -= 1
                elif c == '(':
                    in_braces += 1
                # act depending on brace depth
                if in_braces >= 0:
                    chars.append(c)
                elif in_braces <= -1:
                    # out of starting brace level - exit
                    return ''.join(chars)
        pos = 0 
    print('warning: extract_forwards reached unexpected end of data', file=sys.stderr)
    print(''.join(chars), file=sys.stderr)
    raise ValueError
    return ''.join(chars)

def line_iter(lines, line_index, inc):
    while line_index >= 0 and line_index < len(lines):
        yield lines[line_index]
        line_index += inc

def process_amr_string(amr, compact_amr, search_str=':name'):
    for line_index, (line, compact_line) in enumerate(zip(amr, compact_amr)):
        start = 0
        compact_start = 0
        while True:
            pos = line.find(search_str, start)
            if pos == -1:
                break
            compact_pos = compact_line.find(search_str, compact_start)
            start = pos+1
            compact_start = compact_pos+1
            bwd = extract_backwards(line_iter(compact_amr, line_index, -1), compact_pos)
            fwd = extract_forwards(line_iter(compact_amr, line_index, 1), compact_pos)
            yield bwd,fwd,line_index,pos


if __name__ == "__main__":

    def usage():
        print('usage:', sys.argv[0], '[--debug|-d] [input.amrs... | < input.amr] > output.amr', file=sys.stderr)

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        usage()
        sys.exit(0)

    debug = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--debug' or arg == '-d':
            args.pop(i)
            debug = True
        else:
            i += 1

    def sources():
        if args:
            for arg in args:
                with open(arg, 'rb') as f:
                    yield (line.decode('utf8', errors='ignore') for line in f)
        else:
            usage()
            print('waiting for input from stdin', file=sys.stderr)
            yield sys.stdin

    try:

        concept_re = re.compile(r'^\w+ \/ ([\w\-]+) .*')
        name_ops_re = re.compile(r'^:name \(\w+ \/ name([^()]+)\).*')

        last = ''
        for f in sources():
            if last:
                print() # add extra empty line between sources
            while True:
                before, amr, after = read_amr(f)
                for last in before:
                    print(last)
                if not amr:
                    break

                for bwd,fwd,line_index,pos in process_amr_string(amr, [' '+line.strip() for line in amr]):

                    # extract concept
                    m = concept_re.match(bwd)
                    if m is None:
                        continue
                    concept = m.group(1)

                    # extract name ops
                    m = name_ops_re.match(fwd)
                    if m is None:
                        continue
                    name_ops = m.group(1)

                    # search in database
                    wiki = wikidb.get((concept, name_ops.lower()))
                    if wiki is not None:
                        line = amr[line_index]
                        amr[line_index] = line[:pos] + ':wiki ' + wiki + ' ' + line[pos:]

                    if debug:
                        if wiki is not None:
                            print('    FOUND: ... / %-26s ...%s' % (concept, name_ops), file=sys.stderr)
                        else:
                            print('NOT FOUND: ... / %-26s ...%s' % (concept, name_ops), file=sys.stderr)

                for last in amr:
                    print(last)
                for last in after:
                    print(last)

    except ValueError:
        print('AMR [line: %i]:' % line_index, '\n'.join(amr), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('Interrupted', file=sys.stderr)
        sys.exit(1)
