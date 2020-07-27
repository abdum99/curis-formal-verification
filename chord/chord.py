#!/usr/bin/python3

import subprocess
import sys
from collections import defaultdict
from itertools import chain
from ast import literal_eval

# st = """
#     id_ring.btw(0,1,2) = true
#     id_ring.btw(1,2,0) = true
#     id_ring.btw(2,0,1) = true
#     id_ring.btw(0,0,0) = false
#     id_ring.btw(0,0,1) = false
#     id_ring.btw(0,0,2) = false
#     id_ring.btw(0,1,0) = false
#     id_ring.btw(0,1,1) = false
#     id_ring.btw(0,2,0) = false
#     id_ring.btw(0,2,1) = false
#     id_ring.btw(0,2,2) = false
#     id_ring.btw(1,0,0) = false
#     id_ring.btw(1,0,1) = false
#     id_ring.btw(1,0,2) = false
#     id_ring.btw(1,1,0) = false
#     id_ring.btw(1,1,1) = false
#     id_ring.btw(1,1,2) = false
#     id_ring.btw(1,2,1) = false
#     id_ring.btw(1,2,2) = false
#     id_ring.btw(2,0,0) = false
#     id_ring.btw(2,0,2) = false
#     id_ring.btw(2,1,0) = false
#     id_ring.btw(2,1,1) = false
#     id_ring.btw(2,1,2) = false
#     id_ring.btw(2,2,0) = false
#     id_ring.btw(2,2,1) = false
#     id_ring.btw(2,2,2) = false
#     active(0) = true
#     active(1) = true
#     active(2) = true
#     pred(0,2) = true
#     pred(2,0) = true
#     pred(0,0) = false
#     pred(0,1) = false
#     pred(1,0) = false
#     pred(1,1) = false
#     pred(1,2) = false
#     pred(2,1) = false
#     pred(2,2) = false
#     succ.p(0,0,0) = true
#     succ.p(1,0,0) = true
#     succ.p(2,0,0) = true
#     succ.p(2,1,0) = true
#     succ.p(2,1,1) = true
#     succ.p(0,0,1) = false
#     succ.p(0,0,2) = false
#     succ.p(0,1,0) = false
#     succ.p(0,1,1) = false
#     succ.p(0,1,2) = false
#     succ.p(0,2,0) = false
#     succ.p(0,2,1) = false
#     succ.p(0,2,2) = false
#     succ.p(1,0,1) = false
#     succ.p(1,0,2) = false
#     succ.p(1,1,0) = false
#     succ.p(1,1,1) = false
#     succ.p(1,1,2) = false
#     succ.p(1,2,0) = false
#     succ.p(1,2,1) = false
#     succ.p(1,2,2) = false
#     succ.p(2,0,1) = false
#     succ.p(2,0,2) = false
#     succ.p(2,1,2) = false
#     succ.p(2,2,0) = false
#     succ.p(2,2,1) = false
#     succ.p(2,2,2) = false
# """

def ivy_trace_to_dot(lines):
    
    # find root
    root = [l.split('=')[-1] for l in lines if l.startswith('root = ')]
    root_value = literal_eval(root[0].strip())

    lines = [l.split()[0] for l in lines if l.endswith(' = true')]
    # print(lines)

    relations = defaultdict(set)
    for l in lines:
        assert '(' in l, l
        i = l.find('(')
        relations[l[:i]].add(literal_eval(l[i:-1] + ',)'))
    # print(relations)

    # number of nodes in system
    N = 1 + max(u for tup in chain(*relations.values()) for u in tup)
    # print(f'N = {N}')

    dot = """
    digraph G {
    """

    # active nodes
    for tup in relations['active']:
        for u in tup:
            dot += f'{u} [color=red]\n'
            if u is root_value:
                dot += f'{u} [style=filled]\n'

    # successors (edges)
    reachable = defaultdict(set)
    pair = defaultdict(set)

    for a, b, c in relations['succ.p']:
        pair[a].add((b, c))
        reachable[a].add(b)

    # print(pair)
    # print(reachable)

    for a in range(N):        
        for b in reachable[a]:
            # count = 0
            # for c in reachable[a]:
            #     for u, v in pair[a]:
            #         if u == b and v == c:
            #             count += 1
            #             break
            # count = len(c for c in reachable[a] if (b,c) in pair[a])
            # if count == len(reachable[a]):
            if all((b,c) in pair[a] for c in reachable[a]):    
                dot += f'{a} -> {b} [style=filled]\n'
                break
        else:
            assert len(reachable[a]) == 0, a

    # predecessors
    for u, v in relations['pred']:
        dot += f'{u} -> {v} [style=dashed]\n'

    dot += """
    }
    """

    return dot

if __name__ == '__main__':
    #ivy_output = subprocess.check_output(['ivy_check', 'trace=true', sys.argv[1]], encoding='UTF-8')
    ivy_output = subprocess.check_output(['ivy_check', 'trace=true', sys.argv[1]], universal_newlines=True)
    print(ivy_output)
    ivy_lines = [l.strip() for l in ivy_output.splitlines()]
    
    try:
        i = ivy_lines.index('searching for a small model... done')
        ivy_lines = ivy_lines[i + 2:]
        i = ivy_lines.index(']')
        ivy_lines = ivy_lines[:i]
        dot = ivy_trace_to_dot(ivy_lines)
        open('chord.dot', 'w').write(dot)
        subprocess.run(['dot', '-Tpng', 'chord.dot', '-o',  'chord.png'])
        subprocess.run(['display', 'chord.png'])
        save_file = str(input('Save counter example to newfile?(y/n): ')).lower().strip()
        if save_file[0] == 'y':
            file_name = input('Name of file: ')
            subprocess.run(['cp', 'chord.png', file_name.strip()])
    except ValueError:
        print("Ivy verified model!")
