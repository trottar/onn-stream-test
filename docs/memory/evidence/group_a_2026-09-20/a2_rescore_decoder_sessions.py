#!/usr/bin/env python3
"""Group A / A2 - re-score every decoder session on disk.

Reads logs/games/decoder_sessions/*.json directly. Writes one JSON result
next to this script (or --out). Pure stdlib + numpy/scipy for Spearman/
Mann-Whitney; the per-session table needs neither.

Selection used throughout: sessions with a decoder block, duration >= 15 s,
received 2026-09-16 or later (the 2026-09-15 bring-up sessions are excluded,
as the 2026-09-20 baseline record excluded them). The single low_latency
session (C3.L2c) is reported separately and excluded from correlations.

Usage: python3 a2_rescore_decoder_sessions.py --repo /path/to/onn-stream-test
"""
from __future__ import annotations
import argparse, csv, glob, json, math, os, statistics as st

def load(repo):
    rows=[]
    for f in sorted(glob.glob(os.path.join(repo,"logs","games","decoder_sessions","*.json"))):
        j=json.load(open(f)); r=j["report"]; dec=r.get("decoder") or {}; vid=r.get("video") or {}; aud=r.get("audio") or {}
        dur=r.get("duration_ms") or 0; mins=dur/60000 if dur else None
        disc=r.get("stream_discontinuities")
        row=dict(file=os.path.basename(f),received=j.get("received_at_utc"),dur_s=dur/1000,kbps=r.get("encoder_bitrate_kbps"),
            has_decoder=bool(dec),low_latency=dec.get("low_latency_enabled"),
            spike20=dec.get("spike_20_ms"),spike50=dec.get("spike_50_ms"),spike80=dec.get("spike_80_ms"),spike250=dec.get("spike_250_ms"),spike500=dec.get("spike_500_ms"),
            queued=dec.get("queued_frames"),rendered=dec.get("rendered_frames"),stale=dec.get("stale_output_drops"),qover=dec.get("queue_overflow_drops"),
            max_gap=dec.get("max_output_gap_ms"),max_codec=dec.get("max_codec_ms"),max_rx=dec.get("max_rx_to_decode_ms"),max_inflight=dec.get("max_codec_in_flight"),input_waits=dec.get("input_waits"),max_feed=dec.get("max_feed_delay_ms"),
            v_packets=vid.get("packets"),v_lost=vid.get("lost_packets"),v_lost_in_resyncs=(vid.get("lost_packets_in_resyncs") or 0),v_frames=vid.get("frames"),v_dropped=vid.get("dropped_frames"),
            gap_events=vid.get("forward_gap_events"),max_gap_pk=vid.get("max_forward_gap_packets"),seq_gap_au=vid.get("sequence_gap_au_drops"),
            fec_rec=vid.get("fec_recovered_packets"),fec_unrec=vid.get("fec_unrecoverable_groups"),resyncs=vid.get("sequence_resyncs"),largest_jump=vid.get("largest_resync_jump_packets"),
            wait_idr_drops=vid.get("packets_dropped_waiting_for_idr"),max_resync_to_idr=vid.get("max_resync_to_idr_ms"),late_reorder=vid.get("late_or_reordered_packets"),
            jump_packets=(sum(x["jump_packets"] for x in disc) if disc is not None else None),
            a_lost=aud.get("lost_packets"),a_under=aud.get("underruns"),a_starve=aud.get("prolonged_starvation_events"),
            slow=r.get("slow_events_ge_50_ms") or [],slow_ret=r.get("slow_event_retained"),slow_cap=r.get("slow_event_capacity"),slow_ret_recent=r.get("slow_event_retained_recent"),
            disc=disc,motion=(r.get("controller") or {}).get("motion_events"))
        if mins:
            for k in ("spike20","spike50","spike80","stale","v_lost","gap_events","a_under","a_lost","a_starve","resyncs"):
                v=row.get(k); row[k+"_pm"]=(v/mins) if v is not None else None
            row["fps"]=row["rendered"]/(dur/1000) if row["rendered"] is not None else None
            row["v_fps"]=row["v_frames"]/(dur/1000) if row["v_frames"] is not None else None
            if row["jump_packets"] is not None and row["v_lost"] is not None:
                row["loss_corrected_pm"]=(row["v_lost"]+row["jump_packets"]-row["v_lost_in_resyncs"])/mins  # post-fix reports already include resync jumps in lost_packets
        rows.append(row)
    return rows

