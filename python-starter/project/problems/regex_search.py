from project.problem import Problem
import argparse
import re
import sys


# The expression given in the task description (+ ^ so it always starts at the beginning of a line)
# groups: 1 = whole line, 2 = date and time, 3 = process id, 4 = thread id,
#         5 = level (I, D, V, E, F, A, W), 6 = tag, 7 = message
LOG_LINE = r'^(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) ([IDVEFAW]) (.+?):(?: (.+))?)'

# The same expression, but only for error (E) lines
ERROR_LINE = r'^(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) (E) (.+?):(?: (.+))?)'

# Beginning of a log line until the level: date, time, process id, thread id
HEAD = r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ '

# Task 1: one regex for every sub-task (in the order of the task description)
TASK1_PATTERNS = [
    r'^10-15 [0-9:.]+ ',                         # created on 10-15
    r'^10-15 10:18:51\.',                        # created on 10-15 at 10:18:51
    r'^[0-9-]+ [0-9]{2}:[0-9]{2}:51\.',          # created at second 51 (any minute)
    HEAD + r'[IDVEFAW] lowmemorykiller *:',      # tag is lowmemorykiller
    r'^[0-9-]+ 10:18:51\.[0-9]+ +221 +[0-9]+ ',  # at 10:18:51 with process id 221
    HEAD + r'E ',                                # errors
    HEAD + r'W PackageManager *:',               # warnings sent by PackageManager
    HEAD + r'D .*ExoPlayer',                     # ExoPlayer debug lines (anywhere in the line)
    HEAD + r'[EW] .*\.java:',                    # errors and warnings with a java file position
    HEAD + r'[IDVEFAW] [^:]+: .*Thread',         # "Thread" in the message (after "tag: ")
]

# Java file in a stack trace, e.g. (HashMap.java:500) -> HashMap.java
JAVA_FILE = r'\(([A-Za-z0-9_$]+\.java):[0-9]+\)'


class RegexProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the --rgx argument (number of the regex task)
        """
        parser.add_argument('--rgx', type=int, help='number of the regex task (1-5)')

    def is_chosen_problem(self, args):
        """
        The regex problem is chosen if --rgx was given
        """
        return args.rgx is not None

    def task1(self, text):
        """
        Count the matching lines for every sub-task, one number per line
        """
        return [str(len(re.findall(pattern, text, re.MULTILINE))) for pattern in TASK1_PATTERNS]

    def task2(self, text):
        """
        Java files from the stack traces of the error lines, in order, with repetitions
        """
        files = []
        for line in re.finditer(ERROR_LINE, text, re.MULTILINE):
            message = line.group(7)
            if message is not None:
                files.extend(re.findall(JAVA_FILE, message))
        return files

    def task3(self, text):
        """
        Different process ids in the order of their first occurrence
        """
        pids = {}
        for line in re.finditer(LOG_LINE, text, re.MULTILINE):
            pids[line.group(3)] = True    # a dict keeps the insertion order
        return list(pids)

    def task4(self, text):
        """
        The process with the most errors: PID=xx (xx errors)
        """
        error_count = {}
        for line in re.finditer(ERROR_LINE, text, re.MULTILINE):
            pid = line.group(3)
            error_count[pid] = error_count.get(pid, 0) + 1

        if not error_count:
            return []

        best_pid = None
        for pid in error_count:
            if best_pid is None or error_count[pid] > error_count[best_pid]:
                best_pid = pid
        return [f'PID={best_pid} ({error_count[best_pid]} errors)']

    def task5(self, text):
        """
        Number of errors on the main thread (process id == thread id)
        """
        count = 0
        for line in re.finditer(ERROR_LINE, text, re.MULTILINE):
            if line.group(3) == line.group(4):
                count += 1
        return [str(count)]

    def run(self, args):
        tasks = {
            1: self.task1,
            2: self.task2,
            3: self.task3,
            4: self.task4,
            5: self.task5,
        }
        if args.rgx not in tasks:
            print(f'Hiba: ismeretlen feladat: {args.rgx} (1-5 lehet)', file=sys.stderr)
            sys.exit(1)

        with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        result = tasks[args.rgx](text)

        with open(args.output, 'w') as f:
            f.write('\n'.join(result))