from project.problem import Problem
from collections import deque
import argparse
import sys


class DeterminizeProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the --det flag (determinize the automaton)
        """
        parser.add_argument('--det', help='determinize the given automaton', action='store_true')

    def is_chosen_problem(self, args):
        """
        The determinization problem is chosen if --det was given
        """
        return bool(args.det)

    def read_automaton(self, input_file):
        """
        Read the (possibly nondeterministic) automaton from the input file.
        Returns: (states, alphabet, start_state, final_states, transitions)
        transitions: dict (state, symbol) -> set of next states
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

            # In a nondeterministic automaton one (state, symbol) pair can lead to several states
            transitions.setdefault((from_state, symbol), set()).add(to_state)

        return states, alphabet, start_state, final_states, transitions

    def determinize(self, alphabet, start_state, final_states, transitions):
        """
        Subset construction: every state of the DFA is a set of NFA states.
        The new states are numbered in the order they are discovered (breadth-first search),
        processing the symbols in alphabetical order.
        Returns: (number of states, final state indices, list of (from, symbol, to) transitions)
        """
        symbols = sorted(alphabet)

        start = frozenset([start_state])
        index_of = {start: 0}      # subset -> index of the new state (s0, s1, ...)
        subsets = [start]          # index -> subset
        queue = deque([start])
        dfa_transitions = []

        while queue:
            current = queue.popleft()
            for symbol in symbols:
                # All NFA states reachable from any state of the current subset with this symbol
                target = set()
                for state in current:
                    target |= transitions.get((state, symbol), set())

                if not target:
                    # No transition -> it is not listed
                    continue

                target = frozenset(target)
                if target not in index_of:
                    index_of[target] = len(subsets)
                    subsets.append(target)
                    queue.append(target)

                dfa_transitions.append((index_of[current], symbol, index_of[target]))

        # A new state is final if it contains at least one final NFA state
        dfa_finals = [i for i, subset in enumerate(subsets) if subset & final_states]

        # Order: source state, then symbol, then target state
        dfa_transitions.sort()

        return len(subsets), dfa_finals, dfa_transitions

    def run(self, args):
        try:
            states, alphabet, start_state, final_states, transitions = self.read_automaton(args.input)
        except ValueError as error:
            print(f'Hiba: {error}', file=sys.stderr)
            sys.exit(1)

        count, finals, dfa_transitions = self.determinize(alphabet, start_state, final_states, transitions)

        lines = [
            ' '.join(f's{i}' for i in range(count)),
            ' '.join(alphabet),
            's0',
            ' '.join(f's{i}' for i in finals),
        ]
        for from_index, symbol, to_index in dfa_transitions:
            lines.append(f's{from_index} {symbol} s{to_index}')

        with open(args.output, 'w') as f:
            f.write('\n'.join(lines))