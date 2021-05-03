import re
from pwn import *
import string
from itertools import combinations
p = remote("nooombers.challenges.ooo", 8765)
p.sendline('')

def recv2(until):
    out = p.recvuntil(until)
    # print(out.decode())
    return out

out = p.recvrepeat(timeout=1).decode().split('\n')

initial = out[1]
characters = out[2:]

saved = set()
results = set()
symbols = {}

first = True
eq = None

def save_results():
    global results, saved
    saved = results.copy()

def load_results():
    global results, saved
    results = saved.copy()

def check(out):
    for result in results:
        if out == result[0]:
            return result
    return None

monkas=["".join(ban) for ban in combinations(string.ascii_lowercase, 2)]
def strtosymbol(s):
    if type(s) == Number:
        s = s.e
    if s not in symbols.keys():
        #symbols[s] = string.ascii_letters[len(symbols)]
        symbols[s] = monkas[len(symbols)]    
    return symbols[s]

def get_symbol_eq(s):
    eq = next(filter(lambda x: x[0] == s, results))
    if eq[1] == 0:
        return s
    else:
        return eq

ultrapretty = True
expandpretty = True

def prettyres(r, first=True):
    if type(r) == str:
        return r
    r2 = r[2]
    if expandpretty:
        if len(r2) > 0:
            r2 = list(map(lambda x: prettyres(x, first=False), map(get_symbol_eq, r2)))
    args = ", ".join(r2)
    res = f"{r[1]}({args})"
    if first:
        res += f" = {r[0]}"
        if ultrapretty:
            res = ultraprettify(res)
    return res

def ultraprettify(s):
    s = re.sub(r'3\(1\((\w)\), \1\)', 'n0', s)
    s = re.sub(r'4\(2\((\w)\), \1\)', 'n1', s)
    s = re.sub(r'3\(n1, n1\)', 'n2', s)
    s = re.sub(r'5\(2\((\w)\), \1\)', '@', s)
    return s

def op(i, *tokens):
    p.sendline(characters[i])

    for token in tokens:
        p.sendline(token)
        # p.sendline(t[token[0]][token[1]])
    out = recv2(initial).decode().split('\n')
    if out[-2].strip() == "Too much! Disabling one option...":
        out = out[-3]
    else:
        out = out[-2]
    out = out.split()

    if len(tokens) > 0 and type(tokens[0]) == Number:
        tokens = map(lambda x: x.e, tokens)
    out = out[-1]
        
    symbolout = strtosymbol(out)
    symboltokens = list(map(strtosymbol, tokens))
    newop = (symbolout, i, tuple(symboltokens))
    print(prettyres(newop))
    if (r := check(symbolout)) and r != newop and newop not in results:
        print("!!!", prettyres(newop), "<->", prettyres(r))

    results.add(newop)
    first = False
    return Number(out)

def n():
    return op(0)

def create_symbols(num):
    assert num <= 8
    rs = list(symbols.values())
    while len(rs) < num:
        newr = n()
        if newr not in rs:
            rs.append(Number(newr))
    return rs
            
class Number:
    def __init__(self, e):
        self.e = e
    def __neg__(self):
        return op(1, self)
    def __invert__(self):
        return op(2, self)
    def __add__(self, y):
        return op(3, self, y)
    def __sub__(self, y):
        return op(3, self, op(1, y))
    def __mul__(self, y):
        return op(4, self, y)
    def __truediv__(self, y):
        return op(4, self , op(2, y))
    def __pow__(self, y):
        return op(5, self, y)
    def __xor__(self, y):
        return op(6, self, y)
    def __eq__(self, y):
        if type(y) == str:
            return self.e == y
        else:
            return self.e == y.e
    def __repr__(self) -> str:
        return self.e
    def encode(self, encoding=None):
        return self.e.encode()
    def decode(self, encoding=None):
        return self.e

expandpretty = False
ultrapretty = False

a,b,c = create_symbols(3)

n0 = a-a
n1 = a/a
n2 = n1+n1
n3 = n2+n1
n4 = n3+n1

assert op(1, op(3, op(1, a), a)) == op(3, op(1, a), a)
assert op(1, op(1, a)) == a
assert op(2, op(4, op(2, a), a)) == op(4, op(2, a), a)
assert op(2, op(2, a)) == a
assert op(2, op(3, op(1, a), a)) == op(3, op(1, a), a)
assert op(3, a, b) == op(3, b, a)
assert op(3, a, op(3, b, c)) == op(3, op(3, a, b), c)
assert op(3, b, op(3, op(1, a), a)) == b
assert op(3, op(1, a), op(3, a, b)) == b
assert op(4, a, b) == op(4, b, a)
assert op(4, a, op(4, b, c)) == op(4, op(4, a, b), c)
assert op(4, b, op(4, op(2, a), a))
assert op(4, b, op(5, op(2, a), a))
assert op(4, op(2, a), op(4, a, b)) == b
assert op(4, a, op(3, b, op(1, b))) == op(3, b, op(1, b))
assert op(4, a, op(3, b, c)) == op(3, op(4, a, b), op(4, a, c))
assert op(3, n1, op(3, n1, op(3, n1, n1))) == op(4, op(3, n1, n1), op(3, n1, n1))
assert op(4, a, n2) == op(3, a, a)
assert op(5, a, b) == op(5, b, a)
assert op(5, a, op(5, b, c)) ==  op(5, op(5, a, b), c)
assert op(5, b, op(4, a, op(2, a))) == b
assert op(5, b, op(3, a, op(1, a))) == op(3, a, op(1, a))
assert op(4, op(2, a), op(5, a, b)) == b
assert op(5, op(2, a), op(5, a, b)) != b
assert op(4, op(5, op(2, a), a), op(5, op(2, a), a)) == op(4, op(2, a), a)
assert op(2, op(5, op(2, a), a)) == op(4, op(2, a), a)
assert op(1, op(5, op(2, a), a)) == op(1, op(4, op(2, a), a))
assert op(5, op(2, a), a) != op(4, op(2, a), a)
assert op(6, a, b) != op(6, b, a)
assert op(6, a, op(6, b, c)) != op(6, op(6, a, b), c)
assert op(6, b, op(4, op(2, a), a)) == b
assert op(6, op(4, op(2, a), a), b) == op(4, op(2, a), a)
assert op(6, op(3, op(1, a), a), b) == op(3, op(1, a), a)
assert op(6, b, op(3, op(1, a), a)) == op(4, op(2, a), a)
assert op(6, n3, n2) == op(4, n3, n3)
assert op(6, b, n2) != op(4, b, b)
assert op(6, b, n2) != op(4, b, b)
assert op(6, op(6, n2, n3), n4) == op(6, n2, op(4, n3, n4))
assert op(6, op(6, a, b), c) != op(6, a, op(4, b, c))
assert op(6, op(6, a, b), c) == op(6, a, op(5, b, c))
assert op(6, a, op(1, n1)) != op(2, a)
assert op(5, op(6, a, b), op(6, a, c)) != op(6, a, op(5, b, c))
assert op(5, op(6, a, c), op(6, b, c)) == op(6, op(5, a, b), c)