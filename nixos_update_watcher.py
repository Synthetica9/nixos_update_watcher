#! /usr/bin/env nix-shell
#! nix-shell -i python -p "python3"

from time import sleep
from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime, timedelta
import textwrap
from random import randint

from signal import signal, SIG_IGN, SIGALRM

from tools import *

URL_PAT = "https://channels.nix.gsc.io/{channel}/history"

PATH_PAT = "/nix/var/nix/profiles/per-user/{user}/channels/{name}/svn-revision"
OUTFILE = "/tmp/nixos_update_message.txt"

# TODO: autodetect this.
USERS = {
    "root": {"nixos": "nixos-unstable"}
}


def shorten_revision(long_revision):
    return long_revision[:11]


def update_info_file():
    with open(OUTFILE, "w"): pass  # clear the file

    for (user, channels) in USERS.items():
        for (name, channel) in channels.items():
            print(user, name, channel)
            path = PATH_PAT.format(user=user, name=name)
            with open(path) as f:
                contents = f.read().strip()
                _, localRevision = contents.split(".")

            url = URL_PAT.format(channel=channel)

            localTimestamp = None
            for _ in range(100):
                try:
                    with urlopen(url) as f:
                        for line in f:
                            line = line.decode("UTF8").strip()
                            latestRevision, latestTimestamp = line.split()

                            latestRevision = shorten_revision(latestRevision)
                            latestTimestamp = datetime.fromtimestamp(int(latestTimestamp))

                            if localRevision == latestRevision:
                                print(latestRevision, latestTimestamp)
                                localTimestamp = latestTimestamp
                except URLError as e:
                    print(e)
                    sleep(5)
                else:
                    break
            else:
                return

            with open(OUTFILE, "a") as outfile:
                if localTimestamp is None:
                    outfile.write("Failure to get channel info, there might be updates.\n")

                elif localTimestamp < latestTimestamp:
                    message = [
                        f"Channel {channel} ({name}) for {user} is out-of-date.",
                        f"Latest revision is {latestRevision}, "
                        f"from {latestTimestamp}."
                    ]

                    if user == "root":
                        message.extend([
                            "Suggested course of action: "
                            "run `sudo nixos-rebuild switch --upgrade`"
                        ])

                    outfile.write(textwrap.fill("  ".join(message), 60))


def follow_waiting_protocol():
    # This service is provided for free.
    #
    # If you use this service automatically please be
    # polite and follow some rules:
    #
    #   - please don't poll any more often than every 15
    #     minutes, to reduce the traffic to my server.
    #
    #   - please don't poll exactly on a 5 minute
    #     increment, to avoid the "thundering herd"
    #     problem.
    #
    #   - please add a delay on your scheduled polling
    #     script for a random delay between 1 and 59
    #     seconds, to further spread out  the load.
    #
    #   - please consider using my webhooks instead:
    #     email me at graham at grahamc dot com or
    #     message gchristensen on #nixos on Freenode.
    #
    # Thank you, good luck, have fun
    # Graham

    base_sleep = timedelta(minutes=15)
    random_sleep = timedelta(seconds=randint(1, 60 * 5))
    total_sleep = base_sleep + random_sleep

    print(f"sleeping for {base_sleep} + {random_sleep} = {total_sleep}")
    sleep(total_sleep)


def main():
    signal(SIGALRM, SIG_IGN)
    with running_once("nixos_update_watcher"):
        while True:
            update_info_file()
            with signal_interruptable():
                follow_waiting_protocol()


if __name__ == '__main__':
    main()
