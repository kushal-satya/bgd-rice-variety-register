/* Bangladesh Rice Variety Register: page logic.
   Text comes from content/text.md (editable; {{placeholders}} are computed below from the data).
   Data come from data/site_data.json. The standalone build inlines both as window.__SITE_TEXT__ / window.__SITE_DATA__. */
(async function () {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = n => Number(n).toLocaleString('en-US');
const link = (u, label) => u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(label)}</a>` : '';
const clip = (t, n) => { t = String(t || ''); if (t.length <= n) return t; const c = t.slice(0, n); return c.slice(0, Math.max(c.lastIndexOf(' '), n * 0.6 | 0)).replace(/[\s,;(\/]+$/, '') + '…'; };
const NS = 'http://www.w3.org/2000/svg';
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };

// ---------- load ----------
const D = window.__SITE_DATA__ || await (await fetch('data/site_data.json')).json();
const TEXT = window.__SITE_TEXT__ || await (await fetch('content/text.md')).text();
const R = D.rice;

// ---------- placeholders (documented in README.md) ----------
const sector = r => /^(Private company|Private or NGO inbred)$/.test(r.developer_group) ? 'private' : 'public';
const yrs = R.map(r => +r.approval_year).filter(Boolean);
const built = new Date(D.built + 'T00:00:00Z');
const STATS = {
  n_rice: R.length,
  n_inbred: R.filter(r => r.rice_type === 'inbred').length,
  n_hybrid: R.filter(r => r.rice_type === 'hybrid').length,
  n_public: R.filter(r => sector(r) === 'public').length,
  n_private: R.filter(r => sector(r) === 'private').length,
  n_brri: R.filter(r => r.developer_group === 'BRRI').length,
  n_bina: R.filter(r => r.developer_group === 'BINA').length,
  year_min: Math.min(...yrs), year_max: Math.max(...yrs),
  n_dated: R.filter(r => (r.approval_date || '').length === 10).length,
  n_gazette: R.filter(r => r.gazette_date).length,
  n_cgiar_linked: R.filter(r => ['1', '2', '3'].includes(r.cgiar_role)).length,
  n_cgiar_inbred_linked: R.filter(r => r.rice_type === 'inbred' && ['1', '2', '3'].includes(r.cgiar_role)).length,
  n_cgiar_unknown: R.filter(r => r.cgiar_role === '5').length,
  n_with_features: R.filter(r => r.feature_tags).length,
  n_key_papers: R.filter(r => r.key_papers).length,
  n_fish: D.fish.length, n_fish_events: D.fish_events.length,
  n_fish_acts: (D.fish_groups || []).reduce((a, g) => a + g.n, 0),
  n_evidence: (D.qa || {}).evidence_rows || 0, n_source_files: (D.qa || {}).n_sources || 0,
  n_conflicts: (D.qa || {}).n_conflicts || 0, n_ocr_pages: (D.qa || {}).ocr_pages || 0,
  ocr_mean_conf: (D.qa || {}).ocr_mean_conf || '', n_qa_checks: D.n_qa_checks || 30,
  n_board_rows: (D.attendance || []).length,
  n_board_people: new Set((D.attendance || []).map(x => (x.name_en || x.name_as_written).toLowerCase().replace(/^(dr|md|mr|mrs|ms|prof)\.?\s+/g, '').replace(/[\s.,()\-]+/g, ''))).size,
  board_first: (D.attendance || []).reduce((a, x) => Math.min(a, +x.meeting_no), 999),
  board_last: (D.attendance || []).reduce((a, x) => Math.max(a, +x.meeting_no), 0),
  n_pedigree: R.filter(r => r.pedigree).length,
  n_cgiar_known: R.filter(r => r.cgiar_role && r.cgiar_role !== '5').length,
  n_ocr_unconfirmed: ((D.qa || {}).by_check || []).filter(x => x[0] === 'ocr' && x[1] === 'unvalidated').reduce((a, x) => a + x[2], 0),
  n_date_conflicts: R.filter(r => /approval_date/.test(r.conflict_fields || '')).length,
  n_inbred_untagged: R.filter(r => r.rice_type === 'inbred' && !r.feature_tags).length,
  n_fish_ornamental: ((D.fish_groups || []).find(g => g.approval_type === 'import_approval_ornamental') || {n: 0}).n,
  built: D.built, built_long: built.toLocaleDateString('en-GB', {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC'})
};
const fill = s => s.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => k in STATS ? (k.startsWith('n_') && typeof STATS[k] === 'number' ? fmt(STATS[k]) : String(STATS[k])) : m);

// ---------- minimal markdown ----------
function inline(s) {
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/\*([^*]+)\*/g, '<i>$1</i>').replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}
function md(src) {
  const out = []; let list = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const para of src.trim().split(/\n\s*\n/)) {
    const lines = para.split('\n');
    if (lines.every(l => /^\s*[-*] /.test(l))) { close(); out.push('<ul>' + lines.map(l => `<li>${inline(l.replace(/^\s*[-*] /, ''))}</li>`).join('') + '</ul>'); continue; }
    if (lines.every(l => /^\s*\d+\. /.test(l))) { close(); out.push('<ol>' + lines.map(l => `<li>${inline(l.replace(/^\s*\d+\. /, ''))}</li>`).join('') + '</ol>'); continue; }
    const h = para.match(/^(#{2,4}) (.*)$/);
    if (h) { close(); out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); continue; }
    close(); out.push(`<p>${inline(lines.join(' '))}</p>`);
  }
  close(); return out.join('');
}
const BLOCKS = {};
TEXT.split(/<!--\s*@([\w-]+)\s*-->/).forEach((part, i, arr) => { if (i % 2 === 1) BLOCKS[part] = (arr[i + 1] || '').trim(); });
document.querySelectorAll('[data-text]').forEach(node => {
  const src = fill(BLOCKS[node.dataset.text] || '');
  node.innerHTML = node.hasAttribute('data-inline') ? inline(src) : md(src);
});
document.title = fill(BLOCKS.title || document.title);

// ---------- shared ----------
const SER = [['pub_inb', 'Public inbred', 'var(--s-pub)', 'background:var(--s-pub)', ''], ['pub_hyb', 'Public hybrid', 'url(#hp)', '', 'hp'],
             ['pvt_inb', 'Private inbred', 'var(--s-pvt)', 'background:var(--s-pvt)', ''], ['pvt_hyb', 'Private hybrid', 'url(#hv)', '', 'hv']];
const series = r => (sector(r) === 'public' ? 'pub_' : 'pvt_') + (r.rice_type === 'hybrid' ? 'hyb' : 'inb');
const CODES = {'1': 'CGIAR line released directly', '2': 'CGIAR parent or earlier ancestor', '3': 'Collaboration or funding only', '4': 'No CGIAR element found in traceable pedigree', '5': 'Unknown'};
const SRC = [[/nsb_minutes/, 'NSB minutes'], [/approved_crop_varieties|registered_hybrid_rice/, 'SCA annual list'], [/approved_varieties_notified_crops/, 'SCA compendium 2016'],
  [/hybrid_rice_(varieties_)?list|item4_crop/, 'MoA hybrid list'], [/gazette|bgpress|release_gazette|release_notification/, 'Bangladesh Gazette'], [/adc|adhunik/, 'BRRI handbook'],
  [/riceprofile/, 'BRRI Rice Profile'], [/brri\//, 'BRRI record'], [/bina/, 'BINA record'], [/spia/, 'SPIA 2025'], [/trivsa/, 'TRIVSA'], [/harvestplus/, 'HarvestPlus']];
const srcLabel = f => { for (const [re, l] of SRC) if (re.test((f || '').toLowerCase())) return l; return 'Source document'; };
const offline = st => st === 'dead' || st === 'unreachable';
const tagsOf = r => (r.feature_tags || '').split(' | ').filter(Boolean);
const tip = $('#tip');
const showTip = (ev, html) => { tip.innerHTML = html; tip.hidden = false; moveTip(ev); };
function moveTip(ev) { const w = tip.offsetWidth, h = tip.offsetHeight; let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + w > innerWidth - 8) x = ev.clientX - w - 14; if (y + h > innerHeight - 8) y = ev.clientY - h - 14; tip.style.left = x + 'px'; tip.style.top = y + 'px'; }
const hideTip = () => { tip.hidden = true; };

// ---------- figures (drawn at the container's width; redrawn on resize) ----------
const widthOf = svg => Math.max(320, Math.round(svg.parentNode.getBoundingClientRect().width || 640));
const narrow = W => W < 560;
function fig1() {
  const svg = $('#f1'); svg.innerHTML = '';
  const W = widthOf(svg), H = narrow(W) ? 240 : 300, m = {l: 30, r: 8, t: 14, b: 26};
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const years = []; for (let y = STATS.year_min; y <= STATS.year_max; y++) years.push(y);
  const cnt = {}; years.forEach(y => cnt[y] = {pub_inb: 0, pub_hyb: 0, pvt_inb: 0, pvt_hyb: 0});
  R.forEach(r => { const y = +r.approval_year; if (cnt[y]) cnt[y][series(r)]++; });
  const sum = c => c.pub_inb + c.pub_hyb + c.pvt_inb + c.pvt_hyb;
  const defs = el('defs', {}, svg);
  [['hp', 'var(--s-pub)'], ['hv', 'var(--s-pvt)']].forEach(([id, col]) => { const pt = el('pattern', {id, width: 4, height: 4, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)'}, defs);
    el('rect', {width: 4, height: 4, fill: 'var(--bg)'}, pt); el('rect', {width: 2, height: 4, fill: col}, pt); });
  const top = Math.ceil(Math.max(...years.map(y => sum(cnt[y]))) / 10) * 10, iw = W - m.l - m.r, ih = H - m.t - m.b, bw = iw / years.length;
  const ys = v => m.t + ih - v / top * ih, step = narrow(W) ? 20 : 10;
  for (let v = 0; v <= top; v += 10) { el('line', {x1: m.l, x2: W - m.r, y1: ys(v), y2: ys(v), class: v ? 'gl' : 'ax'}, svg);
    el('text', {x: m.l - 6, y: ys(v) + 3.5, 'text-anchor': 'end'}, svg).textContent = v; }
  years.forEach((y, i) => { if (y % step === 0) el('text', {x: m.l + i * bw + bw / 2, y: H - 8, 'text-anchor': 'middle'}, svg).textContent = y; });
  years.forEach((y, i) => {
    let acc = 0; const c = cnt[y], tot = sum(c), x = m.l + i * bw + (bw > 4 ? 1 : 0), w = Math.max(1, bw - (bw > 4 ? 2 : 0.5));
    const partial = y === STATS.year_max, g = el('g', partial ? {opacity: 0.45} : {}, svg);
    const segs = SER.filter(s => c[s[0]] > 0);
    segs.forEach((s, j) => { const v = c[s[0]], yTop = ys(acc + v), hgt = ys(acc) - ys(acc + v), gap = j < segs.length - 1 ? 1 : 0;
      const rr = el('rect', {x, y: yTop + gap, width: w, height: Math.max(0, hgt - gap), fill: s[2]}, g);
      if (s[4]) { rr.setAttribute('stroke', s[4] === 'hp' ? 'var(--s-pub)' : 'var(--s-pvt)'); rr.setAttribute('stroke-width', '0.8'); }
      acc += v; });
    if (partial && tot) el('text', {x: x + w / 2, y: ys(tot) - 5, 'text-anchor': 'end', class: 'ann'}, svg).textContent = '1 meeting';
    const hit = el('rect', {x: m.l + i * bw, y: m.t, width: bw, height: ih, fill: 'transparent'}, svg);
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${y}</b> · ${tot} approved${partial ? ' (one meeting)' : ''}` + SER.map(s =>
      `<div class="r"><span class="k"><i class="sw ${s[4]}" style="${s[3]}"></i>${s[1]}</span><span>${c[s[0]]}</span></div>`).join('')));
    hit.addEventListener('mouseleave', hideTip);
  });
  const first = R.filter(r => r.rice_type === 'hybrid').sort((a, b) => a.approval_date.localeCompare(b.approval_date))[0];
  if (first) { const i = +first.approval_year - years[0], x = m.l + i * bw + bw / 2;
    el('line', {x1: x, x2: x, y1: ys(sum(cnt[+first.approval_year])) - 4, y2: ys(top * 0.62), class: 'annl'}, svg);
    el('text', {x: x - 4, y: ys(top * 0.62) - 6, 'text-anchor': 'end', class: 'ann'}, svg).textContent = narrow(W) ? 'First hybrids, Sep 1998' : 'First hybrids registered, 40th NSB meeting, Sep 1998'; }
}
const PERIOD = y => { const p = Math.floor(y / 5) * 5; return p; };
function fig2() {
  const svg = $('#f2'); svg.innerHTML = '';
  const W = widthOf(svg), m = {l: 70, r: 34, t: 6, b: 22}, rowH = 22;
  $('#lg2').innerHTML = ['1', '2', '3', '4', '5'].map(k => `<span><i class="sw ${k === '5' ? 'hatch' : ''}" style="${k === '5' ? '' : 'background:var(--c' + k + ')'}"></i>${k} ${CODES[k]}</span>`).join('');
  const inb = R.filter(r => r.rice_type === 'inbred' && +r.approval_year);
  const pers = []; for (let p = PERIOD(STATS.year_min); p <= STATS.year_max; p += 5) pers.push(p);
  const H = m.t + pers.length * rowH + m.b; svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const defs = el('defs', {}, svg), pat = el('pattern', {id: 'h5', width: 5, height: 5, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)'}, defs);
  el('rect', {width: 5, height: 5, fill: 'var(--c5)'}, pat); el('rect', {width: 2, height: 5, fill: 'var(--hatch)'}, pat);
  const rows = pers.map(p => inb.filter(r => PERIOD(+r.approval_year) === p));
  const max = Math.ceil(Math.max(...rows.map(x => x.length)) / 10) * 10, iw = W - m.l - m.r, xs = v => m.l + v / max * iw;
  for (let v = 0; v <= max; v += 10) { el('line', {x1: xs(v), x2: xs(v), y1: m.t, y2: H - m.b, class: v ? 'gl' : 'ax'}, svg);
    el('text', {x: xs(v), y: H - 6, 'text-anchor': 'middle'}, svg).textContent = v; }
  pers.forEach((p, i) => {
    const rs = rows[i], c = {}; ['1', '2', '3', '4', '5'].forEach(k => c[k] = rs.filter(r => (r.cgiar_role || '5') === k).length);
    const y = m.t + i * rowH + 4, h = rowH - 8, last = p + 4 >= STATS.year_max;
    const lab = `${Math.max(p, STATS.year_min)}–${String(Math.min(p + 4, STATS.year_max)).slice(2)}`;
    el('text', {x: m.l - 8, y: y + h / 2 + 4, 'text-anchor': 'end', class: 'lab'}, svg).textContent = lab + (last ? '*' : '');
    let acc = 0; const keys = ['1', '2', '3', '4', '5'].filter(k => c[k] > 0);
    keys.forEach(k => { const w = xs(c[k]) - m.l;
      el('rect', {x: xs(acc), y, width: Math.max(0, w - 1), height: h, fill: k === '5' ? 'url(#h5)' : `var(--c${k})`}, svg); acc += c[k]; });
    el('text', {x: xs(rs.length) + 5, y: y + h / 2 + 4, class: 'lab'}, svg).textContent = rs.length;
    const hit = el('rect', {x: 0, y: y - 4, width: W, height: rowH, fill: 'transparent'}, svg);
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${lab}</b> · ${rs.length} inbred varieties${last ? ' (period incomplete)' : ''}` + keys.map(k =>
      `<div class="r"><span class="k">${k} ${CODES[k]}</span><span>${c[k]}</span></div>`).join('')));
    hit.addEventListener('mouseleave', hideTip);
  });
}
function fig3() {
  const svg = $('#f3'); svg.innerHTML = '';
  const inb = R.filter(r => r.rice_type === 'inbred' && +r.approval_year);
  const decs = []; for (let d = Math.floor(STATS.year_min / 10) * 10; d <= STATS.year_max; d += 10) decs.push(d);
  const tot = {}; inb.forEach(r => tagsOf(r).forEach(t => tot[t] = (tot[t] || 0) + 1));
  const tags = Object.keys(tot).sort((a, b) => tot[b] - tot[a]);
  const cell = {}; inb.forEach(r => { const d = Math.floor(+r.approval_year / 10) * 10; tagsOf(r).forEach(t => { const k = t + '|' + d; cell[k] = (cell[k] || 0) + 1; }); });
  const nDec = {}; inb.forEach(r => { const d = Math.floor(+r.approval_year / 10) * 10; nDec[d] = (nDec[d] || 0) + 1; });
  const W = widthOf(svg), lw = narrow(W) ? 128 : 190, m = {l: lw, r: 46, t: 34, b: 6}, rowH = narrow(W) ? 20 : 22;
  const cw = (W - m.l - m.r) / decs.length, H = m.t + tags.length * rowH + m.b, max = Math.max(1, ...Object.values(cell));
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  decs.forEach((d, j) => { const x = m.l + j * cw + cw / 2;
    el('text', {x, y: 13, 'text-anchor': 'middle', class: 'lab'}, svg).textContent = narrow(W) ? `’${String(d).slice(2)}s` : `${d}s`;
    el('text', {x, y: 27, 'text-anchor': 'middle'}, svg).textContent = `n=${nDec[d] || 0}`; });
  el('text', {x: W - m.r + 6, y: 27}, svg).textContent = 'total';
  tags.forEach((t, i) => {
    const y = m.t + i * rowH;
    el('line', {x1: 0, x2: W, y1: y + rowH, y2: y + rowH, class: 'gl'}, svg);
    el('text', {x: m.l - 8, y: y + rowH / 2 + 4, 'text-anchor': 'end', class: 'lab'}, svg).textContent = t;
    decs.forEach((d, j) => { const n = cell[t + '|' + d] || 0, x = m.l + j * cw;
      if (n) { el('rect', {x: x + 2, y: y + 2, width: cw - 4, height: rowH - 4, fill: 'var(--s-pub)', 'fill-opacity': 0.12 + 0.88 * n / max}, svg);
        el('text', {x: x + cw / 2, y: y + rowH / 2 + 4, 'text-anchor': 'middle', class: n / max > 0.55 ? 'lab inv' : 'lab'}, svg).textContent = n; } });
    el('text', {x: W - m.r + 6, y: y + rowH / 2 + 4, class: 'lab'}, svg).textContent = tot[t];
    const hit = el('rect', {x: 0, y, width: W, height: rowH, fill: 'transparent'}, svg);
    hit.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(t)}</b> · ${tot[t]} of ${inb.length} inbred varieties` + decs.map(d =>
      `<div class="r"><span class="k">${d}s</span><span>${cell[t + '|' + d] || 0} of ${nDec[d] || 0}</span></div>`).join('')));
    hit.addEventListener('mouseleave', hideTip);
  });
}
const drawFigures = () => { if ($('#figures').classList.contains('active')) { fig1(); fig2(); fig3(); } };
let rz; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawFigures, 150); });

