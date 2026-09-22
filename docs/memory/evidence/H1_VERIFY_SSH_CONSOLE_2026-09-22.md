---
memory_schema: 1
as_of: 2026-09-22
status: EVIDENCE — H1-VERIFY, the SSH console and LightDM autologin the user built by hand, checked from a session; read-only on the host except the companion restart the task asks for; no addresses recorded
---

# H1-VERIFY — the console works before the screen goes

Task: `handoffs/H1_VERIFY_TASK.md`. Gate met: the user ran the three `H1`
blocks in `handoffs/PLAN_WEEK_2026-09-21.md`, wrote the LightDM autologin
drop-in from `D-BASE-H2_TASK.md` pre-flight item 2, and rebooted with the
monitor attached (`system boot 2026-09-22 10:55`, uptime 4 min at the
first check).

**No root write.** Nothing under `/etc` was created, edited or read with
`sudo`. The only state this session changed on the host is the companion
process: it was not running when the session started, a `tmux` copy was
started and stopped for check 4, and the companion was then left running
the usual way.

**Result: checks 1-4 pass. Check 5 fails** — the onn is not reachable over
adb and no reconnect sequence could be found from the host alone. That is
a **stop for `H2` check 2**, not for `H1`. Section 5 has the detail.

---

## 1. sshd — up, key-only, root off. PASS

```
$ systemctl is-active ssh
active

$ ss -ltn | grep ':22 '
LISTEN 0  128   0.0.0.0:22   0.0.0.0:*
LISTEN 0  128      [::]:22      [::]:*
```

`sudo -n sshd -T` was **refused** (this session holds no passwordless
sudo), so the configuration was read from the files instead, as the task
allows:

```
$ grep -nE '^\s*#?\s*(PasswordAuthentication|PermitRootLogin|KbdInteractiveAuthentication|PubkeyAuthentication|Include)' /etc/ssh/sshd_config
12:Include /etc/ssh/sshd_config.d/*.conf
33:PermitRootLogin no
38:#PubkeyAuthentication yes
57:PasswordAuthentication no
64:KbdInteractiveAuthentication no

$ ls /etc/ssh/sshd_config.d/
(empty)
```