def epoch(r):
    if r["low_latency"]: return "L2c"
    if r["received"]<"2026-09-19T01:37": return "A_pre_flatten"
    if r["received"]<"2026-09-19T02:38": return "B_flat_pre_L2b"
    return "C_post_L2b"

def med(rs,k):
    v=[r[k] for r in rs if r.get(k) is not None]; return round(float(st.median(v)),1) if v else None
def pct(rs,k,q):
    v=sorted(r[k] for r in rs if r.get(k) is not None)
    if not v: return None
    i=(len(v)-1)*q/100; lo=math.floor(i); hi=math.ceil(i); return round(v[lo]+(v[hi]-v[lo])*(i-lo),1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--out",default=None); a=ap.parse_args()
    outdir=a.out or os.path.dirname(os.path.abspath(__file__))
    rows=[r for r in load(a.repo) if r["has_decoder"]]
    BASE=[r for r in rows if r["received"]>="2026-09-16" and r["dur_s"]>=15]
    NL=[r for r in BASE if not r["low_latency"]]
    try:
        import numpy as np; from scipy import stats
        def sp(x,y):
            x=np.array(x,float); y=np.array(y,float); m=~(np.isnan(x)|np.isnan(y))
            if m.sum()<4: return None
            rho,p=stats.spearmanr(x[m],y[m]); return {"rho":round(float(rho),3),"p":float(f"{p:.2g}"),"n":int(m.sum())}
        def mwu(x,y): return float(f"{stats.mannwhitneyu(x,y).pvalue:.3g}")
        def fisher(a,b,c,d): return float(f"{stats.fisher_exact([[a,b],[c,d]])[1]:.3g}")
    except ImportError:
        sp=lambda x,y:"scipy_missing"; mwu=lambda x,y:"scipy_missing"; fisher=lambda *a:"scipy_missing"
    col=lambda rs,k:[(r[k] if r.get(k) is not None else float("nan")) for r in rs]
    out={"selection":{"decoder_sessions_on_disk":len(rows),"ge15s_from_2026-09-16":len(BASE),"excl_low_latency":len(NL),
                      "newest_50_files_ge15s":len([r for r in rows[-50:] if r["dur_s"]>=15])}}
    agg={}
    for k in ["spike20_pm","spike50_pm","spike80_pm","fps","v_fps","max_gap","max_codec","stale_pm","v_lost_pm","loss_corrected_pm","a_under_pm","max_inflight","dur_s"]:
        agg[k]={"median":med(NL,k),"p10":pct(NL,k,10),"p90":pct(NL,k,90),"min":pct(NL,k,0),"max":pct(NL,k,100),"n":sum(1 for r in NL if r.get(k) is not None)}
    out["aggregate_excl_low_latency"]=agg
    ep={}
    for e in ["A_pre_flatten","B_flat_pre_L2b","C_post_L2b","L2c"]:
        rs=[r for r in BASE if epoch(r)==e]; gaps=sorted((r["max_gap"] for r in rs),reverse=True)
        ep[e]={"n":len(rs),"spike20_pm_med":med(rs,"spike20_pm"),"spike50_pm_med":med(rs,"spike50_pm"),"fps_med":med(rs,"fps"),"stale_pm_med":med(rs,"stale_pm"),
               "max_gap_med":med(rs,"max_gap"),"max_gap_p90":pct(rs,"max_gap",90),"max_gap_top5":gaps[:5],"n_gap_gt_400":sum(1 for g in gaps if g>400),"n_gap_gt_1000":sum(1 for g in gaps if g>1000),
               "v_lost_pm_med":med(rs,"v_lost_pm"),"a_under_pm_med":med(rs,"a_under_pm")}
    A=[r for r in BASE if epoch(r)=="A_pre_flatten"]; C=[r for r in BASE if epoch(r)=="C_post_L2b"]
    ep["A_vs_C_tests"]={"max_gap_mwu_p":mwu([r["max_gap"] for r in A],[r["max_gap"] for r in C]),
        "gap_gt_1000_fisher_p":fisher(sum(1 for r in A if r["max_gap"]>1000),sum(1 for r in A if r["max_gap"]<=1000),sum(1 for r in C if r["max_gap"]>1000),sum(1 for r in C if r["max_gap"]<=1000)),
        "gap_gt_400_fisher_p":fisher(sum(1 for r in A if r["max_gap"]>400),sum(1 for r in A if r["max_gap"]<=400),sum(1 for r in C if r["max_gap"]>400),sum(1 for r in C if r["max_gap"]<=400)),
        "spike20_pm_mwu_p":mwu([r["spike20_pm"] for r in A],[r["spike20_pm"] for r in C]),"fps_mwu_p":mwu([r["fps"] for r in A],[r["fps"] for r in C]),"stale_pm_mwu_p":mwu([r["stale_pm"] for r in A],[r["stale_pm"] for r in C])}
    out["epochs"]=ep
    # latency bands
    out["latency_bands_excl_low_latency"]={"share_lt_20ms_med":round(st.median([1-r["spike20"]/r["queued"] for r in NL]),3),
        "share_20_60ms_rendered_med":round(st.median([(r["spike20"]-r["stale"])/r["queued"] for r in NL]),3),
        "share_gt_60ms_stale_dropped_med":round(st.median([r["stale"]/r["queued"] for r in NL]),3),
        "fps_deficit_network_med":round(st.median([60-r["v_fps"] for r in NL]),2),"fps_deficit_client_stale_overflow_med":round(st.median([r["v_fps"]-r["fps"] for r in NL]),2)}
    # Q1
    d=[r["dur_s"] for r in NL]; u=[r["a_under"] for r in NL]
    try:
        lr=stats.linregress(d,u); q1={"underruns_total_vs_duration_linear":{"intercept":round(float(lr.intercept),1),"slope_per_min":round(float(lr.slope)*60,2),"r":round(float(lr.rvalue),3),"p":float(f"{lr.pvalue:.2g}")}}
        resid=[(r["a_under"]-(lr.intercept+lr.slope*r["dur_s"])) for r in NL]
    except Exception:
        q1={}; resid=None
    q1["underruns_pm_vs_duration"]=sp(col(NL,"dur_s"),col(NL,"a_under_pm"))
    longs=[r for r in NL if r["dur_s"]>=300]; shorts=[r for r in NL if r["dur_s"]<40]
    q1["sessions_ge300s"]={"n":len(longs),"a_under_pm_med":med(longs,"a_under_pm"),"a_under_total_med":med(longs,"a_under")}
    q1["sessions_lt40s"]={"n":len(shorts),"a_under_pm_med":med(shorts,"a_under_pm"),"a_under_total_med":med(shorts,"a_under")}
    if resid is not None:
        for k in ["spike50_pm","spike80_pm","stale_pm","max_gap","v_lost_pm","a_lost_pm","a_starve_pm"]:
            q1["underrun_residual_vs_"+k]=sp(resid,col(NL,k))
    q1["a_starve_pm_vs_spike80_pm"]=sp(col(NL,"a_starve_pm"),col(NL,"spike80_pm"))
    q1["a_starve_pm_vs_v_lost_pm"]=sp(col(NL,"a_starve_pm"),col(NL,"v_lost_pm"))
    q1["a_lost_pm_vs_v_lost_pm"]=sp(col(NL,"a_lost_pm"),col(NL,"v_lost_pm"))
    q1["limitation"]="audio underruns exist only as session totals; no per-event timeline, so within-session co-occurrence cannot be measured from existing artifacts"
    out["Q1_audio_vs_decode"]=q1
    # Q2
    lpg=[r["v_lost"]/r["gap_events"] for r in NL if r["gap_events"]]
    mg=[r["max_gap_pk"] for r in NL if r["max_gap_pk"] is not None]
    post=[r for r in NL if r["jump_packets"] is not None]
    q2={"lost_per_gap_event":{"median":round(st.median(lpg),2),"p90":round(sorted(lpg)[int(0.9*(len(lpg)-1))],2),"max":round(max(lpg),2),"n":len(lpg),"share_sessions_gt_1_5":round(sum(1 for v in lpg if v>1.5)/len(lpg),3)},
        "max_forward_gap_packets":{"median":st.median(mg),"p90":sorted(mg)[int(0.9*(len(mg)-1))],"max":max(mg)},
        "late_or_reordered_packets_total":sum(r["late_reorder"] or 0 for r in NL),
        "resync_jumps_excluded_from_lost_packets":{"post_L2b_sessions":len(post),"lost_packets_sum":sum(r["v_lost"] for r in post),"jump_packets_sum":sum(r["jump_packets"] for r in post),
            "reported_lost_pm_med":med(post,"v_lost_pm"),"corrected_lost_pm_med":med(post,"loss_corrected_pm"),
            "reported_loss_pct":round(100*sum(r["v_lost"] for r in post)/sum(r["v_packets"] for r in post),3),
            "corrected_loss_pct":round(100*sum(r["v_lost"]+r["jump_packets"] for r in post)/sum(r["v_packets"]+r["jump_packets"] for r in post),3)},
        "lost_pm_vs_fps":sp(col(NL,"v_lost_pm"),col(NL,"fps")),"lost_pm_vs_max_gap":sp(col(NL,"v_lost_pm"),col(NL,"max_gap")),"lost_pm_vs_spike50_pm":sp(col(NL,"v_lost_pm"),col(NL,"spike50_pm")),
        "max_gap_vs_largest_resync_jump":sp(col(NL,"largest_jump"),col(NL,"max_gap")),"max_gap_vs_max_resync_to_idr":sp([r["max_resync_to_idr"] or 0 for r in NL],col(NL,"max_gap")),
        "lost_pm_median_by_day":{}}
    byday={}
    for r in NL: byday.setdefault(r["received"][:10],[]).append(r["v_lost_pm"])
    q2["lost_pm_median_by_day"]={k:round(st.median(v),1) for k,v in sorted(byday.items())}
    r2i=[x["resync_to_idr_ms"] for r in NL for x in (r.get("disc") and [] or [])]
    out["Q2_loss_burstiness"]=q2
    # Q3
    q3={"spike20_pm_vs_duration":sp(col(NL,"dur_s"),col(NL,"spike20_pm")),"spike50_pm_vs_duration":sp(col(NL,"dur_s"),col(NL,"spike50_pm")),"stale_pm_vs_duration":sp(col(NL,"dur_s"),col(NL,"stale_pm"))}
    within=[]
    for r in NL:
        ev=r["slow"]
        if not ev or r["dur_s"]<60: continue
        el=sorted(e[0] for e in ev)
        n=r["slow_ret_recent"] if r["slow_ret_recent"] is not None else len(el)
        tail=el[-n:] if n else []
        if len(tail)>=10 and tail[-1]>tail[0]:
            span=(tail[-1]-tail[0])/1000; tr=len(tail)/(span/60); wr=r["spike50"]/(r["dur_s"]/60)
            within.append({"received":r["received"],"dur_s":round(r["dur_s"],1),"tail_start_s":round(tail[0]/1000,1),"tail_window_s":round(span,1),"tail_rate_pm":round(tr,1),"whole_rate_pm":round(wr,1),"ratio":round(tr/wr,2)})
    ratios=[w["ratio"] for w in within]
    q3["tail_over_whole_ratio"]={"n":len(ratios),"median":round(st.median(ratios),2),"p10":round(sorted(ratios)[int(0.1*(len(ratios)-1))],2),"p90":round(sorted(ratios)[int(0.9*(len(ratios)-1))],2)}
    q3["per_session"]=within
    out["Q3_spike_vs_elapsed"]=q3
    # Q4
    q4={"max_inflight_distribution":{str(k):sum(1 for r in NL if r["max_inflight"]==k) for k in sorted(set(r["max_inflight"] for r in NL))}}
    for k in ["max_inflight","v_lost_pm","loss_corrected_pm","spike50_pm","spike80_pm","max_codec","max_gap","fps","a_under_pm"]:
        q4["stale_pm_vs_"+k]=sp(col(NL,"stale_pm"),col(NL,k))
    lowloss=[r for r in NL if (r["v_lost_pm"] or 0)<20]; hiloss=[r for r in NL if (r["v_lost_pm"] or 0)>=400]
    q4["low_loss_lt20pm"]={"n":len(lowloss),"stale_pm_med":med(lowloss,"stale_pm"),"fps_med":med(lowloss,"fps"),"spike20_pm_med":med(lowloss,"spike20_pm")}
    q4["high_loss_ge400pm"]={"n":len(hiloss),"stale_pm_med":med(hiloss,"stale_pm"),"fps_med":med(hiloss,"fps"),"spike20_pm_med":med(hiloss,"spike20_pm")}
    ev=[e for r in NL for e in r["slow"] if len(e)>=7]
    ifl=[e[4] for e in ev]; cms=[e[3] for e in ev]; gap=[e[6] for e in ev]; feed=[e[2] for e in ev]
    q4["slow_event_pool"]={"n":len(ev),"in_flight_distribution":{str(k):ifl.count(k) for k in sorted(set(ifl))},"in_flight_median":st.median(ifl),
        "share_in_flight_ge_8":round(sum(1 for x in ifl if x>=8)/len(ifl),4),"feed_delay_median_ms":st.median(feed),"share_feed_delay_gt_5ms":round(sum(1 for x in feed if x>5)/len(feed),3),
        "output_gap_vs_codec_ms":sp(gap,cms),"codec_ms_vs_in_flight":sp(cms,ifl)}
    buckets={}
    for m,i in zip(cms,ifl):
        b="50-80" if m<80 else "80-150" if m<150 else "150-300" if m<300 else "300+"; buckets.setdefault(b,[]).append(i)
    q4["in_flight_by_codec_ms_bucket"]={b:{"n":len(v),"in_flight_median":st.median(v),"in_flight_mean":round(sum(v)/len(v),2)} for b,v in buckets.items()}
    q4["worst_stalls"]=[{k:r[k] for k in ("received","dur_s","max_gap","max_codec","max_rx","max_inflight","fps","v_lost_pm","largest_jump","resyncs","max_resync_to_idr","wait_idr_drops","a_under_pm","a_starve")} for r in sorted(NL,key=lambda r:-r["max_gap"])[:14]]
    out["Q4_stale_drops"]=q4
    l2c=[r for r in BASE if r["low_latency"]]
    if l2c:
        r=l2c[0]; out["low_latency_session"]={k:r[k] for k in ("received","dur_s","spike20_pm","stale_pm","fps","max_gap","max_codec","max_inflight","v_lost_pm")}
        out["low_latency_session"]["share_lt_20ms"]=round(1-r["spike20"]/r["queued"],3)
    json.dump(out,open(os.path.join(outdir,"a2_rescore_result.json"),"w"),indent=1,default=str)
    keys=["file","received","dur_s","kbps","low_latency","spike20_pm","spike50_pm","spike80_pm","spike250","spike500","fps","v_fps","stale_pm","max_gap","max_codec","max_rx","max_inflight","input_waits","max_feed","v_lost_pm","loss_corrected_pm","gap_events","max_gap_pk","fec_rec","fec_unrec","resyncs","largest_jump","jump_packets","max_resync_to_idr","wait_idr_drops","a_under","a_under_pm","a_lost_pm","a_starve","slow_ret","slow_cap","motion"]
    with open(os.path.join(outdir,"a2_session_table.csv"),"w",newline="") as fh:
        w=csv.writer(fh,lineterminator="\n"); w.writerow(keys+["epoch"])
        for r in rows: w.writerow([(round(r[k],2) if isinstance(r.get(k),float) else r.get(k)) for k in keys]+[epoch(r)])
    print(json.dumps({k:out[k] for k in ("selection","epochs","latency_bands_excl_low_latency")},indent=1))
if __name__=="__main__": main()
