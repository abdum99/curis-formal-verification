#!/usr/bin/python3

import subprocess
import sys
from collections import defaultdict
from itertools import chain
from ast import literal_eval

def ivy_trace_to_dot(pre_state, action):
    
    # find roots
    root_1 = [l.split('=')[-1] for l in pre_state if l.startswith('root_1 = ')]
    root_value_1 = literal_eval(root_1[0].strip())
    root_2 = [l.split('=')[-1] for l in pre_state if l.startswith('root_2 = ')]
    root_value_2 = literal_eval(root_2[0].strip())
    root_3 = [l.split('=')[-1] for l in pre_state if l.startswith('root_3 = ')]
    root_value_3 = literal_eval(root_3[0].strip())

    # identify nodes that violate invariant
    inv_var = [l.split('=')[0].strip() for l in pre_state if l.startswith('@')]
    inv_var = [x for x in inv_var]
    inv_nodes = [l.split('=')[-1].strip() for l in pre_state if l.startswith('@')]
    inv_nodes = [literal_eval(x) for x in inv_nodes]
        
    # get relations
    pre_state = [l.split()[0] for l in pre_state if l.endswith(' = true')]
    relations = defaultdict(set)
    for l in pre_state:
        assert '(' in l, l
        i = l.find('(')
        relations[l[:i]].add(literal_eval(l[i:-1] + ',)'))
    
    # number of nodes in system
    N = 1 + max(u for tup in chain(*relations.values()) for u in tup)

    # renaming nodes
    btw_list = [root_value_1]
    while len(btw_list) < N:
        a = btw_list[-1]  
        for b in range(N):
            if all((a,b,c) in relations['id_ring.btw'] or a == c or b == c for c in range(N)):
                btw_list.append(b)
                break
        else:
            assert False
    print(btw_list)

    root_value_1 = btw_list.index(root_value_1)
    root_value_2 = btw_list.index(root_value_2)
    root_value_3 = btw_list.index(root_value_3)

    dot = """
    digraph G {
    """
    # print action
    fmls = [l.split('=')[-1].strip() for l in action[:action.index(']')] if l.startswith('fml')]
    fmls = tuple(btw_list.index(literal_eval(x)) for x in fmls)
    call, action_name = action[0].split()
    assert call == 'call', call
    dot += f'label = "{action_name}{fmls}\n succ.p: orange\n succ_1: blue\n succ_2: red"\n'
    for u in fmls:
        dot += f'{u} [style=filled]\n'
                
    # computing labels to each node
    label = ['root_1\n' if x == root_value_1 else 'root_2\n' if x == root_value_2 else 'root_3\n' if x == root_value_3 else ' ' for x in range(N)]
    #label = ['root_2\n' if x == root_value_2 else ' ' for x in range(N)]
    #label = ['root_3\n' if x == root_value_3 else ' ' for x in range(N)]

    # active nodes
    for tup in relations['active']:
        for u in tup:
            dot += f'{btw_list.index(u)} [color=green]\n'
            label[btw_list.index(u)] += 'active\n'

    # failed nodes
    for tup in relations['failed']:
        for u in tup:
            dot += f'{btw_list.index(u)} [color=red]\n'
            label[btw_list.index(u)] += 'failed\n'

    # dom for succ_1
    for tup in relations['succ_1.dom']:
        for u in tup:
            label[btw_list.index(u)] += 'succ_1.dom\n'
            
    # dom for succ_2
    for tup in relations['succ_2.dom']:
        for u in tup:
            label[btw_list.index(u)] += 'succ_2.dom\n'        

    # dom for succ
    for tup in relations['succ.dom']:
        for u in tup:
            label[btw_list.index(u)] += 'succ.dom\n'

    # dom for succ
    for tup in relations['pred.dom']:
        for u in tup:
            label[btw_list.index(u)] += 'pred.dom\n'
            
    # adding to labels the nodes that violate the invariant
    for i in range(len(inv_nodes)):
        u = btw_list.index(inv_nodes[i])
        label[u] += str(inv_var[i]) + '\n'

    # writing label to nodes
    for u in range(N):
        dot += f'{u} [label="{u}\n {label[u]}"]'

    # WRITING EDGES
    
    # edges for succ_1 (blue)
    for a, b in relations['succ_1.f']:
        dot += f'{btw_list.index(a)} -> {btw_list.index(b)} [style=filled, color=blue]\n'
        
    # edges for succ_2 (red)
    for a, b in relations['succ_2.f']:
        dot += f'{btw_list.index(a)} -> {btw_list.index(b)} [style=filled, color=red]\n'

    # edges for succ.p (orange)
    reachable = defaultdict(set)
    pair = defaultdict(set)

    for a, b, c in relations['succ.p']:
        pair[a].add((b, c))
        reachable[a].add(b)

    for a in range(N):        
        for b in reachable[a]:
            if all((b,c) in pair[a] for c in reachable[a]):    
                dot += f'{btw_list.index(a)} -> {btw_list.index(b)} [style=filled, color=orange]\n'
                break
        else:
            assert len(reachable[a]) == 0, a

    # edges for predecessors (dashed)
    for u, v in relations['pred.f']:
        dot += f'{btw_list.index(u)} -> {btw_list.index(v)} [style=dashed]\n'

    dot += """

    }
    """

    return dot

if __name__ == '__main__':
    if sys.argv[1].endswith('.ivy'):
        ivy_original_output = subprocess.check_output(['ivy_check', 'trace=true', sys.argv[1]], universal_newlines=True)
    else:
        ivy_original_output = open(sys.argv[1]).read()
    ivy_output = ivy_original_output
    print(ivy_output)
    ivy_output = [l.strip() for l in ivy_output.splitlines()]
            
    try:
        i = ivy_output.index('searching for a small model... done')
        ivy_output = ivy_output[i + 2:]
        i = ivy_output.index(']')
        violation_action = ivy_output[i + 1:-1]
        pre_state = ivy_output[:i]
        dot = ivy_trace_to_dot(pre_state, violation_action)
        open('chord2_no_joins.dot', 'w').write(dot)
        open('chord2_no_joins_output.txt', 'w').write(ivy_original_output)
        subprocess.check_call(['display', 'chord2_no_joins.dot'])
        save_file = str(input('Save counter example to newfile?(y/n): ')).lower().strip()
        if save_file[0] == 'y':
            file_name = input('Name of file: ')
            file_name_dot = file_name + '.dot'
            subprocess.check_call(['cp', 'chord2_no_joins.dot', file_name_dot.strip()])
            file_name_output = file_name + '_ivy_output.txt'
            subprocess.check_call(['cp', 'chord2_no_joins_output.txt', file_name_output.strip()])
    except ValueError:
        print("Check output")