`/etc/ssh/sshd_config.d/` is **empty**, so nothing overrides the main file
and the `Include` on line 12 pulls in nothing. Required values, all met:
password auth **no**, root login **no**, keyboard-interactive **no**,
pubkey **yes** (line 38 is commented, and the compiled-in default is
`yes` — this is the one value not asserted by an explicit line, and it is
proven in practice by the user's key login having worked).

Authorised key:

```
$ stat -c '%a %U:%G %n' ~/.ssh ~/.ssh/authorized_keys
700 privyhub:privyhub /home/privyhub/.ssh
600 privyhub:privyhub /home/privyhub/.ssh/authorized_keys

$ ssh-keygen -lf ~/.ssh/authorized_keys | awk '{print $1, $NF}'
256 (ED25519)
```

**One key, ED25519, mode 600 in a 700 directory.** Type only; the key and
its comment are not recorded here.

## 2. Autologin — an active X11 session on seat0, unlocked. PASS

```
$ loginctl list-sessions
SESSION  UID USER     SEAT  LEADER CLASS   TTY IDLE SINCE
      1 1000 privyhub seat0 1483   user    -   no   -
      2 1000 privyhub -     1523   manager -   no   -

$ loginctl show-session 1 -p Type -p State -p Remote -p Active -p Name -p Service -p Class
Name=privyhub
Remote=no
Service=lightdm-autologin
Type=x11
Class=user
Active=yes
State=active
```

`Type=x11`, `State=active`, `Remote=no`, on `seat0`, owned by the project
user. **`Service=lightdm-autologin` is the proof no one typed a password**
— PAM opened the session through LightDM's autologin service, not its
greeter, after a boot four minutes earlier.

The drop-in, quoted whole:

```
$ cat /etc/lightdm/lightdm.conf.d/10-autologin.conf
[Seat:*]
autologin-user=privyhub
autologin-session=xfce
```

`-rw-r--r-- root root`, written 2026-09-22 10:42, i.e. before the 10:55
boot that it then drove. Both keys `H2` pre-flight item 2 asks for are
present and match.

**Not locked**, and it has no way to lock itself:

```
$ light-locker-command -q
The screensaver is inactive

$ pgrep -a light-locker
2303 light-locker            # no arguments — defaults

$ xset q
Screen Saver:  timeout: 0   cycle: 600   prefer blanking: yes

$ xfconf-query -c xfce4-power-manager -l -v | grep -iE 'dpms'
/xfce4-power-manager/dpms-on-ac-off    0
/xfce4-power-manager/dpms-on-ac-sleep  0
```

`light-locker` is running, but the X screensaver timeout is **0** and DPMS
on AC is **off**, so there is no idle event to trigger it. Worth keeping
in view for the headless period: `light-locker` locks by switching to the
greeter VT, which would take the X session out from under `x11grab`. It
is inert today because nothing arms it — not because it was removed.

## 3. The capture path from a bare shell — `DISPLAY=:0` alone is enough. PASS

The task's emulation of an SSH environment, verbatim:

```
$ env -i HOME=$HOME PATH=$PATH DISPLAY=:0 bash -c 'xrandr --current | head -3; xdotool getactivewindow getwindowname'
Screen 0: minimum 320 x 200, current 1440 x 900, maximum 16384 x 16384
DisplayPort-0 connected 1440x900+0+0 (normal left inverted right x axis y axis) 408mm x 255mm
   1440x900      59.89*+  74.98
Claude
```

X answers. **No `XAUTHORITY` export is needed**, and the reason is
stronger than "`HOME` let Xlib find the cookie" — the server grants the
project user directly:

```
$ DISPLAY=:0 xhost
access control enabled, only authorized clients can connect
SI:localuser:privyhub

$ env -i PATH=$PATH DISPLAY=:0 HOME=/nonexistent bash -c 'xrandr --current | head -1'
Screen 0: minimum 320 x 200, current 1440 x 900, maximum 16384 x 16384
```

With `HOME` pointed at a path that does not exist — so no cookie can be
read — X still answers, because the access list carries the
server-interpreted entry **`SI:localuser:privyhub`**. Any local process
running as `privyhub` is authorised whatever its environment.

**What the SSH console must export: `DISPLAY=:0`, and nothing else.**
`/home/privyhub/.Xauthority` exists (mode 600, rewritten at the 10:55
boot) and `XAUTHORITY=/home/privyhub/.Xauthority` is set inside the
desktop session, but passing it is optional here. Note the desktop session
and the running companion carry `DISPLAY=:0.0`; `:0` and `:0.0` both
resolve to the same screen and either works.

This is the check that decided whether the companion can be started from
SSH at all. **It can.**

## 4. tmux, and the companion started from it. PASS

The companion was **not running** when this session started — `pgrep` found
only the shell wrapper, and 8765 was free — so the task's start path was
run in full rather than skipped.

```
$ tmux new -d -s privyhub 'cd ~/Projects/onn-stream-test && DISPLAY=:0 python3 ./companion/privyhub_service.py'
$ sleep 10
$ tmux ls
privyhub: 1 windows (created Tue Sep 22 11:00:26 2026)
r3: 1 windows (created Tue Sep 22 10:58:52 2026) (attached)

$ ps -eo pid,cmd | awk '/[p]ython3 \.\/companion\/privyhub_service\.py/{print}'
4673 python3 ./companion/privyhub_service.py

$ ss -lntp | grep 8765
LISTEN 0 5  0.0.0.0:8765  0.0.0.0:*  users:(("python3",pid=4673,fd=4))

$ curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json; s=json.load(sys.stdin); print(s['ready'], s['encoder_overrides']['any_override'])"
True False
```

**`True False`, as required** — and pid 4673 is the process holding 8765,
per the `TOOLS.md` rule that something answering is not evidence the new
process is the one answering.

Then stopped, and the companion restarted the usual way:

```
$ tmux kill-session -t privyhub
$ ss -lntp | grep 8765
(8765 free)                      # the companion dies with its tmux session

$ nohup python3 ./companion/privyhub_service.py > <scratch>/companion.log 2>&1 &
$ ps -eo pid,cmd | awk '/[p]ython3 \.\/companion\/privyhub_service\.py/{print}'
4742 python3 ./companion/privyhub_service.py
$ ss -lntp | grep 8765
LISTEN 0 5  0.0.0.0:8765  0.0.0.0:*  users:(("python3",pid=4742,fd=4))
$ tr '\0' '\n' < /proc/4742/environ | grep -E '^(DISPLAY|XAUTHORITY)='
XAUTHORITY=/home/privyhub/.Xauthority
DISPLAY=:0.0
$ curl -s localhost:8765/plugins/games/native-stream-status | ...
True False
```

**The companion is left running as pid 4742**, inheriting `DISPLAY=:0.0`
from this session.

**`Linger=no` is unchanged** (`loginctl show-user privyhub -p Linger`).
The tmux server is a child of the user session and is killed at logout, as
it always was. With autologin in force there is no logout on a reboot —
the session comes back by itself — so in practice the loss is: **a reboot
kills the tmux server and everything in it, and nothing brings the
companion back.** There is still no unit, no crontab entry and no linger;
`H2` item 4 already expects the companion to be started by hand after every
reboot, and this check does not change that.

## 5. adb after the reboot — the onn is NOT reachable. FAIL

```
$ adb devices
* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
                                 # empty
```

No device. adb on this host is **wireless only** — `lsusb` lists a root
hub set, a mouse, and nothing else; there is no USB path to fall back to.
Two recovery routes were tried, and the task's two-attempt limit was
respected:

| attempt | command | result |
| --- | --- | --- |
| 1 | `adb mdns services` | `List of discovered mdns services` — empty |
| 2 | `adb mdns check` | no output at all |
| 1 | `adb connect <last known endpoint>` | `failed to connect: Connection refused` |

The endpoint came from the host's shell history (11 prior `adb connect`
calls, **every one on a different high port**). `Connection refused`
rather than a timeout is the expected signature of the known **ephemeral
port rotation** — `patches/ADB_EPHEMERAL_PORT_RECOVERY_PROBE_V2_2026-09-15.md`
and `investigations/ADB_STALE_CACHE_NATIVE_ERROR_2026-09-14.md` — where
the TV's wireless-debugging listener comes back on a new port after a
restart, so every stored endpoint is dead on arrival.

