#!/usr/bin/env python3
"""Validate dot-bracket secondary-structure strings in a FASTA-like file.

Each record is three lines: a name, a sequence (prefixed with '>'), and a
dot-bracket string. A structure is valid if:
  - it only contains recognised symbols ( . and matched bracket pairs ),
  - every opening bracket has a matching closing bracket (balanced/nested),
  - its length matches the sequence length.
"""
import sys

# Supported bracket pairs (pseudoknots use extra pairs like [], {}, <>).
PAIRS = {')': '(', ']': '[', '}': '{', '>': '<'}
OPENERS = set(PAIRS.values())
CLOSERS = set(PAIRS.keys())
VALID = OPENERS | CLOSERS | {'.'}


# Canonical Watson-Crick pairs plus the G-U wobble pair (RNA).
VALID_PAIRS = {
    frozenset('AU'), frozenset('GC'), frozenset('GU'),
}


def is_valid_pair(b1, b2):
    return frozenset((b1.upper(), b2.upper())) in VALID_PAIRS


def check(struct, seq=None):
    errors = []
    for i, c in enumerate(struct):
        if c not in VALID:
            errors.append(f"bad char {c!r} at position {i}")
    stack = []
    for i, c in enumerate(struct):
        if c in OPENERS:
            stack.append((c, i))
        elif c in CLOSERS:
            if not stack or stack[-1][0] != PAIRS[c]:
                errors.append(f"unmatched {c!r} at position {i}")
            else:
                _, j = stack.pop()
                # Verify the paired bases form a valid base pair.
                if seq is not None and len(seq) == len(struct):
                    b1, b2 = seq[j], seq[i]
                    if not is_valid_pair(b1, b2):
                        errors.append(
                            f"invalid base pair {b1}-{b2} "
                            f"at positions {j}/{i}"
                        )
    for c, i in stack:
        errors.append(f"unmatched {c!r} at position {i}")
    if seq is not None and len(seq) != len(struct):
        errors.append(f"length mismatch: seq={len(seq)} struct={len(struct)}")
    return errors


def parse(path):
    name = seq = None
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith('>'):
                seq = line[1:]
            elif set(line) <= VALID:
                yield name, seq, line
                name = seq = None
            else:
                name = line


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'adar_library_1.txt'
    all_ok = True
    for name, seq, struct in parse(path):
        errs = check(struct, seq)
        if errs:
            all_ok = False
            print(f"INVALID  {name}")
            for e in errs:
                print(f"         - {e}")
        else:
            print(f"OK       {name}  (len {len(struct)})")
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
