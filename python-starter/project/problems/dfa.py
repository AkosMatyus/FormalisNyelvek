from project.problem import Problem
import argparse


class DFAProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the --check argument (comma separated words to check)
        """
        parser.add_argument('--check', help='words to check with the DFA, separated by commas')

    def is_chosen_problem(self, args):
        """
        The DFA problem is chosen if --check was given
        """
        return args.check is not None

    def read_automaton(self, input_file):
        """
        Read the DFA from the input file.
        Returns: (start_state, final_states, transitions)
        transitions: dict (state, symbol) -> next state
        """
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip() != '']

        # 1. line: states, 2. line: alphabet (not needed, symbols come from transitions)
        start_state = lines[2]
        final_states = set(lines[3].split())

        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) != 3:
                continue
            from_state, symbol, to_state = parts
            transitions[(from_state, symbol)] = to_state

        return start_state, final_states, transitions

    def accepts(self, word, start_state, final_states, transitions):
        """
        Simulate the DFA on the given word
        """
        state = start_state
        for symbol in word:
            if (state, symbol) not in transitions:
                # no transition -> the word is rejected
                return False
            state = transitions[(state, symbol)]
        return state in final_states

    def run(self, args):
        start_state, final_states, transitions = self.read_automaton(args.input)

        words = args.check.split(',')
        results = []
        for word in words:
            if self.accepts(word, start_state, final_states, transitions):
                results.append('IGEN')
            else:
                results.append('NEM')

        with open(args.output, 'w') as f:
            f.write('\n'.join(results))