`2026-09-20.md` records the sequence that worked that day —
`adb reconnect offline`, then `adb connect <endpoint>` — but it **cannot
apply here**: it presumes a known-good current endpoint, and the port is
exactly what has been lost. The address-free route, mDNS discovery, found
nothing; the openscreen backend on this adb answers `adb mdns check` with
silence.

**What this means, and the smallest fix.** The current port is displayed
on the TV, under *Developer options → Wireless debugging*, and reading it
needs the onn's own screen and remote. **`H1-VERIFY` cannot close this gap
and neither can `H2`**: `H2` check 2 depends on adb, so the cutover is
blocked on a reconnect that only the user can perform, from the TV. The
durable fix — so a host reboot stops costing a trip to the TV — is either
`adb tcpip 5555` while the device is connected once (a fixed port that
survives restarts), or a pairing recorded such that mDNS discovery works;
neither is in `TOOLS.md` today, and neither is authorised by this task.
**Recommendation for the user, before the plug goes in: reconnect the onn
from the TV, then run `adb tcpip 5555` and confirm `adb connect` on the
fixed port survives a TV restart.** That is the one action that makes
`H2` check 2 runnable without the monitor.

---

## Summary

| # | check | verdict |
| --- | --- | --- |
| 1 | sshd active on 22, key-only, root off, one ED25519 key at 600 | **PASS** |
| 2 | active X11 autologin session on seat0, unlocked, drop-in correct | **PASS** |
| 3 | X answers a bare shell with only `DISPLAY=:0` | **PASS** |
| 4 | companion from tmux reports `True False`; restarted normally | **PASS** |
| 5 | adb lists the onn | **FAIL** — no reconnect possible from the host |

`H1` itself is **done**: there is a console that survives the monitor
coming off, and a session that comes up without a keyboard. `H2` stays
gated on the plug **and now also on the user reconnecting adb from the
TV**.

**Redaction.** No addresses, MACs, SSIDs, key material, serials or device
identifiers appear above. Ports are recorded as bare numbers (22, 8765,
5037, 5555); the one historical adb port quoted in the attempt table was
replaced by `<last known endpoint>`.
