# D-127 — Incorrect-guide durable intent runtime acceptance — 2026-09-17

**Classification:**

`D127_INCORRECT_GUIDE_DURABILITY_CONFIRMED`

Measured:

- Android marked rows: 1;
- Linux durable state matched the marked row;
- `manual_hidden = 0`;
- `auto_hidden = 0`;
- rejected guide source key present;
- incorrect-guide timestamp present;
- problems: none.

Conclusion:

D-127 is runtime accepted. Incorrect-guide intent survives Linux-authoritative
sync without hiding the channel.
