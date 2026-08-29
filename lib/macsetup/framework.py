"""Component framework: every managed piece of setup is a Component."""

from dataclasses import dataclass, field

from . import util


@dataclass
class Check:
    """One verifiable assertion about system state."""
    name: str
    ok: bool
    expected: str = ""
    actual: str = ""
    note: str = ""  # remediation hint for things `apply` can't fix


@dataclass
class Warning_:
    """Doctor-level advisory (conflict, stale entry, permission concern)."""
    name: str
    detail: str
    fix: str = ""  # shell command or instruction


class Component:
    """A unit of managed configuration.

    checks()  -> list[Check]   report desired vs actual, no side effects
    apply()   -> list[str]     converge (idempotent), return actions taken
    adopt()   -> list[str]     pull live state back into the repo (file comps)
    warnings()-> list[Warning_] doctor-only advisories
    manual    -> list[str]     steps only the user can do (TCC grants, etc.)
    """

    name = ""
    description = ""
    manual: list = []

    def checks(self):
        return []

    def apply(self):
        return []

    def adoptable(self):
        return False

    def adopt(self):
        return []

    def warnings(self):
        return []


class FileComponent(Component):
    """Config files copied from the repo to system locations.

    pairs: list of (repo_relative_src, dest_path, mode_or_None)
    """

    pairs = []  # list of (src_path, dest_path, mode_or_None)
    restart_note = ""

    def _resolved(self):
        yield from self.pairs

    def checks(self):
        out = []
        for src, dest, _mode in self._resolved():
            if not src.exists():
                out.append(Check(f"{dest}", False, "repo file exists", "missing from repo",
                                 note=f"expected at {src}"))
                continue
            ok = util.files_match(src, dest)
            actual = "matches repo" if ok else ("missing" if not dest.exists() else "differs from repo")
            out.append(Check(str(dest).replace(str(util.HOME), "~"), ok,
                             "matches repo", actual))
        return out

    def apply(self):
        actions = []
        for src, dest, mode in self._resolved():
            if not src.exists():
                continue
            if util.install_file(src, dest, mode):
                actions.append(f"installed {dest}")
        if actions and self.restart_note:
            actions.append(self.restart_note)
        return actions

    def adoptable(self):
        return True

    def adopt(self):
        actions = []
        for src, dest, _mode in self._resolved():
            if dest.exists() and not util.files_match(src, dest):
                src.parent.mkdir(parents=True, exist_ok=True)
                src.write_bytes(dest.read_bytes())
                actions.append(f"adopted {dest} -> {src.relative_to(util.REPO)}")
        return actions


@dataclass
class DefaultsSpec:
    """Desired values for keys in one defaults domain."""
    domain: str
    values: dict = field(default_factory=dict)

    def checks(self, prefix=""):
        live = util.defaults_export(self.domain)
        out = []
        for key, want in self.values.items():
            have = live.get(key)
            ok = util.norm(have) == util.norm(want)
            out.append(Check(f"{prefix}{self.domain} {key}", ok,
                             repr(util.norm(want)), repr(util.norm(have))))
        return out

    def apply(self):
        live = util.defaults_export(self.domain)
        actions = []
        for key, want in self.values.items():
            if util.norm(live.get(key)) != util.norm(want):
                util.defaults_write(self.domain, key, want)
                actions.append(f"defaults write {self.domain} {key}")
        return actions
