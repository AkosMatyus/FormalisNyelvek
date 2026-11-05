from project.problem import Problem
from collections import deque
import argparse
import re
import sys


def state_key(name):
    """
    Sorting key for state names: q2 comes before q10 (numeric order, not plain string order)
    """
    match = re.fullmatch(r'(\D*)(\d+)', name)
    if match:
        return (0, match.group(1), int(match.group(2)))
    return (1, name, 0)


def new_name(name):
    """
    Rename a state: q1 -> s1 (the number stays, the letter becomes s)
    """
    match = re.fullmatch(r'(\D*)(\d+)', name)
    if match:
        return 's' + match.group(2)
    return 's' + name


class MinimizeProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the --mini flag (minimize the automaton)
        """
        parser.add_argument('--mini', help='minimize the given automaton', action='store_true')

    def is_chosen_problem(self, args):
        """
        The minimization problem is chosen if --mini was given
        """
        return bool(args.mini)

    def read_automaton(self, input_file):
        """
        Read the deterministic automaton from the input file.
        Returns: (states, alphabet, start_state, final_states, transitions)
        transitions: dict (state, symbol) -> next state
        """
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f]

        # Drop empty lines at the end of the file
        while lines and lines[-1] == '':
            lines.pop()

        if len(lines) < 4:
            raise ValueError('A bemeneti fajlnak legalabb 4 sort kell tartalmaznia.')

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2]
        final_states = set(lines[3].split())

        # --- Basic error handling ---
        if start_state not in states:
            raise ValueError(f'Ismeretlen kezdoallapot: {start_state}')
        for state in final_states:
            if state not in states:
                raise ValueError(f'Ismeretlen vegallapot: {state}')

        transitions = {}
        for line_number, line in enumerate(lines[4:], start=5):
            if line == '':
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f'Hibas atmenet a(z) {line_number}. sorban: {line}')
            from_state, symbol, to_state = parts

            if from_state not in states:
                raise ValueError(f'Ismeretlen allapot a(z) {line_number}. sorban: {from_state}')
            if to_state not in states:
                raise ValueError(f'Ismeretlen allapot a(z) {line_number}. sorban: {to_state}')
            if symbol not in alphabet:
                raise ValueError(f'Ismeretlen szimbolum a(z) {line_number}. sorban: {symbol}')

            # The automaton must be deterministic: one (state, symbol) pair -> at most one target
            if (from_state, symbol) in transitions and transitions[(from_state, symbol)] != to_state:
                raise ValueError(f'Az automata nem determinisztikus a(z) {line_number}. sorban: {line}')

            transitions[(from_state, symbol)] = to_state

        return states, alphabet, start_state, final_states, transitions

    def reachable_states(self, alphabet, start_state, transitions):
        """
        Collect the states reachable from the start state (breadth-first search).
        Unreachable states can never be used, so they are left out of the minimal automaton.
        """
        reachable = {start_state}
        queue = deque([start_state])
        while queue:
            state = queue.popleft()
            for symbol in alphabet:
                target = transitions.get((state, symbol))
                if target is not None and target not in reachable:
                    reachable.add(target)
                    queue.append(target)
        return reachable

    def minimize(self, states, alphabet, final_states, transitions):
        """
        Partition refinement (Moore's algorithm).
        Start with two groups: final and non-final states. Then split the groups again and again:
        two states stay together only if, for every symbol, they go into the same group
        (or both have no transition with that symbol).
        Stops when no group splits any more.
        Returns: dict state -> group number
        """
        group_of = {state: (1 if state in final_states else 0) for state in states}

        while True:
            # Signature of a state: its current group + the groups of its targets
            signatures = {}
            for state in states:
                targets = []
                for symbol in alphabet:
                    target = transitions.get((state, symbol))
                    targets.append(group_of[target] if target is not None else None)
                signatures[state] = (group_of[state], tuple(targets))

            # States with the same signature form one new group
            new_ids = {}
            new_group_of = {}
            for state in sorted(states, key=state_key):
                signature = signatures[state]
                if signature not in new_ids:
                    new_ids[signature] = len(new_ids)
                new_group_of[state] = new_ids[signature]

            number_of_old_groups = len(set(group_of.values()))
            group_of = new_group_of
            if len(new_ids) == number_of_old_groups:
                # Nothing split -> the partition is final
                return group_of

    def run(self, args):
        try:
            states, alphabet, start_state, final_states, transitions = self.read_automaton(args.input)
        except ValueError as error:
            print(f'Hiba: {error}', file=sys.stderr)
            sys.exit(1)

        # 1. Remove unreachable states
        reachable = self.reachable_states(alphabet, start_state, transitions)
        states = [state for state in states if state in reachable]

        # 2. Find the groups of equivalent states
        group_of = self.minimize(states, alphabet, final_states, transitions)

        # 3. Every group is named after its smallest state (q1 and q5 -> s1)
        representative = {}
        for state in sorted(states, key=state_key):
            group = group_of[state]
            if group not in representative:
                representative[group] = state

        def merged(state):
            return representative[group_of[state]]

        new_states = sorted(set(representative.values()), key=state_key)
        new_start = merged(start_state)
        new_finals = sorted({merged(state) for state in states if state in final_states}, key=state_key)

        # 4. Transitions between the new states (a set, so there are no duplicates)
        new_transitions = set()
        for (from_state, symbol), to_state in transitions.items():
            if from_state in reachable:
                new_transitions.add((merged(from_state), symbol, merged(to_state)))

        # Order: source state, then symbol, then target state
        ordered = sorted(new_transitions, key=lambda t: (state_key(t[0]), t[1], state_key(t[2])))

        lines = [
            ' '.join(new_name(state) for state in new_states),
            ' '.join(alphabet),
            new_name(new_start),
            ' '.join(new_name(state) for state in new_finals),
        ]
        for from_state, symbol, to_state in ordered:
            lines.append(f'{new_name(from_state)} {symbol} {new_name(to_state)}')

        with open(args.output, 'w') as f:
            f.write('\n'.join(lines))