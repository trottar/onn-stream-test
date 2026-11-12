# B100 — design addendum 1 (2026-11-12, before the fix's code)

Found by the first full run: B98's byte-for-byte checks against B97 failed — the `not_tested` mark was also set on the
fold rows of a template **untestable as a whole** (template h without hints), whose folds B97 lists unmarked. Such a
template is "none" already; the mark means "this template was tested on all states but not on the others". **The mark
moves from `_fold` to `_report`'s testable path**: rows skipped as "the template is not testable on the other states"
in a template that is testable on all states get `not_tested: true`; a template untestable as a whole keeps B97's rows.