// ---------- register ----------
const fg = $('#fg'), fc = $('#fc'), ff = $('#ff');
fg.innerHTML = '<option value="">All</option>' + [...new Set(R.map(r => r.developer_group))].sort().map(g => `<option>${esc(g)}</option>`).join('');
fc.innerHTML += ['1', '2', '3', '4', '5'].map(k => `<option value="${k}">${k} · ${CODES[k]}</option>`).join('');
ff.innerHTML += [...new Set(R.flatMap(tagsOf))].sort().map(t => `<option>${esc(t)}</option>`).join('');
R.forEach(r => { r.name = r.variety_name || r.official_name_en || r.official_name_bn;
  r._s = [r.variety_name, r.official_name_en, r.official_name_bn, r.popular_name, r.breeding_line, r.pedigree, r.developer, r.variety_id, r.feature_tags].join(' ').toLowerCase(); });
R.forEach(r => { r._n = [r.variety_name, r.official_name_en, r.official_name_bn, r.popular_name].join(' ').toLowerCase().replace(/[\s\-]+/g, ''); });
let sortK = 'approval_date', sortDir = 1, page = 0, open = null; const PER = 40;
const norm = q => q.toLowerCase().replace(/[\s\-]+/g, '');
function filtered() {
  const q = $('#q').value.trim().toLowerCase(), qn = norm(q);
  const rank = r => !q ? 0 : r._n.includes(qn) ? 0 : 1;      // name matches before pedigree or line matches
  return R.filter(r => (!q || r._s.includes(q) || r._n.includes(qn)) && (!$('#fs').value || sector(r) === $('#fs').value) && (!fg.value || r.developer_group === fg.value)
      && (!$('#ft').value || r.rice_type === $('#ft').value) && (!fc.value || r.cgiar_role === fc.value) && (!ff.value || tagsOf(r).includes(ff.value)))
    .sort((a, b) => { const x = (a[sortK] || ''), y = (b[sortK] || ''); return rank(a) - rank(b) || (x < y ? -1 : x > y ? 1 : 0) * sortDir || a.approval_date.localeCompare(b.approval_date); });
}
function sourceCell(r) {
  const lab = srcLabel(r.local_file);
  if (r.source_url && !offline(r.source_url_status)) return link(r.source_url, lab) + (r.archived_url ? `<div class="bn">${link(r.archived_url, 'archived copy')}</div>` : '');
  if (r.archived_url) return link(r.archived_url, lab) + `<div class="st">original offline; archived copy</div>`;
  return esc(lab) + (r.source_url ? `<div class="st">original offline</div>` : '');
}
const CHECK = {key_check: 'matched the NSB meeting-date key', visual_check: 'confirmed on the page image', two_source: 'two independent sources agree',
  unvalidated: 'single machine-readable source', text: 'machine-readable text'};
