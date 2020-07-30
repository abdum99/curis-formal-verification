#!/usr/bin/python3

import subprocess
import sys
from collections import defaultdict
from itertools import chain
from ast import literal_eval

def ivy_trace_to_dot(pre_state, action):
    
    # find root
    root = [l.split('=')[-1] for l in pre_state if l.startswith('root = ')]
    root_value = literal_eval(root[0].strip())

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

    root_value = btw_list.index(root_value)
    
    dot = """
    digraph G {
    """
    # print action
    fmls = [l.split('=')[-1].strip() for l in action[:action.index(']')] if l.startswith('fml')]
    fmls = tuple(btw_list.index(literal_eval(x)) for x in fmls)
    call, action_name = action[0].split()
    assert call == 'call', call
    dot += f'label = "{action_name}{fmls}"\n'
    for u in fmls:
        dot += f'{u} [style=filled]\n'
                
    # active nodes
    for tup in relations['active']:
        for u in tup:
            dot += f'{btw_list.index(u)} [color=green]\n'
            if btw_list.index(u) is root_value:
                dot += f'{btw_list.index(u)} [label="{btw_list.index(u)}\nroot"]\n'

    # computing labels to each node
    label = ['root\n' if x == root_value else ' ' for x in range(N)]
    for i in range(len(inv_nodes)):
        u = btw_list.index(inv_nodes[i])
        label[u] += str(inv_var[i]) + '\n'
    
    # writing label to nodes that violate inv
    for u in inv_nodes:
        i = inv_nodes.index(u)
        dot += f'{btw_list.index(u)} [label="{btw_list.index(u)}\n {label[btw_list.index(u)]}"]'
            
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
    ivy_original_output = subprocess.check_output(['ivy_check', 'trace=true', sys.argv[1]], universal_newlines=True)
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
        open('chord.dot', 'w').write(dot)
        open('chord_output.txt', 'w').write(ivy_original_output)
        subprocess.check_call(['display', 'chord.dot'])
        save_file = str(input('Save counter example to newfile?(y/n): ')).lower().strip()
        if save_file[0] == 'y':
            file_name = input('Name of file: ')
            file_name_dot = file_name + '.dot'
            subprocess.check_call(['cp', 'chord.dot', file_name_dot.strip()])
            file_name_output = file_name + '_ivy_output.txt'
            subprocess.check_call(['cp', 'chord_output.txt', file_name_output.strip()])
    except ValueError:
        print("Check output")
