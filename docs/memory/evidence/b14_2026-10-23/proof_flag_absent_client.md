# B14 (client) — property absent = the predecessors (only added lines, all in the allowed forms)

| file | removed / changed | added | outside the forms |
| --- | ---: | ---: | ---: |
| `NativeStreamActivity.kt` | **0** | 55 | **0** |
| `DiagnosticsActivity.kt` | **0** | 15 | **0** |

Result: **PROVEN**. New file `LinkNotice.kt` is reached only through `linkNotice` (null without the property) and the diagnostics page's flag check.

### NativeStreamActivity.kt

```
                // B14: the link notice from the client's own link reading (null = today)
                linkNotice?.let { tickLinkNotice(it) }

        // B14: the link notice's line, bottom-left over the picture (null = today: no view)
        if (linkNotice != null) {
            val notice = TextView(this).apply {
                setTextColor(Color.WHITE)
                setBackgroundColor(0xCC000000.toInt())
                textSize = 15f
                setPadding(20, 12, 20, 12)
                visibility = View.GONE
            }
            noticeView = notice
            root.addView(notice, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT
            ).apply { gravity = Gravity.BOTTOM or Gravity.START; setMargins(24, 24, 24, 24) })
        }
        // B14: a new session re-arms the link notice (null = today)
        linkNotice?.onSessionStart()
        noticeView?.visibility = View.GONE
        // B14: the link notice's count and last reasons (null = today: no key)
        linkNotice?.let { n ->
            root.put("link_notice_shown", n.shownCount)
            root.put("link_notice_last_reasons", n.lastReasons)
        }


    // B14: the link notice, only with debug.privyhub.link_notice=1 (null = today); its own sampler if link_report=0.
    private val linkNotice: LinkNotice? by lazy { if (LinkNoticeFlag.fromSystem()) LinkNotice() else null }
    private val noticeSampler: LinkSampler? by lazy {
        if (linkNotice != null && linkSampler == null) LinkSampler({ readWifi(applicationContext) }) else null
    }
    private var noticeView: TextView? = null

    // B14: one evaluation per UI tick; the view and the diagnostics page's line follow the transitions
    private fun tickLinkNotice(n: LinkNotice) {
        if (!sessionStarted) return
        val s = (linkSampler ?: noticeSampler)?.current()
        when (val ev = n.update(s, System.nanoTime() / 1_000_000L)) {
            is LinkNotice.Event.Shown -> {
                noticeView?.text = ev.text
                noticeView?.visibility = View.VISIBLE
                LinkNoticeStatus.lastText = ev.text
                LinkNoticeStatus.lastShownAtMs = System.currentTimeMillis()
                LinkNoticeStatus.showing = true
            }
            LinkNotice.Event.Cleared -> {
                noticeView?.visibility = View.GONE
                LinkNoticeStatus.showing = false
            }
            null -> {}
        }
    }
                // B14: the link notice's state (null = today: nothing)
                (linkNotice?.query() ?: "") +
```

### DiagnosticsActivity.kt

```
// B14: the link notice's last line (only with debug.privyhub.link_notice=1)
import com.safeiot.privyhub.streaming.LinkNoticeFlag
import com.safeiot.privyhub.streaming.LinkNoticeStatus

        // B14: the last link notice, while the app runs (absent = today: no view)
        if (LinkNoticeFlag.fromSystem()) {
            content.addView(
                TextView(this).apply {
                    text = LinkNoticeStatus.lastText?.let { "Last link notice:\n$it" } ?: "Link notice: none shown"
                    textSize = 15f
                    setTextColor(Color.WHITE)
                },
                ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            )
        }
```