const readable = s => (s || '').split(/;\s*/).filter(Boolean).map(x => { const m = x.match(/^([\w ]+)=(\w+)(?:\s*\(([^)]*)\))?/);
  return m ? `${m[1].replace(/_/g, ' ')}: ${CHECK[m[2]] || m[2].replace(/_/g, ' ')}` : x.replace(/_/g, ' '); }).join('; ');
const FLAG = {year_only: 'only the year is documented', date_single_source: 'date from a single source', institute_claim_only: 'documented only by the institute'};
const readableFlags = s => (s || '').split(/;\s*/).filter(Boolean).map(f => f.startsWith('has_conflicts') ? '' : (FLAG[f] || f.replace(/_/g, ' '))).filter(Boolean).join('; ');
const EVSRC = {special_traits_official: 'the official description (special traits)', identifying_traits_official: 'the official description (identifying traits)',
  stress_tolerance: 'the stress tolerance stated in the NSB minutes', quality_traits: 'the grain quality stated in the NSB minutes', key_traits: 'an institute or CGIAR summary',
  ecosystem: 'the stated ecosystem', recommended_region: 'the recommended region', cgiar_spia_flags: 'a SPIA (2025) flag', 'key_traits (TRIVSA screening)': 'a TRIVSA disease or stress rating'};
