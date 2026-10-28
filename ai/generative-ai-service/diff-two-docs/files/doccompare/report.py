"""Write the change record (JSON, full provenance) and a self-contained HTML
review page: side-by-side pages with overlays, then one row per change with
the OLD/NEW crops, exact strings and the verifier's verdict.
"""
from __future__ import annotations

import html
import json
from pathlib import Path


def write_json(out_dir: Path, record: dict) -> Path:
    p = out_dir / "changes.json"
    p.write_text(json.dumps(record, ensure_ascii=False, indent=1))
    return p


def _rel(out_dir: Path, p: str) -> str:
    try:
        return str(Path(p).resolve().relative_to(out_dir.resolve()))
    except ValueError:
        return p


def _box_div(b, W, H, cls):
    x0, y0, x1, y1 = b
    return (f'<div class="box {cls}" style="left:{100 * x0 / W:.2f}%;top:{100 * y0 / H:.2f}%;'
            f'width:{100 * (x1 - x0) / W:.2f}%;height:{100 * (y1 - y0) / H:.2f}%"></div>')


def write_html(out_dir: Path, record: dict) -> Path:
    esc = lambda s: html.escape(str(s if s is not None else ""), quote=False)  # noqa: E731
    css = """
    body{font-family:-apple-system,Helvetica,Arial,sans-serif;margin:16px;color:#222}
    h2{margin-top:32px} .pair{display:flex;gap:12px;align-items:flex-start}
    .pg{position:relative;flex:1;border:1px solid #ccc} .pg img{width:100%;display:block}
    .box{position:absolute;border:2px solid;box-sizing:border-box;pointer-events:none}
    .acc{border-color:#d33;background:rgba(220,50,50,.12)} .rej{border-color:#39c;background:rgba(50,150,220,.08)}
    .unv{border-color:#f90;background:rgba(255,150,0,.12)}
    table{border-collapse:collapse;width:100%;margin-top:12px;font-size:13px}
    td,th{border:1px solid #ddd;padding:6px;vertical-align:top} th{background:#f4f4f4;text-align:left}
    td img{max-width:360px;max-height:220px;border:1px solid #ccc}
    .mono{font-family:Menlo,monospace;white-space:pre-wrap} .muted{color:#777}
    .tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:12px;background:#eee}
    .acc-tag{background:#fdd} .rej-tag{background:#def}
    """
    parts = [f"<!doctype html><meta charset=utf-8><title>doc-compare report</title><style>{css}</style>"]
    parts.append(f"<h1>Document comparison</h1><p><b>OLD</b> {esc(record['old']['pdf'])} ({record['old']['pages']} pages)"
                 f"<br><b>NEW</b> {esc(record['new']['pdf'])} ({record['new']['pages']} pages)"
                 f"<br>model {esc(record.get('model'))} · dpi {record['dpi']} · "
                 f"{len(record['changes'])} verified changes, {len(record['rejected'])} candidates rejected, "
                 f"{len(record['unverified'])} unverified</p>")
    chg_by_pair: dict[tuple, list] = {}
    for coll, cls in (("changes", "acc"), ("rejected", "rej"), ("unverified", "unv")):
        for c in record[coll]:
            chg_by_pair.setdefault((c["old_page"], c["new_page"]), []).append((c, cls))
    for pp in record["page_pairs"]:
        op, np_ = pp["old_page"], pp["new_page"]
        parts.append(f"<h2>Old p{op if op else '—'} ↔ New p{np_ if np_ else '—'} "
                     f"<span class=muted>(similarity {pp['similarity']:.2f}, registration {esc(pp.get('registration'))}, "
                     f"{pp.get('n_text_candidates', 0)} text / {pp.get('n_blobs', 0)} pixel candidates)</span></h2>")
        if op is None or np_ is None:
            parts.append("<p><b>Page inserted or removed.</b></p>")
            continue
        items = chg_by_pair.get((op, np_), [])
        ow, oh, nw, nh = pp["old_size"][0], pp["old_size"][1], pp["new_size"][0], pp["new_size"][1]
        o_boxes = "".join(_box_div(c["old_bbox"], ow, oh, cls) for c, cls in items if c.get("old_bbox"))
        n_boxes = "".join(_box_div(c["new_bbox"], nw, nh, cls) for c, cls in items if c.get("new_bbox"))
        parts.append(f'<div class=pair><div class=pg><img src="{esc(_rel(out_dir, pp["old_png"]))}">{o_boxes}</div>'
                     f'<div class=pg><img src="{esc(_rel(out_dir, pp["new_png"]))}">{n_boxes}</div></div>')
        rows = []
        for c, cls in items:
            v = c.get("verdict") or {}
            tag = {"acc": "CHANGE", "rej": "rejected", "unv": "unverified"}[cls]
            where = " / ".join(x for x in (v.get("row_label"), v.get("column_header")) if x)
            rows.append(
                f"<tr><td>{c['id']}<br><span class='tag {cls}-tag'>{tag}</span><br><span class=muted>{esc(c['kind'])}/{esc(c['op'])}"
                f"<br>{', '.join(c['sources'])}</span></td>"
                f"<td><img src='{esc(_rel(out_dir, c['crops']['old']))}'></td><td><img src='{esc(_rel(out_dir, c['crops']['new']))}'></td>"
                f"<td><b>{esc(v.get('change_type', ''))}</b> <span class=muted>{esc(v.get('confidence', ''))}"
                f"{(' · p=' + str(v['token_prob'])) if v.get('token_prob') is not None else ''}</span>"
                f"<br>{esc(v.get('description', ''))}<br><span class=muted>{esc(where)}</span>"
                f"<div class=mono>old: {esc(v.get('old_text') or c['hint']['old_text'])}\nnew: {esc(v.get('new_text') or c['hint']['new_text'])}</div>"
                f"{('<div class=muted>error: ' + esc(v.get('error')) + '</div>') if v.get('error') else ''}</td></tr>")
        if rows:
            parts.append("<table><tr><th>#</th><th>OLD crop</th><th>NEW crop</th><th>verdict</th></tr>" + "".join(rows) + "</table>")
        else:
            parts.append("<p class=muted>No candidates on this page pair.</p>")
    p = out_dir / "report.html"
    p.write_text("".join(parts))
    return p
