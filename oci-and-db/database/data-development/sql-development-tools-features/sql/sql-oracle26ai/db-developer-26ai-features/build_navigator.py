#!/usr/bin/env python3
"""Regenerate the offline 26ai Developer Knowledge Navigator from Markdown files.
Usage: python3 build_navigator.py (run from anywhere; script uses its own folder).
Requires Python 3.9+ standard library only. Never changes source Markdown.
"""
from pathlib import Path
import json, re, html
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / '26ai_developer_navigator.html'
STORY = re.compile(r'^\d{2}_.+')

def inline(s):
    s = html.escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', lambda m: '<a href="'+html.escape(m.group(2),quote=True)+'" target="_blank" rel="noopener">'+m.group(1)+'</a>', s)
    s = re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s = re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*',r'<em>\1</em>',s)
    return s

def render(md):
    lines=md.splitlines(); out=[]; code=[]; para=[]; in_code=False; list_mode=False; quote=[]; table=[]
    def flushpara():
        if para: out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
    def flushlist():
        nonlocal list_mode
        if list_mode:out.append('</ul>');list_mode=False
    def flushquote():
        if quote:out.append('<blockquote>'+inline(' '.join(quote))+'</blockquote>');quote.clear()
    def flushtable():
        if not table:return
        out.append('<div class="table-scroll"><table>')
        for i,row in enumerate(table):
            if i==1 and all(re.fullmatch(r':?-{3,}:?',c.strip()) for c in row):continue
            tag='th' if i==0 else 'td';out.append('<tr>'+''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in row)+'</tr>')
        out.append('</table></div>');table.clear()
    for line in lines+['']:
        if line.strip().startswith('```'):
            flushpara();flushlist();flushquote();flushtable()
            if in_code:
                out.append('<div class="code-wrap"><button class="copy-btn" type="button" onclick="copyCode(this)">Copy SQL / code</button><pre><code>'+html.escape('\n'.join(code))+'</code></pre></div>');code=[];in_code=False
            else:in_code=True
            continue
        if in_code:code.append(line);continue
        if line.startswith('|') and line.rstrip().endswith('|'):
            flushpara();flushlist();flushquote();table.append(line.strip().strip('|').split('|'));continue
        flushtable()
        if line.startswith('>'):
            flushpara();flushlist();quote.append(line[1:].strip());continue
        flushquote()
        if not line.strip():flushpara();flushlist();continue
        if line.startswith('#'):
            flushpara();flushlist();m=re.match(r'^(#{1,6})\s+(.*)',line)
            if m: level=min(len(m.group(1))+1,6);out.append(f'<h{level}>{inline(m.group(2))}</h{level}>');continue
        if re.match(r'^\s*[-*]\s+',line):
            flushpara()
            if not list_mode:out.append('<ul>');list_mode=True
            out.append('<li>'+inline(re.sub(r'^\s*[-*]\s+','',line))+'</li>');continue
        flushlist();para.append(line.strip())
    return '\n'.join(out)

def section(md, label):
    matches=list(re.finditer(r'^##\s+(.+)$',md,re.M))
    for i,m in enumerate(matches):
        if label in m.group(1).lower():
            return md[m.end():matches[i+1].start() if i+1<len(matches) else len(md)].strip()
    return ''

def stripmd(s):
    s=re.sub(r'```[\s\S]*?```',' ',s);s=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
    return re.sub(r'[`*_#>|]','',s).strip()

items=[]
for p in sorted(ROOT.iterdir()):
    if not p.is_dir() or not STORY.match(p.name):continue
    for f in sorted((p/'additional_information').glob('*.md')) if (p/'additional_information').exists() else []:
        md=f.read_text(encoding='utf-8-sig'); title=re.search(r'^#\s+(.+)$',md,re.M)
        question=re.search(r'^>\s*\*\*Developer question:\*\*\s*(.*)',md,re.M|re.I)
        takeaway=stripmd(section(md,'key takeaway'))
        adoption=stripmd(section(md,'when should developers adopt'))
        items.append(dict(id=str(f.relative_to(ROOT)).replace('/','--'),path=f.relative_to(ROOT).as_posix(),story=p.name,title=title.group(1) if title else f.stem.replace('_',' ').title(),question=stripmd(question.group(1)) if question else '',takeaway=takeaway,adoption=adoption,body=render(md),text=stripmd(md)))