const readableEvidence = s => (s || '').split(' | ').filter(Boolean).map(x => { const i = x.indexOf(': '); const t = x.slice(0, i), src = x.slice(i + 2).split(', ');
  return `${t[0].toUpperCase() + t.slice(1)}, from ${src.map(c => EVSRC[c] || EVSRC[c.replace(/ \(TRIVSA screening\)/, '')] && (c.includes('TRIVSA') ? EVSRC['key_traits (TRIVSA screening)'] : EVSRC[c]) || c.replace(/_/g, ' ')).join(' and ')}.`; }).join(' ');
const EVENT = {release: 'released', registration: 'registered', extension_season_or_region: 'approval extended to a further season or region',
  denotification_proposed_deferred: 'withdrawal proposed and deferred', rename: 'renamed', 'recommendation_pending/deferred': 'decision deferred',
  import_permission: 'seed import permitted', provisional_release: 'released provisionally', full_release_after_provisional: 'full release after provisional release',
  condition_change: 'conditions of approval changed', status_change_other: 'status changed', suspension: 'seed multiplication suspended',
  registration_renewal_or_extension: 'registration renewed or extended', rejection: 'rejected'};
const parentsHtml = r => ((D.parents || {})[r.variety_id] || []).map(x => {
  const name = x.id ? `<a href="#${esc(x.id)}">${esc(x.l)}</a>` : esc(x.l);
  const tag = x.cg === 'Y' ? ` <span class="bn">${esc(x.c || 'CGIAR')} line</span>` : '';
  const role = x.role && x.role !== 'unknown' ? ` <span class="bn">${esc(x.role.replace(/_/g, ' '))}${x.dose ? ', ×' + esc(x.dose) : ''}</span>` : '';
  return name + tag + role; }).join('<br>');
