"""
Tests for the problems.
"""

import sys
import traceback

from regex_parse import make_parser
import hal_vm

all_problems = ('literals finite plus star plus_compiled star_compiled '
                'literals_hal').split()
solutions = set(all_problems)

def main(argv):
    problems = argv[1:] or all_problems
    for problem in problems:
        test_problem(problem)
    return 0

def test_problem(name):
    module = __import__(name)
    check = globals()['check_'+name]
    print("Testing " + name + ".py: ")
    try:
        check(module)
    except NotImplementedError:
        print("  Nothing to test yet.")
    else:
        if name in solutions:
            url = "https://github.com/darius/regexercise_solutions/blob/master/%s.py" % name
            print("  Passed! See my solution at " + url)
        else:
            print("  Passed.")

def check(module, regex_string, string, remainder):
    parse = make_parser(module)
    check_search(module.search, regex_string, parse(regex_string),
                 string, remainder)

def check_search(search, pattern_string, pattern, string, remainder):
    correct_result = remainder is not None
    stream = iter(string)
    try:
        result = search(pattern, stream)
    except NotImplementedError:
        raise
    except:
        print_bounded_traceback()
        print show_test_case(pattern_string, pattern, string, remainder, False)
        sys.exit(1)
    unconsumed = ''.join(stream)
    test_case = show_test_case(pattern_string, pattern, string, remainder,
                               True, result, unconsumed)
    if remainder is None:
        assert result is False, "Wrong result." + test_case
        assert not unconsumed, "The stream should be exhausted." + test_case
    else:
        assert result is True, "Wrong result." + test_case
        assert unconsumed == remainder, "Too much or too litle of the stream was consumed." + test_case

def show_test_case(pattern_string, pattern, string, remainder,
                   completed, result=None, unconsumed=None):
    correct_result = remainder is not None
    pairs = ()
    if pattern_string is not None:
        pairs += (("Regex:", pattern_string),)
    pairs += (("Pattern: ", pattern), ("Input:", string))
    if not completed:
        pairs += (("Result should be:", correct_result),)
    elif result is not correct_result:
        pairs += (("Result should be:", correct_result),
                  ("But result is:   ", result))
    if not completed:
        pairs += (("Remainder should be:", remainder),)
    elif unconsumed != (remainder or ''):
        pairs += (("Remainder should be:", remainder),
                  ("But remainder is:   ", unconsumed))
    return ''.join('\n %s %r' % pair for pair in pairs)

def print_bounded_traceback():
    lines = traceback.format_exc().splitlines()
    if 30 < len(lines):
        lines = lines[:15] + ['  [...]'] + lines[-15:]
    print '\n'.join(lines)

def check_literals(module):
    check_search(module.search, None, [], '', None)
    check_search(module.search, None, [], 'wheee', None)
    check_search(module.search, None, [''], 'wheee', 'wheee')
    check1_base(LiteralsRegexMaker(module.search))
    return "Literal patterns: all tests passed."

def check_literals_hal(module):
    # TODO other check_literals tests -- move 'em into regex tests
    check1_base(LiteralsRegexMaker(HalSearch(module.compile_pattern)))
    return "Literal patterns for HAL: all tests passed."

def HalSearch(compiler):
    def search(regex, chars):
        program = compiler(regex)
        return hal_vm.load_program(program, chars).run()
        # XXX make stream track getch
    return search

class LiteralsRegexMaker:
    def __init__(self, search):
        self.search = search
    empty = ['']
    def literal(self, char): return [char]
    def chain(self, r, s):   return [ri + sj for ri in r for sj in s]
    def either(self, r, s):  return r + s

def check1_base(module):
    check(module, r'X', 'wheee', None)
    check(module, r'X', 'X', '')
    check(module, r'X', 'wheXXXee', 'XXee')
    check(module, r'X', 'yX', '')
    check(module, r'X|X', 'yX', '')
    check(module, r'X|YY', 'YX', '')
    check(module, r'hallo|a', 'hallo', 'llo')
    check(module, r'ab', 'aab', '')
    check(module, r'rat|cat', 'a cat is fat', ' is fat')
    check(module, r'XXX', 'XX', None)
    check(module, r'XXXY', 'r u XXXish or XXXY?', '?')
    check(module, r'bababy', 'aababababyish', 'ish')
    check(module, r'bababy', 'aabababababyish', 'ish')
    check(module, r'bababy', 'aabababababish', None)

def check_finite(module):
    check1_base(module)
    check(module, r'(0|1)'*20,
          'hello 01100011000110001100 how are you?',
          ' how are you?')
    check(module, r'(0|1)'*20,
          'hello 0110001100011000110 how are you?',
          None)
    check(module, r'(aa|a)'*2,
          'aaa b',
          'a b')
    check(module, r'(aa|a)'*40,
          'a aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa b',
          'aaaaa b')
    check(module, r'(aa|a)'*40,
          'a aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa b',
          None)
    return "Abstract data: all tests passed."

def check_plus(module):
    check_finite(module)
    check(module, r'A+', 'A', '')
    check(module, r'A+', 'Rating AAA+, would do again.', 'AA+, would do again.')
    check(module, r'a[bc]+d', 'my abdomen', 'omen')
    check(module, r'a[bc]+d', 'abcbdcb', 'cb')
    check(module, r'a[bc]+d', 'my addomen', None)
    check(module, r'(cat|dog)+like', 'dogcatcatdogcatdogdogcatdogcatcatdogcatdogdogcatlikely', 'ly')
    return "Plus: all tests passed."

def check_plus_compiled(module):
    return check_plus(module)

def check_star(module):
    check_plus(module)
    check(module, r'a*', '', '')
    check(module, r'ba*', '', None)
    check(module, r'ba*', 'abc', 'c')
    check(module, r'ab*c', 'an abba abcd', 'd')
    check(module, r'ab*c', 'an abba abd', None)
    check(module, r'yo(ab|c*a)*ba', 'a yoaabcaccaabbaba', 'ba')
# These tests go beyond the official interface, but can help:
#    check(module, r'()*', '', '')
#    check(module, r'(()())*', '', '')
    check(module, r'a(b*)*d', 'an ad attacks', ' attacks')
    check(module, r'a(b*)*d', 'an abdomen', 'omen')
    return "Star: all tests passed."

def check_star_compiled(module):
    return check_star(module)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
