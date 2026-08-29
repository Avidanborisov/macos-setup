"""macsetup command-line interface."""

import argparse
import sys

from . import util
from .util import bold, dim, green, red, yellow
from .components import ALL


def _select(names):
    if not names:
        return ALL
    by_name = {c.name: c for c in ALL}
    unknown = [n for n in names if n not in by_name]
    if unknown:
        print(red(f"unknown component(s): {', '.join(unknown)}"))
        print("available: " + ", ".join(by_name))
        sys.exit(2)
    return [by_name[n] for n in names]


def cmd_list(_args):
    for comp in ALL:
        extra = dim(" [adoptable]") if comp.adoptable() else ""
        print(f"  {bold(comp.name):<24} {comp.description}{extra}")


def cmd_status(args):
    verbose = getattr(args, "verbose", False)
    drift = 0
    for comp in _select(args.components):
        checks = comp.checks()
        bad = [c for c in checks if not c.ok]
        drift += len(bad)
        mark = green("ok") if not bad else red(f"{len(bad)} drifted")
        print(f"{bold(comp.name):<24} {mark}")
        shown = checks if verbose else bad
        for c in shown:
            m = green("+") if c.ok else red("-")
            print(f"    {m} {c.name}")
            if not c.ok or verbose:
                print(f"        expected: {c.expected}")
                print(f"        actual:   {c.actual}")
            if c.note:
                print(f"        {yellow(c.note)}")
    print()
    if drift:
        print(red(f"{drift} setting(s) drifted.") + " Run `macsetup apply` to converge.")
        return 1
    print(green("Everything matches the desired configuration."))
    return 0


def cmd_apply(args):
    failed = 0
    for comp in _select(args.components):
        bad = [c for c in comp.checks() if not c.ok]
        if not bad and not args.force:
            print(f"{bold(comp.name):<24} {green('ok')} {dim('(nothing to do)')}")
            continue
        actions = comp.apply()
        for a in actions:
            colour = red if a.startswith(("FAILED", "SKIPPED")) else green
            print(f"{bold(comp.name):<24} {colour(a)}")
        still_bad = [c for c in comp.checks() if not c.ok]
        if still_bad:
            failed += len(still_bad)
            print(f"{bold(comp.name):<24} {red('still drifted after apply:')}")
            for c in still_bad:
                print(f"    - {c.name}: expected {c.expected}, actual {c.actual}"
                      + (f" ({c.note})" if c.note else ""))
    manual = [(comp.name, step) for comp in _select(args.components)
              for step in comp.manual]
    if manual:
        print(bold("\nManual steps (verify these are done):"))
        for name, step in manual:
            print(f"  [{name}] {step}")
    return 1 if failed else 0


def cmd_diff(args):
    args.verbose = True
    return cmd_status(args)


def cmd_adopt(args):
    comps = _select(args.components)
    any_adopted = False
    for comp in comps:
        if not comp.adoptable():
            if args.components:  # only complain when explicitly requested
                print(f"{bold(comp.name):<24} {yellow('not adoptable (not a file component)')}")
            continue
        actions = comp.adopt()
        for a in actions:
            print(f"{bold(comp.name):<24} {green(a)}")
            any_adopted = True
    if not any_adopted:
        print("Nothing to adopt — repo copies already match the live files.")
    else:
        print(dim("\nReview with `git diff` and commit the adopted changes."))
    return 0


def cmd_doctor(args):
    status_rc = cmd_status(argparse.Namespace(components=args.components, verbose=False))
    print(bold("\nAdvisories:"))
    warnings = []
    for comp in _select(args.components):
        warnings.extend(comp.warnings())
    if not warnings:
        print(green("  none — no conflicts or problems detected"))
    for w in warnings:
        print(f"  {yellow('!')} {bold(w.name)}")
        print(f"      {w.detail}")
        if w.fix:
            print(f"      fix: {w.fix}")
    return 1 if (status_rc or warnings) else 0


def cmd_test(args):
    rc = cmd_status(argparse.Namespace(components=args.components, verbose=False))
    if args.interactive:
        from . import interactive
        if not sys.stdin.isatty():
            print(red("interactive tests need a real terminal"))
            return 1
        ok = interactive.run_interactive(include_gui=not args.keys_only)
        return 0 if (ok and rc == 0) else 1
    print(dim("\n(automated checks only — run `macsetup test -i` in Ghostty "
              "for keypress + GUI verification)"))
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="macsetup",
        description="Provision and verify this Mac's Windows-style keyboard/window "
                    "setup and preferred tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, fn, help_, extra=None):
        p = sub.add_parser(name, help=help_)
        p.add_argument("components", nargs="*",
                       help="limit to specific components (see `macsetup list`)")
        if extra:
            extra(p)
        p.set_defaults(fn=fn)
        return p

    sub.add_parser("list", help="list managed components").set_defaults(
        fn=cmd_list, components=[])
    add("status", cmd_status, "show drift between desired and live state")
    add("diff", cmd_diff, "like status, but show every check with expected/actual")
    add("apply", cmd_apply, "converge the system to the desired state",
        extra=lambda p: p.add_argument("--force", action="store_true",
                                       help="re-apply even when checks pass"))
    add("adopt", cmd_adopt, "copy live config files back into the repo")
    add("doctor", cmd_doctor, "status + conflict/permission advisories")
    add("test", cmd_test, "verify the setup works",
        extra=lambda p: (
            p.add_argument("-i", "--interactive", action="store_true",
                           help="prompt for real keypresses and GUI confirmation"),
            p.add_argument("--keys-only", action="store_true",
                           help="interactive: only the terminal key tests")))

    args = parser.parse_args(argv)
    try:
        return args.fn(args) or 0
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130