const eventsHtml = r => ((D.events || {})[r.variety_id] || []).slice().sort((a, b) => (a.d || '').localeCompare(b.d || '')).map(x =>
  `${esc(x.d || '')} · NSB ${esc(x.m)} · ${esc(EVENT[x.t] || x.t.replace(/_/g, ' '))}${x.x ? ': ' + esc(x.x) : ''}`).join('<br>');
const depthHtml = r => !r.depth_to_cgiar ? '' : r.depth_to_cgiar === '0' ? 'the variety is itself a CGIAR line' :
  `${esc(r.depth_to_cgiar)} (${r.depth_to_cgiar === '1' ? 'parent' : r.depth_to_cgiar === '2' ? 'grandparent' : r.depth_to_cgiar + ' generations back'})${r.nearest_cgiar_ancestor ? ': ' + esc(r.nearest_cgiar_ancestor) : ''}`;
const links = s => (s || '').split(' | ').filter(u => /^https?:/.test(u)).map(u => link(u, u.replace(/^https?:\/\/(www\.)?/, '').slice(0, 70))).join('<br>');
function detail(r) {
  const feat = [['Stated traits', tagsOf(r).length ? `<span class="tags">${tagsOf(r).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</span>` : ''],
    ['Where each trait is stated', esc(readableEvidence(r.feature_evidence))], ['Special traits (official)', esc(r.special_traits_official)], ['Identifying traits (official)', esc(r.identifying_traits_official)],
    ['Trait description', r.trait_text_available === 'no' ? 'none found in the sources' : ''],
    ['Season', esc(r.season_std || r.season)], ['Ecosystem', esc([r.ecosystem_std, r.ecosystem].filter(Boolean).join(' · '))], ['Grain class', esc(r.grain_class)], ['Duration (days)', esc(r.duration_days)], ['Yield (t/ha)', esc(r.yield_t_ha)],
    ['Yield advantage over check', esc(r.yield_advantage_pct)], ['Check variety', esc(r.check_variety)], ['Recommended region', esc(r.recommended_region || r.region_scope)],
    ['Grain and quality', esc(r.quality_traits)], ['Stress tolerance', esc(r.stress_tolerance)], ['DUS result', esc(r.dus_result)], ['Trial sites (VCU)', esc(r.vcu_sites)]];
  const rows = [['Name as printed', esc(r.official_name_en)], ['Bangla name', esc(r.official_name_bn)], ['Popular name', esc(r.popular_name)], ['Developer (as printed)', esc(r.developer)],
    ['Approval route', esc((r.release_category || '').replace('NSB_release', 'Release by NSB (ছাড়করণ)').replace('NSB_registration', 'Registration by NSB (নিবন্ধন)').replace('pre_NSB_recommended', 'Recommended before the NSB existed'))],
    ['NSB decision', esc(r.approval_reference)], ['Gazette', esc([r.gazette_date, r.gazette_status].filter(Boolean).join(' · '))],
    ['Status, February 2026', r.status_as_of_2026 ? esc(r.status_as_of_2026) + (r.status_basis ? `<div class="bn">${esc(r.status_basis)}</div>` : '') : ''],
    ['Decisions after approval', ((D.events || {})[r.variety_id] || []).filter(x => !/^(release|registration)$/.test(x.t)).length ?
      eventsHtml({variety_id: r.variety_id}).split('<br>').filter(l => !/· (released|registered)(:|$)/.test(l)).join('<br>') : ''],
    ['Other names', esc(r.aliases)], ['Developer (standardised)', esc([r.developer_std, r.developer_type].filter(Boolean).join(' · '))], ['Breeding line', esc(r.breeding_line)], ['Pedigree', esc(r.pedigree)], ['Parents', parentsHtml(r)], ['Breeding method', esc(r.breeding_method)],
    ['Generations to the nearest CGIAR line', depthHtml(r)],
    ['CGIAR link', r.cgiar_role ? esc(`${r.cgiar_role} · ${CODES[r.cgiar_role]}`) : ''], ['CGIAR centre', esc(r.cgiar_center)], ['CGIAR lineage', esc(r.cgiar_lineage)],
    ['CGIAR own statements', esc(r.cgiar_independent)], ['CGIAR sources', links(r.cgiar_source_urls)], ['CGIAR evidence document', links(r.cgiar_evidence_url)],
    ['Codes in household surveys', esc((r.survey_codes || '').split(' | ').join('; '))],
    ['Key papers', links(r.key_papers)], ['Adoption (as reported)', esc(r.adoption)], ['Market segment', esc(r.market_segment)],
    ['How verified', esc(readable(r.validation_summary))], ['Sources disagree', esc((r.conflict_note || r.conflict_fields || '').split(' | ').join('; '))],
    ['Archived file', esc(r.local_file)], ['Quality notes', esc(readableFlags(r.flags))], ['Identifier', `<code>${esc(r.variety_id)}</code> · <a href="#${esc(r.variety_id)}">link to this variety</a>`]];
  const dl = (arr, cls) => `<dl class="${cls}">` + arr.filter(x => x[1]).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('') + '</dl>';
  const decs = (D.decisions || {})[r.variety_id] || [];
  const decHtml = decs.length ? `<h3 style="margin-top:14px">National Seed Board decisions (${decs.length})</h3>` + decs.map(x =>
    `<details style="margin:4px 0"><summary>${esc(x.d)} · NSB ${esc(x.m)} · ${esc((x.t || '').replace(/_/g, ' '))}${x.src ? ' · ' + link(x.src, 'minutes, p. ' + (x.pg || '')) : ''}</summary>
     ${x.h && !(x.p || '').startsWith(x.h.slice(0, 60)) ? `<p class="bn" style="margin:6px 0">${esc(x.h)}</p>` : ''}<p style="white-space:pre-wrap;margin:6px 0;font-size:13px">${esc(x.p)}</p>
     ${x.dec ? `<p style="margin:6px 0"><b>Decision:</b> ${esc(x.dec)}</p>` : ''}</details>`).join('') +
    '<p class="note">Text as read from the minutes (OCR or text layer; numbers verified on page images). Full text and every attribute: bgd_nsb_decisions_full.csv.</p>' : '';
  return `<h3 style="margin-top:0">Traits and agronomy</h3>${dl(feat, 'featgrid')}<h3>Identity, approval and sources</h3>${dl(rows, 'dl')}${decHtml}`;
}
const nsbShort = ref => { const m = (ref || '').match(/NSB (\d+\w*) meeting/); return m ? m[1] : clip(ref, 30); };
const shortStats = r => [/^[\d.\-–— ]+$/.test(r.duration_days || '') ? r.duration_days + ' days' : '', /^[\d.\-–— ]+$/.test(r.yield_t_ha || '') ? r.yield_t_ha + ' t/ha' : ''].filter(Boolean).join(' · ');
function render() {
  const rows = filtered(), pages = Math.max(1, Math.ceil(rows.length / PER)); page = Math.min(page, pages - 1);
  $('#cnt').textContent = `${rows.length} of ${R.length} varieties`;
  $('#pg').textContent = `Page ${page + 1} of ${pages}`; $('#prev').disabled = page === 0; $('#next').disabled = page >= pages - 1;
  const tb = $('#tb tbody'); tb.innerHTML = '';
  rows.slice(page * PER, page * PER + PER).forEach(r => {
    const tr = document.createElement('tr'); tr.className = 'row'; tr.tabIndex = 0;
    const code = r.cgiar_role || '5', tg = tagsOf(r);
    tr.innerHTML = `<td><div>${esc(r.name)}</div><div class="bn">${esc(r.official_name_bn)}</div></td>
      <td>${esc(r.developer_group)}<div class="bn">${sector(r)} · ${esc(r.rice_type)}</div></td>
      <td class="num">${esc(r.approval_date)}</td><td>${esc(nsbShort(r.approval_reference))}</td>
      <td>${tg.length ? `<span class="tags">${tg.slice(0, 4).map(t => `<span class="tag">${esc(t)}</span>`).join('')}${tg.length > 4 ? `<span class="bn">+${tg.length - 4}</span>` : ''}</span>` : ''}${shortStats(r) ? `<div class="bn">${esc(shortStats(r))}</div>` : ''}</td>
      <td><span class="code cc${code}" title="${esc(CODES[code])}">${code}</span>${r.cgiar_center ? ' <span class="bn">' + esc(r.cgiar_center) + '</span>' : ''}</td>
      <td>${sourceCell(r)}</td>`;
    const toggle = () => { open = open === r.variety_id ? null : r.variety_id; render();
      try { history.replaceState(null, '', open ? '#' + open : location.pathname + location.search); } catch (e) {} };
    tr.addEventListener('click', e => { if (e.target.closest('a')) return; toggle(); });
    tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    tb.appendChild(tr);
    if (open === r.variety_id) { const d = document.createElement('tr'); d.className = 'det'; d.innerHTML = `<td colspan="7">${detail(r)}</td>`; tb.appendChild(d); }
  });
  document.querySelectorAll('#tb th[data-k]').forEach(th => th.setAttribute('aria-sort', th.dataset.k === sortK ? (sortDir > 0 ? 'ascending' : 'descending') : 'none'));
}
['#q', '#fs', '#fg', '#ft', '#ff', '#fc'].forEach(s => $(s).addEventListener('input', () => { page = 0; render(); }));
$('#prev').onclick = () => { page--; render(); }; $('#next').onclick = () => { page++; render(); };
document.querySelectorAll('#tb th[data-k]').forEach(th => th.addEventListener('click', () => { const k = th.dataset.k; sortDir = sortK === k ? -sortDir : 1; sortK = k; render(); }));
const VIEWS = [...document.querySelectorAll('main > section[data-view]')].map(x => x.dataset.view);
function showView(v) {
  if (!VIEWS.includes(v) || (v === 'board' && !(D.attendance || []).length)) v = 'overview';
  document.querySelectorAll('main > section[data-view]').forEach(x => x.classList.toggle('active', x.dataset.view === v));
  document.querySelectorAll('nav.views a').forEach(a => { const on = a.dataset.view === v; a.classList.toggle('active', on); if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  if (v === 'figures') drawFigures();
  return v;
}
function route() {
  const h = decodeURIComponent(location.hash.slice(1));
  if (h.startsWith('RICE-')) { showView('register'); openFromHash(); }
  else { showView(h || 'overview'); if (h !== 'register') scrollTo({top: 0}); }
}
function openFromHash() {
  const id = decodeURIComponent(location.hash.slice(1)); const r = R.find(x => x.variety_id === id); if (!r) return;
  ['#q', '#fs', '#fg', '#ft', '#ff', '#fc'].forEach(s => $(s).value = ''); open = id; sortK = 'approval_date'; sortDir = 1;
  page = Math.floor(filtered().indexOf(r) / PER); render();
  const row = document.querySelector('#tb tr.det'); if (row) row.previousElementSibling.scrollIntoView({block: 'start'});
}
render(); route(); addEventListener('hashchange', route);
window.__register = {rows: R, detail};
// CSV of the rows currently selected by the filters
$('#csv').addEventListener('click', () => {
  const cols = ['variety_id', 'variety_name', 'official_name_bn', 'developer_group', 'sector', 'rice_type', 'release_category', 'approval_date', 'approval_reference',
    'gazette_date', 'breeding_line', 'pedigree', 'cgiar_role', 'cgiar_center', 'feature_tags', 'duration_days', 'yield_t_ha', 'source_url'];
  const q = v => /[",\n]/.test(v = String(v ?? '')) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const csv = '\ufeff' + [cols.join(','), ...filtered().map(r => cols.map(c => q(r[c])).join(','))].join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
  a.download = 'bgd_rice_varieties_selection.csv'; document.body.appendChild(a); a.click(); a.remove();
});

// ---------- board contacts (internal build only) ----------
if ((D.attendance || []).length) {
  document.querySelectorAll('.internal').forEach(e => e.hidden = false);
  const A = D.attendance, bo = $('#bo'), bm = $('#bm');
  bo.innerHTML += [...new Set(A.map(x => x.organisation_std).filter(Boolean))].sort().map(o => `<option>${esc(o)}</option>`).join('');
  bm.innerHTML += [...new Set(A.map(x => x.meeting_no))].sort((a, b) => b - a).map(m => `<option value="${esc(m)}">NSB ${esc(m)}</option>`).join('');
  A.forEach(x => x._s = [x.name_as_written, x.name_en, x.designation, x.organisation, x.organisation_std, x.phone, x.email].join(' ').toLowerCase());
  const tel = s => (s || '').split(' | ').filter(Boolean).map(n => /\?/.test(n) ? esc(n) : `<a href="tel:${esc(n.replace(/[^\d+]/g, ''))}">${esc(n)}</a>`).join('<br>');
  const mail = s => (s || '').split(' | ').filter(Boolean).map(m => /^[^\s@]+@[^\s@]+\.\w+$/.test(m) ? `<a href="mailto:${esc(m)}">${esc(m)}</a>` : esc(m)).join('<br>');
  const draw = () => {
    const q = $('#bq').value.trim().toLowerCase();
    const rows = A.filter(x => (!q || x._s.includes(q)) && (!bo.value || x.organisation_std === bo.value) && (!bm.value || x.meeting_no === bm.value))
      .sort((a, b) => (+b.meeting_no - +a.meeting_no) || (+a.serial - +b.serial));
    $('#bcnt').textContent = `${rows.length} of ${A.length} entries`;
    $('#btb tbody').innerHTML = rows.map(x => `<tr><td class="num">NSB ${esc(x.meeting_no)}<div class="bn">${esc(x.meeting_date)}</div></td>
      <td>${esc(x.name_en || x.name_as_written)}${x.name_en && x.name_en !== x.name_as_written ? `<div class="bn">${esc(x.name_as_written)}</div>` : ''}</td>
      <td>${esc(x.designation)}</td><td>${esc(x.organisation_std || x.organisation)}${x.organisation_std && x.organisation && x.organisation !== x.organisation_std ? `<div class="bn">${esc(x.organisation)}</div>` : ''}</td>
      <td class="num">${tel(x.phone)}</td><td>${mail(x.email)}</td><td>${esc(x.read_confidence)}</td>
      <td>${x.source_url ? link(x.source_url, 'minutes, p. ' + x.page) : esc('p. ' + x.page)}</td></tr>`).join('');
  };
  ['#bq', '#bo', '#bm'].forEach(s => $(s).addEventListener('input', draw)); draw();
}

// ---------- fish ----------
D.fish.slice().sort((a, b) => (a.release_date || '9').localeCompare(b.release_date || '9')).forEach(f => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${esc(f.strain_name_std || f.strain_name)}<div class="bn">${esc((f.strain_name || '').replace(/\s*\(TVC wording\)/, ''))}</div></td><td><i>${esc((f.species_scientific || '').split('(')[0])}</i></td>
    <td>${esc(f.release_basis)}</td><td>${esc(f.government_act)}</td><td class="num">${esc(f.release_date || '—')}</td>
    <td><span class="code cc${f.cgiar_role || '5'}" title="${esc(CODES[f.cgiar_role || '5'])}">${esc(f.cgiar_role || '5')}</span></td>`;
  $('#fishtb tbody').appendChild(tr);
});
D.fish_events.slice().sort((a, b) => (a.release_date || '9').localeCompare(b.release_date || '9')).forEach(e => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${esc(e.strain_name || e.event_id)}</td><td>${esc((e.event_type || '').replace(/^germplasm /, '').replace(/\(.*\)/, '').trim())}</td><td class="num">${esc(e.release_date || 'planned')}</td><td>${esc((e.developer || '').split('(')[0])}</td><td class="bn">${esc(e.notes || '')}</td>`;
  $('#fishev tbody').appendChild(tr);
});
const TYPE = {import_approval_ornamental: 'Ornamental species permitted for import', hatchery_permitted_species: 'Species hatcheries may produce', introduction_recorded: 'Exotic introduction (no approval instrument found)',
  technology_validation_listing: 'BFRI validated-technology listing', framework_instrument: 'Legal power (framework)', ban: 'Species ban', import_approval: 'Species permitted for broodstock or seed import',
  introduction_approval: 'Approval of a new species', policy: 'Policy', technology_transfer: 'Strain handover', strain_naming: 'Strain naming by ministry notification', brood_bank_supply: 'Brood bank supply',
  enforcement_directive: 'Enforcement directive', genetic_resource_protection: 'Genetic resource protection', ban_proposal: 'Proposed ban', strain_release: 'Strain release by institute',
  farm_permit_procedure: 'Farm permit procedure', implementation_circular: 'Implementation circular', health_certification_requirement: 'Health certification requirement', hatchery_permitted_input: 'Permitted hatchery input'};
(D.fish_groups || []).forEach(g => { const tr = document.createElement('tr');
  const per = g.first && g.last ? (g.first.slice(0, 4) === g.last.slice(0, 4) ? g.first.slice(0, 4) : `${g.first.slice(0, 4)}–${g.last.slice(0, 4)}`) : '';
  tr.innerHTML = `<td>${esc(TYPE[g.approval_type] || g.approval_type)}</td><td class="num r">${g.n}</td><td>${esc(g.bodies)}</td><td class="num">${esc(per)}</td>`; $('#fishg tbody').appendChild(tr); });
(D.fish_key_acts || []).slice().sort((a, b) => (a.approval_date || '9999').localeCompare(b.approval_date || '9999')).forEach(a => {
  const tr = document.createElement('tr');
  const ref = a.source_url && !offline(a.source_url_status) ? link(a.source_url, clip(a.approval_reference || 'source', 90)) : esc(a.approval_reference || '');
  tr.innerHTML = `<td class="num">${esc(a.approval_date || 'undated')}</td><td>${esc((a.name || '').replace(/\s*->\s*/g, ' to '))}<div class="bn"><i>${esc(a.species_scientific || '')}</i></div></td><td>${esc(TYPE[a.approval_type] || a.approval_type)}</td><td>${esc(a.approving_body || '')}</td><td>${ref}</td>`;
  $('#fishk tbody').appendChild(tr);
});

// ---------- verification tables ----------
(function () {
  const q = D.qa || {};
  (q.ocr_bands || []).forEach(b => { const tr = document.createElement('tr'); tr.innerHTML = `<td>${esc(b[0])}</td><td class="num r">${fmt(b[1])}</td><td class="num r">${fmt(b[2])}</td>`; $('#qa1 tbody').appendChild(tr); });
  const lab = {key_check: 'Matched the NSB meeting-date key', visual_check: 'Read by eye on the page image', two_source: 'Two independent sources agree', text: 'Machine-readable text, HTML, API or spreadsheet', unvalidated: 'Machine-readable, single source'};
  const agg = {}; (q.by_check || []).forEach(([m, c, n]) => { const k = (m === 'ocr' && c === 'unvalidated') ? 'ocr_unvalidated' : c; agg[k] = (agg[k] || 0) + n; });
  ['key_check', 'visual_check', 'two_source', 'unvalidated', 'text', 'ocr_unvalidated'].filter(k => agg[k]).forEach(k => { const tr = document.createElement('tr');
    tr.innerHTML = `<td>${esc(k === 'ocr_unvalidated' ? 'Read by OCR, not confirmed (kept out of the register)' : lab[k])}</td><td class="num r">${fmt(agg[k])}</td>`; $('#qa2 tbody').appendChild(tr); });
  $('#qanote').textContent = `${fmt(q.evidence_rows || 0)} evidence rows from ${fmt(q.n_sources || 0)} source files; ${fmt(q.n_conflicts || 0)} disagreeing values kept in the conflicts file. Mean OCR word confidence across ${fmt(q.ocr_pages || 0)} scanned pages: ${q.ocr_mean_conf ?? '–'}.`;
})();

// ---------- completeness and disagreements ----------
(function () {
  const inb = R.filter(r => r.rice_type === 'inbred'), hyb = R.filter(r => r.rice_type === 'hybrid');
  const F = [['Exact date of the approving meeting', r => (r.approval_date || '').length === 10], ['NSB meeting reference', r => /NSB \d/.test(r.approval_reference || '')],
    ['Gazette notification date', r => r.gazette_date], ['Breeding line', r => r.breeding_line], ['Pedigree', r => r.pedigree],
    ['CGIAR link determined (codes 1 to 4)', r => r.cgiar_role && r.cgiar_role !== '5'], ['Season', r => r.season_std || r.season],
    ['Duration', r => r.duration_min_days || r.duration_days], ['Yield', r => r.yield_t_ha], ['Ecosystem', r => r.ecosystem_std || r.ecosystem],
    ['Grain class', r => r.grain_class], ['Recommended region', r => r.recommended_region || r.region_scope], ['Any trait description', r => r.trait_text_available === 'yes'],
    ['At least one stated trait', r => r.feature_tags], ['Key paper', r => r.key_papers], ['Code in a household survey', r => r.survey_codes]];
  const cell = (rows, f) => { const n = rows.filter(f).length; return `${n} <span class="bn">(${Math.round(n / rows.length * 100)}%)</span>`; };
  $('#compl tbody').innerHTML = F.map(([k, f]) => `<tr><td>${k}</td><td class="num r">${cell(inb, f)}</td><td class="num r">${cell(hyb, f)}</td></tr>`).join('');
  const KIND = {substantive: 'different values', compatible: 'same value stated differently', date_1_year: 'dates one year apart', date_2plus_years: 'dates two or more years apart',
    date_same_year: 'different day in the same year', later_decision: 'a later Board decision changed it', later_notification: 'a later gazette notice changed it', formatting_only: 'formatting only'};
  $('#confl tbody').innerHTML = (D.conflicts_by_field || []).slice(0, 14).map(c =>
    `<tr><td>${esc(c.field.replace(/_/g, ' '))}</td><td class="num r">${c.n}</td><td>${esc(KIND[c.top] || c.top.replace(/_/g, ' '))}</td></tr>`).join('');
})();

// ---------- surveys ----------
(function () {
  const T = D.crosswalk_summary || []; if (!T.length) return;
  $('#cwtb tbody').innerHTML = T.map(x => `<tr><td>${esc(x.label)}</td><td class="num r">${x.n}</td><td class="num r">${x.resolved}</td><td class="num r">${x.brand_family}</td>
    <td class="num r">${x.not_approved_variety}</td><td class="num r">${x.generic_label}</td><td class="num r">${x.unmatched}</td></tr>`).join('');
})();

// ---------- references ----------
(function () {
  const by = {}; (D.references || []).forEach(r => (by[r.group] = by[r.group] || []).push(r));
  let n = 0;
  $('#reflist').innerHTML = Object.entries(by).map(([g, rs]) => `<div class="refgroup">${esc(g)}</div><ol class="refs" start="${n + 1}">` + rs.map(r => { n++;
    const main = r.url && !offline(r.url_status) ? link(r.url, r.url.includes('doi.org/') ? r.url.replace('https://', '') : 'source') : '';
    const arc = r.archived_url ? (main ? ' · ' : '') + link(r.archived_url, 'archived copy') : '';
    const off = r.url && offline(r.url_status) ? ' <span class="st">original offline</span>' : r.url && r.url_status === 'unchecked' ? ' <span class="st">link not checked</span>' : '';
    return `<li>${esc(r.citation)} ${main}${arc}${off}</li>`; }).join('') + '</ol>').join('');
})();

// ---------- files ----------
(D.files || []).forEach(f => { const tr = document.createElement('tr');
  const name = D.download_base !== null ? `<a href="${esc((D.download_base ?? 'data/') + f.file)}">${esc(f.file)}</a>` : esc(f.file);
  tr.innerHTML = `<td class="mono">${name}</td><td>${esc(f.desc)}</td><td>${esc(f.unit)}</td><td class="num r">${fmt(f.rows)}</td><td class="num r">${f.cols}</td><td class="num r">${f.mb < 0.1 ? '&lt;0.1' : f.mb}</td>`;
  $('#filetb tbody').appendChild(tr); });
})();