DATA=json.dumps(items,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('</','<\\/')
TEMPLATE=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Oracle AI Database 26ai | Developer Knowledge Navigator</title>
<style>
:root{--navy:#03234b;--green:#009639;--page:#f0f2f5;--ink:#12213b;--muted:#536176;--line:#e2e6ea;--code:#1e2330}*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:14px/1.6 Inter,Arial,sans-serif}header{background:var(--navy);border-bottom:3px solid var(--green);color:white;padding:14px max(24px,calc((100vw - 1480px)/2));display:flex;align-items:center;justify-content:space-between;gap:20px}header b{font-size:17px}header span{font-size:12px;color:#b7c5d5}.shell{max-width:1480px;margin:auto;padding:24px}.hero{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:16px}.hero h1{font-size:24px;margin:0}.hero p{margin:3px 0;color:var(--muted)}.search{width:100%;border:1px solid #cbd0d8;border-radius:8px;padding:14px 16px;font-size:16px;background:white;outline:none}.search:focus{border-color:var(--green);box-shadow:0 0 0 3px #00963920}.layout{display:grid;grid-template-columns:235px 315px minmax(0,1fr);gap:16px;margin-top:18px;align-items:start}.panel{background:white;border:1px solid var(--line);border-radius:8px;box-shadow:0 1px 4px #0001;overflow:hidden}.panel-head{padding:12px 15px;background:#f8fafc;border-bottom:1px solid var(--line);font-weight:800;font-size:12px;text-transform:uppercase;letter-spacing:.04em}.sidebar,.results{padding:8px;max-height:calc(100vh - 215px);overflow:auto;position:sticky;top:12px}.navbtn,.result{width:100%;text-align:left;background:white;border:1px solid transparent;border-radius:6px;padding:10px;cursor:pointer;color:var(--ink);font:inherit}.navbtn:hover,.result:hover{background:#f0fff5;border-color:#cdebd8}.navbtn.active,.result.active{background:#e7f8ee;border-color:var(--green)}.navbtn{font-size:12px;font-weight:700}.count{float:right;color:#8493a6}.result{margin-bottom:5px;border-color:var(--line)}.result strong{display:block;font-size:13px;line-height:1.35}.result small{display:block;color:var(--muted);margin-top:5px;line-height:1.4}.badge{display:inline-block;color:#067537;background:#e7f8ee;border-radius:4px;padding:1px 7px;font-size:10px;font-weight:800}.detail{min-height:60vh}.detail-inner{padding:23px 27px}.detail h2{font-size:25px;line-height:1.25;margin:10px 0}.detail .question{border-left:4px solid var(--green);background:#f0fff5;padding:12px 15px;margin:16px 0}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.btn{border:1px solid #cbd0d8;background:white;color:var(--ink);border-radius:6px;padding:8px 12px;font-weight:700;cursor:pointer}.btn.active,.btn:hover{background:var(--navy);color:white}.summary{display:grid;gap:12px;margin-top:18px}.summary article{background:#f8fafc;border:1px solid var(--line);padding:15px;border-radius:6px}.summary h3{margin:0 0 5px;font-size:12px;text-transform:uppercase;color:var(--green)}.summary p{margin:0;white-space:pre-wrap}.md h2{font-size:23px}.md h3{font-size:17px;margin-top:26px;border-bottom:1px solid var(--line);padding-bottom:6px}.md p{line-height:1.75}.md blockquote{border-left:4px solid var(--green);background:#f0fff5;margin:12px 0;padding:10px 15px}.md ul{padding-left:22px}.md li{margin:5px 0}.md code:not(pre code){background:#eef2f6;border-radius:3px;padding:2px 5px}.code-wrap{position:relative;margin:15px 0}.code-wrap pre{background:var(--code);color:#b8e2f3;padding:19px 16px;border-radius:7px;overflow:auto;font:12px/1.65 'JetBrains Mono',Consolas,monospace;white-space:pre}.copy-btn{position:absolute;right:8px;top:8px;background:#334155;color:white;border:1px solid #64748b;border-radius:4px;font-size:11px;padding:5px 8px;cursor:pointer}.table-scroll{overflow:auto}.md table{border-collapse:collapse;width:100%;font-size:12px}.md th,.md td{border-bottom:1px solid var(--line);padding:9px;text-align:left}.md th{background:#f8fafc}.md a{color:#087a3a}.empty{padding:18px;color:var(--muted)}footer{padding:22px;text-align:center;color:var(--muted);font-size:11px}@media(max-width:1080px){.layout{grid-template-columns:190px 1fr}.detail{grid-column:1/-1}.sidebar,.results{max-height:340px;position:static}}@media(max-width:650px){.layout{display:block}.layout>.panel{margin-bottom:12px}.detail-inner{padding:17px}header{display:block}.hero{display:block}}
</style></head><body>
<header><b>Oracle AI Database 26ai</b><span>Developer Knowledge Navigator · Offline speaker reference</span></header>
<div class="shell"><div class="hero"><div><h1>Developer feature comparisons</h1><p>Find the right answer during a LiveLab. Select a storyline or search across the full catalog.</p></div><span class="badge" id="total"></span></div>
<input id="search" class="search" type="search" placeholder="Search questions, features, SQL examples… (press /)" aria-label="Search all comparisons" autocomplete="off">
<div class="layout"><aside class="panel"><div class="panel-head">Storylines</div><div id="stories" class="sidebar"></div></aside><section class="panel"><div class="panel-head">Matching comparisons <span id="matchCount" class="count"></span></div><div id="results" class="results"></div></section><main class="panel detail" id="detail"><div class="empty">Select a comparison to view its overview and details.</div></main></div></div>
<footer>Generated from local Markdown · Search works without a network connection · Rebuild after editing source files</footer>
<script>
const DOCS=__DATA__;
const SYNONYMS={udt:'user defined types object types',vpd:'virtual private database',mle:'multilingual engine javascript',etag:'optimistic concurrency control json relational duality',occ:'optimistic concurrency control',locking:'row locking lock free reservations',rest:'api json duality',js:'javascript multilingual engine',sqlmacro:'sql macros',semantic:'vector search',plsql:'pl/sql procedural functions'};
let activeStory='',selected='',mode='overview';const $=id=>document.getElementById(id);
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function pretty(s){const name=s.replace(/^\d{2}_/,'');if(name==='transactions_concurrency')return 'Transactions & Concurrency';return name.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());}
function score(d,q){if(!q)return 1;const terms=q.toLowerCase().trim().split(/\s+/).filter(Boolean);const title=d.title.toLowerCase(),question=d.question.toLowerCase(),takeaway=d.takeaway.toLowerCase(),body=d.text.toLowerCase(),story=d.story.toLowerCase();let total=0;for(const t of terms){const variants=[t,...(SYNONYMS[t]||'').split(' ').filter(Boolean)];let best=0;for(const v of variants){if(title.includes(v))best=Math.max(best,10);else if(question.includes(v))best=Math.max(best,9);else if(takeaway.includes(v))best=Math.max(best,6);else if(story.includes(v))best=Math.max(best,4);else if(body.includes(v))best=Math.max(best,1);}if(!best)return 0;total+=best;}return total;}
function list(){const q=$('search').value.trim();const docs=DOCS.map(d=>({...d,_score:score(d,q)})).filter(d=>d._score>0&&(!activeStory||d.story===activeStory)).sort((a,b)=>b._score-a._score||a.title.localeCompare(b.title));$('matchCount').textContent=docs.length;$('results').innerHTML=docs.length?docs.map(d=>`<button class="result ${selected===d.id?'active':''}" data-id="${esc(d.id)}"><strong>${esc(d.title)}</strong><small>${esc(d.question||d.takeaway.slice(0,140))}</small></button>`).join(''):'<div class="empty">No matching comparisons. Try a feature name or synonym.</div>';document.querySelectorAll('.result').forEach(b=>b.onclick=()=>show(b.dataset.id));if(docs.length&&(!selected||!docs.some(d=>d.id===selected)))show(docs[0].id,false);if(!docs.length)$('detail').innerHTML='<div class="empty">No comparison selected.</div>';}
function stories(){const names=[...new Set(DOCS.map(d=>d.story))].sort();$('stories').innerHTML=`<button class="navbtn ${!activeStory?'active':''}" data-story="">All storylines <span class="count">${DOCS.length}</span></button>`+names.map(n=>`<button class="navbtn ${activeStory===n?'active':''}" data-story="${esc(n)}">${esc(pretty(n))}<span class="count">${DOCS.filter(d=>d.story===n).length}</span></button>`).join('');document.querySelectorAll('.navbtn').forEach(b=>b.onclick=()=>{activeStory=b.dataset.story;selected='';stories();list()});}
function show(id,rerender=true){const d=DOCS.find(x=>x.id===id);if(!d)return;if(selected!==id)mode='overview';selected=id;const speaker=`<div class="summary"><article><h3>Developer question</h3><p>${esc(d.question||'What changes, and why adopt it?')}</p></article><article><h3>Key takeaway</h3><p>${esc(d.takeaway||'See the technical comparison.')}</p></article><article><h3>When to adopt</h3><p>${esc(d.adoption||'See section 5 in Details.')}</p></article></div>`;$('detail').innerHTML=`<div class="detail-inner"><span class="badge">${esc(pretty(d.story))}</span><h2>${esc(d.title)}</h2><div class="toolbar"><button class="btn ${mode==='overview'?'active':''}" id="speakerBtn">Overview</button><button class="btn ${mode==='details'?'active':''}" id="technicalBtn">Details</button></div><div id="content">${mode==='overview'?speaker:'<div class="md">'+d.body+'</div>'}</div></div>`;$('speakerBtn').onclick=()=>{mode='overview';show(id)};$('technicalBtn').onclick=()=>{mode='details';show(id)};if(rerender)document.querySelectorAll('.result').forEach(b=>b.classList.toggle('active',b.dataset.id===id));}
async function copyCode(btn){const text=btn.nextElementSibling.innerText;try{await navigator.clipboard.writeText(text)}catch(e){const t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove()}btn.textContent='Copied';setTimeout(()=>btn.textContent='Copy SQL / code',1400)}
$('search').addEventListener('input',list);document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==$('search')){e.preventDefault();$('search').focus()}if(e.key==='Escape')$('search').blur()});$('total').textContent=DOCS.length+' comparisons';stories();list();
</script></body></html>'''
OUTPUT.write_text(TEMPLATE.replace('__DATA__',DATA),encoding='utf-8')
print(f'Generated {OUTPUT.name}: {len(items)} comparisons, {OUTPUT.stat().st_size:,} bytes')
