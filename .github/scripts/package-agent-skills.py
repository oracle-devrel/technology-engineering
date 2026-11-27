#!/usr/bin/env python3
"""Build portable skill release assets from tracked solution files."""

import argparse
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOLUTIONS = Path("oci-and-db/cloud-native/devops-and-containers")
SKILLS = {
    "devops": [
        SOLUTIONS / "devops/oci-devops-rm/files/.agents/skills/oke-devops-starter",
    ],
    "gitops": [
        SOLUTIONS / "oke/oke-gitops/files/repos/argocd/cluster-config/skills/manage-oke-with-argocd",
        SOLUTIONS / "oke/oke-gitops/files/repos/fluxcd/cluster-config/skills/manage-oke-with-flux",
    ],
}


def asset_for_tag(tag):
    for prefix, asset in (("oci-devops-rm-", "devops"), ("oke-gitops-", "gitops")):
        if tag.startswith(prefix) and tag != prefix:
            return asset
    raise ValueError(f"No agent skill assets configured for release tag: {tag}")


def package_skill(root, source, output_dir):
    root = root.resolve()
    source_dir = root / source
    entries = subprocess.check_output(
        ["git", "ls-files", "--stage", "-z", "--", source.as_posix()], cwd=root,
    ).decode().split("\0")
    files = []
    for entry in filter(None, entries):
        metadata, name = entry.split("\t", 1)
        mode, _, stage = metadata.split()
        relative = Path(name).relative_to(source)
        if mode not in ("100644", "100755") or stage != "0":
            raise ValueError(f"Skill input must be a regular, unconflicted file: {name}")
        path = root / name
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError(f"Skill input must not contain symlinks: {name}")
        files.append((relative, path, mode))
    if not any(relative == Path("SKILL.md") for relative, _, _ in files):
        raise ValueError(f"Missing tracked SKILL.md in {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{source.name}.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, path, mode in sorted(files):
            info = zipfile.ZipInfo((Path(source.name) / relative).as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = int(mode, 8) << 16
            archive.writestr(info, path.read_bytes())
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--asset", choices=[*SKILLS, "all"])
    selection.add_argument("--tag", help="Select the skills for a solution release tag")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    asset = asset_for_tag(args.tag) if args.tag else args.asset
    for selected in SKILLS if asset == "all" else [asset]:
        for source in SKILLS[selected]:
            print(package_skill(ROOT, source, args.output_dir.resolve()))


if __name__ == "__main__":
    main()
