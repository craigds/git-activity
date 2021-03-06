#!/usr/bin/env python3
import argparse
from collections import defaultdict
import datetime
import os
import subprocess
import sys


def die(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(
        description="Summarize git activity on other branches"
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--days",
        action="store",
        type=int,
        default=30,
        help="How far back to look for activity",
        metavar="DAYS",
    )
    parser.add_argument(
        "--max-changes",
        action="store",
        type=int,
        default=None,
        help="Only show files/dirs with less than this number of changed lines (sums additions & deletions)",
        metavar="CHANGES",
    )
    parser.add_argument(
        "--only-filenames",
        action="store_true",
        default=False,
        help="Only show filenames (only really useful with `--max-changes=N`)",
    )
    parser.add_argument(
        '--remote',
        type=str,
        default=None,
        help="Which remote? Defaults to remote for current branch",
        metavar='REMOTE',
    )
    parser.add_argument("files", nargs="+", metavar="FILE")

    args = parser.parse_args()

    # Get branch name
    try:
        branch_name = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        die("Couldn't get git branch name; is this a git repository?")
        sys.exit(1)

    if args.verbose:
        print(f"Current branch: {branch_name}")

    # Get remote name
    if args.remote:
        remote_name = args.remote
    else:
        try:
            remote_name = (
                subprocess.check_output(
                    ["git", "config", f"branch.{branch_name}.remote"]
                )
                .strip()
                .decode("utf-8")
            )
        except subprocess.CalledProcessError:
            die("Couldn't detect a remote for the current branch.")
            sys.exit(1)

    if args.verbose:
        print(f"Remote name: {remote_name}")

    # Check all file args actually exist
    for f in args.files:
        if not os.path.exists(f):
            die(f"{f} doesn't exist")

    # Fetch to make sure remote branch info is up to date
    if args.verbose:
        print(f"Fetching from remote")
    subprocess.check_call(["git", "fetch", remote_name])

    if args.verbose:
        print(f"Finding remote branches")
    remote_branches = (
        subprocess.check_output(
            ["git", "branch", "--remote", "--format", "%(authordate) %(refname)"]
        )
        .strip()
        .decode("utf-8")
        .splitlines()
    )
    # "Fri Oct 12 16:36:58 2018 +1300 refs/remotes/origin/api-add-version-filter"
    # split into datetime part and remote name part
    remote_branches = [line.split(" refs/remotes/") for line in remote_branches]

    # convert to datetime objects, sort, and remove all the ones not modified 'recently'
    limit_timestamp = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        args.days
    )
    remote_branches = [
        b
        for (timestamp, b) in remote_branches
        if datetime.datetime.strptime(timestamp, "%a %b %d %H:%M:%S %Y %z")
        >= limit_timestamp
    ]

    if args.verbose:
        print(
            f"Diffing {len(remote_branches)} remote branches modified in the last {args.days} days"
        )

    additions = defaultdict(int)
    deletions = defaultdict(int)
    for remote_branch in remote_branches:
        stat = (
            subprocess.check_output(
                ["git", "diff", "--numstat", f"...{remote_branch}", *args.files]
            )
            .strip()
            .decode("utf-8")
        )
        for line in stat.splitlines():
            (file_additions, file_deletions, path) = line.strip().split()
            try:
                additions[path] += int(file_additions)
                deletions[path] += int(file_deletions)
            except ValueError:
                # binary files don't have integer line counts
                pass

    for path in args.files:
        if args.max_changes is not None:
            total_changes = deletions[path] + additions[path]
            if total_changes > args.max_changes:
                continue
        if args.only_filenames:
            print(path)
        else:
            # prefix negative number with a minus, even if it's zero.
            # (f'{-deletions[path]:-8d}' doesn't add the minus if it's zero)
            deletions_str = f'-{deletions[path]}'
            print(f"{additions[path]:+8d} {deletions_str:>8s} {path}")


if __name__ == "__main__":
    main()
