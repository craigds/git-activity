#!/usr/bin/env python3
import argparse
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
    try:
        remote_name = (
            subprocess.check_output(["git", "config", f"branch.{branch_name}.remote"])
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
    for dirname in args.files:
        additions = 0
        deletions = 0
        for remote_branch in remote_branches:
            stat = (
                subprocess.check_output(
                    ["git", "diff", "--numstat", f"..{remote_branch}", dirname]
                )
                .strip()
                .decode("utf-8")
            )
            for line in stat.splitlines():
                (file_additions, file_deletions) = line.split()[:2]
                additions += int(file_additions)
                deletions += int(file_deletions)

        print(f"{additions:+8d} {-deletions:-8d} {dirname}")


if __name__ == "__main__":
    main()
