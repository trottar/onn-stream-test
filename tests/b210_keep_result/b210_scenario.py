# B210: run inside B114's child by b114_scenario.py's `b210` mode — B178's hub scenario as it is (the add-a-game path
# for a made-up score title, then the hub's endings: two ended, a tie, two unreadable finals), and before the child
# answers, what the hub kept under the title's code (the played/ folders: each one's read.json and its pictures).
_b178_finish = finish


def finish(hung_at=None):
    try:
        home_ = Path(os.environ["PRIVYHUB_ADD_GAME_HOME"])
        kept_ = []
        for d_ in sorted(home_.glob("T*/played/*")):
            rj_ = json.loads((d_ / "read.json").read_text())
            kept_.append({"code": d_.parent.parent.name, "read": rj_, "pictures": len(list(d_.glob("f*.jpg"))),
                          "text": (d_ / "read.json").read_text()})
        S["played"] = kept_
        S["played_names"] = [title, str(root)]
        S["result_rows"] = [r_.get("step") for r_ in rows() if r_.get("step", "").startswith("result_")]
    except Exception:
        import traceback as tb_
        S["played_error"] = tb_.format_exc()[-2000:]
    _b178_finish(hung_at)


exec(compile(Path(args["b178_dir"], "b178_scenario.py").read_text(), "b178_scenario.py", "exec"))
