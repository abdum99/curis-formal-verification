#!/usr/bin/python3

import subprocess
import sys
from collections import defaultdict
from itertools import chain
from ast import literal_eval

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

    # renaming nodes
    btw_list = [root_value]
    while len(btw_list) < N:
        a = btw_list[-1]  
        for b in range(N):
            if all((a,b,c) in relations['id_ring.btw'] or a == c or b == c for c in range(N)):
                btw_list.append(b)
                break
        else:
            assert False
    print(btw_list)
 
    dot = """
    digraph G {
    """
    # active nodes
    for tup in relations['active']:
        for u in tup:
            dot += f'{btw_list.index(u)} [color=red]\n'
            if u is root_value:
                dot += f'{btw_list.index(u)} [style=filled]\n'

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
                dot += f'{btw_list.index(a)} -> {btw_list.index(b)} [style=filled]\n'
                break
        else:
            assert len(reachable[a]) == 0, a

    # predecessors
    for u, v in relations['pred']:
        dot += f'{btw_list.index(u)} -> {btw_list.index(v)} [style=dashed]\n'

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
        print("Check output")
