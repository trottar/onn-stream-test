#!/usr/bin/env python3
"""Queue BI B189: T90 through the tool from its seven kept saves, in a scratch copy of its add_game folder (the real
folder, the rules folder and the user's slots only read). The title for register's library lookup is read from the
copy's binding in process — never on a command line, never printed. usage:
  t90_run.py <tools folder> <scratch> register|label <readings...>|label-look <answer>|learn"""
import contextlib, io, json, os, sys
tools, scratch, stage = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ.update({"PRIVYHUB_ADD_GAME_HOME": f"{scratch}/home", "PRIVYHUB_ADD_GAME_EVIDENCE": f"{scratch}/ev",
                   "PRIVYHUB_H7_RULES": f"{scratch}/rules", "PRIVYHUB_ADD_GAME_LOGS": f"{scratch}/logs",
                   "PRIVYHUB_ADD_GAME_ASK": f"{scratch}/ask"})
os.makedirs(f"{scratch}/rules", exist_ok=True)
sys.path.insert(0, tools)
import party_add_game as pag
if stage == "register":
    words = json.load(open(f"{scratch}/home/T90/binding.json"))["title"]
    argv = ["register", "T90", "--players", "2", "--system", "ps1", "--result", "score", "--setup", "none",
            "--find", words]
else:
    argv = [stage, "T90", *sys.argv[4:]]
sys.exit(pag.main(argv))
