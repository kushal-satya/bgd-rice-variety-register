/* Bangladesh Rice Variety Register: page logic.
   Text comes from content/text.md (editable; {{placeholders}} are computed below from the data).
   Data come from data/site_data.json. The standalone build inlines both as window.__SITE_TEXT__ / window.__SITE_DATA__. */
(async function () {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const BN = /[ঀ-৿]/;
const T = s => BN.test(s || '') ? `<span lang="bn">${esc(s)}</span>` : esc(s);      // marks Bangla text for screen readers and fonts
const fmt = n => Number(n).toLocaleString('en-US');
const pct = (n, d) => d ? Math.round(n / d * 100) + '%' : '–';
const link = (u, label) => u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(label)}</a>` : '';
const clip = (t, n) => { t = String(t || ''); if (t.length <= n) return t; const c = t.slice(0, n); return c.slice(0, Math.max(c.lastIndexOf(' '), n * 0.6 | 0)).replace(/[\s,;(\/]+$/, '') + '…'; };
const NS = 'http://www.w3.org/2000/svg';
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };

// ---------- load ----------
const D = window.__SITE_DATA__ || await (await fetch('data/site_data.json')).json();
const TEXT = window.__SITE_TEXT__ || await (await fetch('content/text.md')).text();
const R = D.rice;
const BYID = Object.fromEntries(R.map(r => [r.variety_id, r]));

// ---------- placeholders (documented in README.md) ----------
const sector = r => r.sector ? r.sector : (/^(Private company|Private or NGO inbred)$/.test(r.developer_group) ? 'private' : 'public');
const yrs = R.map(r => +r.approval_year).filter(Boolean);
const built = new Date(D.built + 'T00:00:00Z');
const inbreds = R.filter(r => r.rice_type === 'inbred');
const STATS = {
  n_rice: R.length,
  n_inbred: inbreds.length,
  n_hybrid: R.filter(r => r.rice_type === 'hybrid').length,
  n_public: R.filter(r => sector(r) === 'public').length,
  n_private: R.filter(r => sector(r) === 'private').length,
  n_brri: R.filter(r => r.developer_group === 'BRRI').length,
  n_bina: R.filter(r => r.developer_group === 'BINA').length,
  year_min: Math.min(...yrs), year_max: Math.max(...yrs),
  n_dated: R.filter(r => (r.approval_date || '').length === 10).length,
  n_gazette: R.filter(r => r.gazette_date).length,
  n_cgiar_linked: R.filter(r => ['1', '2', '3'].includes(r.cgiar_role)).length,
  n_cgiar_inbred_linked: inbreds.filter(r => ['1', '2', '3'].includes(r.cgiar_role)).length,
  n_cgiar_inbred_ancestry: inbreds.filter(r => ['1', '2'].includes(r.cgiar_role)).length,
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
  n_pedigree_inbred: inbreds.filter(r => r.pedigree).length,
  n_cgiar_known: R.filter(r => r.cgiar_role && r.cgiar_role !== '5').length,
  n_ocr_unconfirmed: ((D.qa || {}).by_check || []).filter(x => x[0] === 'ocr' && x[1] === 'unvalidated').reduce((a, x) => a + x[2], 0),
  n_date_conflicts: R.filter(r => /approval_date/.test(r.conflict_fields || '')).length,
  n_inbred_untagged: inbreds.filter(r => !r.feature_tags).length,
  n_fish_ornamental: ((D.fish_groups || []).find(g => g.approval_type === 'import_approval_ornamental') || {n: 0}).n,
  n_parent_links: Object.values(D.parents || {}).reduce((a, l) => a + l.length, 0),
  built: D.built, built_long: built.toLocaleDateString('en-GB', {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC'})
};
const fill = s => s.replace(/\{\{\s*(\w+)\s*\}\}/g, (m, k) => k in STATS ? (k.startsWith('n_') && typeof STATS[k] === 'number' ? fmt(STATS[k]) : String(STATS[k])) : m);

// ---------- minimal markdown ----------
function inline(s) {
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/\*([^*]+)\*/g, '<i>$1</i>').replace(/\[([^\]]+)\]\(((?:https?:|#)[^)\s]+)\)/g, (m, t, u) => u.startsWith('#') ? `<a href="${u}">${t}</a>` : `<a href="${u}" target="_blank" rel="noopener">${t}</a>`)
    .replace(/([ঀ-৿][ঀ-৿\s\-।]*[ঀ-৿])/g, '<span lang="bn">$1</span>');
}
function md(src) {
  const out = [];
  for (const para of src.trim().split(/\n\s*\n/)) {
    const lines = para.split('\n');
    if (lines.every(l => /^\s*[-*] /.test(l))) { out.push('<ul>' + lines.map(l => `<li>${inline(l.replace(/^\s*[-*] /, ''))}</li>`).join('') + '</ul>'); continue; }
    if (lines.every(l => /^\s*\d+\. /.test(l))) { out.push('<ol>' + lines.map(l => `<li>${inline(l.replace(/^\s*\d+\. /, ''))}</li>`).join('') + '</ol>'); continue; }
    const h = para.match(/^(#{2,4}) (.*)$/);
    if (h) { out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); continue; }
    out.push(`<p>${inline(lines.join(' '))}</p>`);
  }
  return out.join('');
}
const BLOCKS = {};
TEXT.split(/<!--\s*@([\w-]+)\s*-->/).forEach((part, i, arr) => { if (i % 2 === 1) BLOCKS[part] = (arr[i + 1] || '').trim(); });
document.querySelectorAll('[data-text]').forEach(node => {
  const src = fill(BLOCKS[node.dataset.text] || '');
  node.innerHTML = node.hasAttribute('data-inline') ? inline(src) : md(src);
});
const SITE_TITLE = fill(BLOCKS.title || document.title);
document.title = SITE_TITLE;

// ---------- shared ----------
const SER = [['pub_inb', 'Public inbred', 'var(--s-pub)', 'background:var(--s-pub)', ''], ['pub_hyb', 'Public hybrid', 'url(#hp)', '', 'hp'],
             ['pvt_inb', 'Private inbred', 'var(--s-pvt)', 'background:var(--s-pvt)', ''], ['pvt_hyb', 'Private hybrid', 'url(#hv)', '', 'hv']];
const series = r => (sector(r) === 'public' ? 'pub_' : 'pvt_') + (r.rice_type === 'hybrid' ? 'hyb' : 'inb');
const CODES = {'1': 'CGIAR line released directly', '2': 'CGIAR parent or earlier ancestor', '3': 'Collaboration or funding only', '4': 'No CGIAR line in the traceable pedigree', '5': 'Pedigree unknown'};
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
const hover = (node, html) => { node.addEventListener('mousemove', ev => showTip(ev, html())); node.addEventListener('pointerdown', ev => showTip(ev, html())); node.addEventListener('mouseleave', hideTip); };
// a data table under each figure: the numbers behind the chart, for keyboard, touch and screen-reader readers
function dataTable(id, head, rows, note) {
  const box = $('#' + id); if (!box) return;
  box.innerHTML = `<summary>Data for this figure</summary><div class="tw"><table><thead><tr>${head.map((h, i) => `<th scope="col"${i ? ' class="r"' : ''}>${h}</th>`).join('')}</tr></thead><tbody>` +
    rows.map(r => `<tr>${r.map((c, i) => i ? `<td class="num r">${c}</td>` : `<th scope="row">${c}</th>`).join('')}</tr>`).join('') + `</tbody></table></div>${note ? `<p class="note">${note}</p>` : ''}`;
}

// ---------- figures (drawn at the container's width; redrawn on resize) ----------
const widthOf = svg => Math.max(300, Math.round(svg.parentNode.getBoundingClientRect().width || 640));
const narrow = W => W < 560;
const YEARS = []; for (let y = STATS.year_min; y <= STATS.year_max; y++) YEARS.push(y);
const COUNT = {}; YEARS.forEach(y => COUNT[y] = {pub_inb: 0, pub_hyb: 0, pvt_inb: 0, pvt_hyb: 0});
R.forEach(r => { const y = +r.approval_year; if (COUNT[y]) COUNT[y][series(r)]++; });
function hatchDefs(svg) {
  const defs = el('defs', {}, svg);
  [['hp', 'var(--s-pub)'], ['hv', 'var(--s-pvt)']].forEach(([id, col]) => { const pt = el('pattern', {id, width: 4, height: 4, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)'}, defs);
    el('rect', {width: 4, height: 4, fill: 'var(--bg)'}, pt); el('rect', {width: 2, height: 4, fill: col}, pt); });
  const pat = el('pattern', {id: 'h5', width: 5, height: 5, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)'}, defs);
  el('rect', {width: 5, height: 5, fill: 'var(--c5)'}, pat); el('rect', {width: 2, height: 5, fill: 'var(--hatch)'}, pat);
}
// Figure 1: approvals per year in two aligned panels, public above and private below, on one scale
function fig1() {
  const svg = $('#f1'); svg.innerHTML = ''; hatchDefs(svg);
  const W = widthOf(svg), ph = narrow(W) ? 110 : 140, gap = 34, m = {l: 30, r: 8, t: 18, b: 24}, H = m.t + ph * 2 + gap + m.b;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const top = Math.ceil(Math.max(...YEARS.map(y => Math.max(COUNT[y].pub_inb + COUNT[y].pub_hyb, COUNT[y].pvt_inb + COUNT[y].pvt_hyb))) / 10) * 10;
  const iw = W - m.l - m.r, bw = iw / YEARS.length, step = narrow(W) ? 20 : 10;
  [['Public developers', 'pub', m.t], ['Seed companies and NGOs', 'pvt', m.t + ph + gap]].forEach(([title, s, y0]) => {
    const ys = v => y0 + ph - v / top * ph;
    el('text', {x: m.l, y: y0 - 6, class: 'lab'}, svg).textContent = title;
    for (let v = 0; v <= top; v += 10) { el('line', {x1: m.l, x2: W - m.r, y1: ys(v), y2: ys(v), class: v ? 'gl' : 'ax'}, svg);
      el('text', {x: m.l - 6, y: ys(v) + 3.5, 'text-anchor': 'end'}, svg).textContent = v; }
    YEARS.forEach((y, i) => {
      const c = COUNT[y], x = m.l + i * bw + (bw > 4 ? 1 : 0), w = Math.max(1, bw - (bw > 4 ? 2 : 0.5)), partial = y === STATS.year_max;
      const inb = c[s + '_inb'], hyb = c[s + '_hyb'];
      if (inb) el('rect', {x, y: ys(inb), width: w, height: ys(0) - ys(inb), fill: `var(--s-${s})`}, svg);
      if (hyb) el('rect', {x, y: ys(inb + hyb), width: w, height: ys(inb) - ys(inb + hyb) - (inb ? 1 : 0), fill: `url(#h${s === 'pub' ? 'p' : 'v'})`, stroke: `var(--s-${s})`, 'stroke-width': 0.8}, svg);
      if (partial && inb + hyb) el('rect', {x: x - 1.5, y: ys(inb + hyb) - 1.5, width: w + 3, height: ys(0) - ys(inb + hyb) + 1.5, fill: 'none', stroke: 'var(--ink-3)', 'stroke-dasharray': '2 2'}, svg);
      const hit = el('rect', {x: m.l + i * bw, y: y0, width: bw, height: ph, fill: 'transparent'}, svg);
      hover(hit, () => `<b>${y}</b>${partial ? ' (one meeting, 5 February)' : ''} · ${title.toLowerCase()}<div class="r"><span class="k">Inbred</span><span>${inb}</span></div><div class="r"><span class="k">Hybrid</span><span>${hyb}</span></div>`);
    });
  });
  YEARS.forEach((y, i) => { if (y % step === 0) el('text', {x: m.l + i * bw + bw / 2, y: H - 6, 'text-anchor': 'middle'}, svg).textContent = y; });
  const last = YEARS.length - 1, xl = m.l + last * bw + bw / 2;
  el('text', {x: xl, y: m.t + ph + gap + ph - (COUNT[STATS.year_max].pvt_inb + COUNT[STATS.year_max].pvt_hyb) / top * ph - 8, 'text-anchor': 'end', class: 'ann'}, svg).textContent = narrow(W) ? 'Feb 2026: one meeting' : 'Feb 2026: one meeting only';
  const first = R.filter(r => r.rice_type === 'hybrid').sort((a, b) => a.approval_date.localeCompare(b.approval_date))[0];
  if (first) { const i = +first.approval_year - YEARS[0], x = m.l + i * bw + bw / 2, y0 = m.t + ph + gap, ys = v => y0 + ph - v / top * ph;
    el('line', {x1: x, x2: x, y1: ys(COUNT[+first.approval_year].pvt_hyb + COUNT[+first.approval_year].pvt_inb) - 3, y2: ys(top * 0.7), class: 'annl'}, svg);
    el('text', {x: x - 4, y: ys(top * 0.7) - 5, 'text-anchor': 'end', class: 'ann'}, svg).textContent = narrow(W) ? 'First hybrids, 1998' : 'First hybrids registered, 40th NSB meeting, Sep 1998'; }
  dataTable('f1data', ['Year', 'Public inbred', 'Public hybrid', 'Private inbred', 'Private hybrid', 'All'],
    YEARS.filter(y => COUNT[y].pub_inb + COUNT[y].pub_hyb + COUNT[y].pvt_inb + COUNT[y].pvt_hyb).map(y => { const c = COUNT[y]; return [y + (y === STATS.year_max ? ' (one meeting)' : ''), c.pub_inb, c.pub_hyb, c.pvt_inb, c.pvt_hyb, c.pub_inb + c.pub_hyb + c.pvt_inb + c.pvt_hyb]; }), 'Years with no approvals are omitted.');
}
// Figure 2: cumulative stock of approved varieties
function fig2() {
  const svg = $('#f2'); svg.innerHTML = '';
  const W = widthOf(svg), H = narrow(W) ? 250 : 280, m = {l: 36, r: narrow(W) ? 108 : 120, t: 12, b: 24};
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const L = [['Public inbred', 'pub_inb', 'var(--s-pub)', ''], ['Private hybrid', 'pvt_hyb', 'var(--s-pvt)', ''], ['Public hybrid', 'pub_hyb', 'var(--s-pub)', '4 3'], ['Private inbred', 'pvt_inb', 'var(--s-pvt)', '4 3']];
  const cum = {}; L.forEach(([, k]) => { let a = 0; cum[k] = YEARS.map(y => (a += COUNT[y][k])); });
  const top = Math.ceil(Math.max(...L.map(([, k]) => cum[k][cum[k].length - 1])) / 50) * 50;
  const xs = y => m.l + (y - STATS.year_min) / (STATS.year_max - STATS.year_min) * (W - m.l - m.r), ys = v => m.t + (H - m.t - m.b) * (1 - v / top);
  for (let v = 0; v <= top; v += 50) { el('line', {x1: m.l, x2: W - m.r, y1: ys(v), y2: ys(v), class: v ? 'gl' : 'ax'}, svg);
    el('text', {x: m.l - 6, y: ys(v) + 3.5, 'text-anchor': 'end'}, svg).textContent = v; }
  YEARS.forEach(y => { if (y % (narrow(W) ? 20 : 10) === 0) el('text', {x: xs(y), y: H - 6, 'text-anchor': 'middle'}, svg).textContent = y; });
  const ends = [];
  L.forEach(([lab, k, col, dash]) => {
    el('path', {d: YEARS.map((y, i) => `${i ? 'L' : 'M'}${xs(y).toFixed(1)},${ys(cum[k][i]).toFixed(1)}`).join(''), fill: 'none', stroke: col, 'stroke-width': dash ? 1.6 : 2.2, 'stroke-dasharray': dash}, svg);
    const v = cum[k][cum[k].length - 1]; ends.push([ys(v), `${lab} ${v}`, col]);
  });
  ends.sort((a, b) => a[0] - b[0]); let prev = -99;
  ends.forEach(([y, t, col]) => { const yy = Math.max(y, prev + 14); prev = yy; el('text', {x: W - m.r + 6, y: yy + 4, class: 'lab', style: `fill:${col}`}, svg).textContent = t; });
  const hit = el('rect', {x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent'}, svg);
  hit.addEventListener('mousemove', ev => { const b = svg.getBoundingClientRect(), x = (ev.clientX - b.left) * W / b.width;
    const y = Math.round(STATS.year_min + (x - m.l) / (W - m.l - m.r) * (STATS.year_max - STATS.year_min)), i = Math.max(0, Math.min(YEARS.length - 1, y - STATS.year_min));
    showTip(ev, `<b>By end of ${YEARS[i]}</b>` + L.map(([lab, k]) => `<div class="r"><span class="k">${lab}</span><span>${cum[k][i]}</span></div>`).join('')); });
  hit.addEventListener('mouseleave', hideTip);
  dataTable('f2data', ['By end of', 'Public inbred', 'Public hybrid', 'Private inbred', 'Private hybrid'],
    YEARS.filter(y => y % 5 === 0 || y === 2009 || y === STATS.year_max).map(y => { const i = y - STATS.year_min; return [y + (y === STATS.year_max ? ' (to February)' : ''), cum.pub_inb[i], cum.pub_hyb[i], cum.pvt_inb[i], cum.pvt_hyb[i]]; }), 'Selected years: every fifth year, 2009 (when private hybrids overtook public inbreds) and the last year.');
}
// Figure 3: share of inbred varieties stating each trait, by decade
function fig3() {
  const svg = $('#f3'); svg.innerHTML = '';
  const inb = inbreds.filter(r => +r.approval_year);
  const decs = []; for (let d = Math.floor(STATS.year_min / 10) * 10; d <= STATS.year_max; d += 10) decs.push(d);
  const tot = {}; inb.forEach(r => tagsOf(r).forEach(t => tot[t] = (tot[t] || 0) + 1));
  const tags = Object.keys(tot).sort((a, b) => tot[b] - tot[a]);
  const cell = {}; inb.forEach(r => { const d = Math.floor(+r.approval_year / 10) * 10; tagsOf(r).forEach(t => { const k = t + '|' + d; cell[k] = (cell[k] || 0) + 1; }); });
  const nDec = {}; inb.forEach(r => { const d = Math.floor(+r.approval_year / 10) * 10; nDec[d] = (nDec[d] || 0) + 1; });
  const W = widthOf(svg), lw = narrow(W) ? 128 : 190, m = {l: lw, r: 46, t: 34, b: 6}, rowH = narrow(W) ? 20 : 22;
  const cw = (W - m.l - m.r) / decs.length, H = m.t + tags.length * rowH + m.b;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  decs.forEach((d, j) => { const x = m.l + j * cw + cw / 2;
    const part = d < STATS.year_min || d + 9 > STATS.year_max ? '*' : '';
    el('text', {x, y: 13, 'text-anchor': 'middle', class: 'lab'}, svg).textContent = (narrow(W) ? `’${String(d).slice(2)}s` : `${d}s`) + part;
    el('text', {x, y: 27, 'text-anchor': 'middle'}, svg).textContent = `n=${nDec[d] || 0}`; });
  el('text', {x: W - m.r + 6, y: 27}, svg).textContent = 'all';
  tags.forEach((t, i) => {
    const y = m.t + i * rowH;
    el('line', {x1: 0, x2: W, y1: y + rowH, y2: y + rowH, class: 'gl'}, svg);
    el('text', {x: m.l - 8, y: y + rowH / 2 + 4, 'text-anchor': 'end', class: 'lab'}, svg).textContent = narrow(W) ? t.replace('bacterial blight', 'blight').replace(' / deepwater / haor', ' / deepwater') : t;
    decs.forEach((d, j) => { const n = cell[t + '|' + d] || 0, sh = nDec[d] ? n / nDec[d] : 0, x = m.l + j * cw;
      if (n) { el('rect', {x: x + 2, y: y + 2, width: cw - 4, height: rowH - 4, fill: 'var(--s-pub)', 'fill-opacity': 0.10 + 0.55 * sh}, svg);
        el('text', {x: x + cw / 2, y: y + rowH / 2 + 4, 'text-anchor': 'middle', class: 'lab'}, svg).textContent = narrow(W) ? Math.round(sh * 100) : Math.round(sh * 100) + '%'; } });
    el('text', {x: W - m.r + 6, y: y + rowH / 2 + 4, class: 'lab'}, svg).textContent = pct(tot[t], inb.length);
    const hit = el('rect', {x: 0, y, width: W, height: rowH, fill: 'transparent'}, svg);
    hover(hit, () => `<b>${esc(t)}</b> · ${tot[t]} of ${inb.length} inbred varieties` + decs.map(d =>
      `<div class="r"><span class="k">${d}s</span><span>${cell[t + '|' + d] || 0} of ${nDec[d] || 0}</span></div>`).join(''));
  });
  dataTable('f3data', ['Stated trait', ...decs.map(d => `${d}s (n=${nDec[d] || 0})`), `All (n=${inb.length})`],
    tags.map(t => [esc(t), ...decs.map(d => `${cell[t + '|' + d] || 0}`), tot[t]]), 'Counts of inbred varieties; the chart shows each count as a share of the varieties approved in that decade.');
}

// ---------- CGIAR and lineage ----------
// Pedigree graph from the parent-child links: register varieties by id, other lines by their printed name.
const NODE = {}, KIDS = {};
const nkey = s => String(s || '').toLowerCase().replace(/[\s\-_.]+/g, '');
const BYNAME = {};   // a printed parent name that is exactly a register variety's name links to that variety
R.forEach(r => [r.variety_name, r.official_name_en].forEach(n => { const k = nkey(n); if (k && !(k in BYNAME)) BYNAME[k] = r.variety_id; }));
const nodeKey = x => x.id || BYNAME[nkey(x.l)] || ('L:' + x.l);
R.forEach(r => NODE[r.variety_id] = {key: r.variety_id, label: r.name || r.variety_name, year: +r.approval_year || null, reg: true, cg: ['1'].includes(r.cgiar_role) && r.depth_to_cgiar === '0', role: r.cgiar_role});
const PARENTS = {};
if (D.lineage && (D.lineage.edges || []).length) {
  // the pedigree graph built by build_pedigree.py (printed pedigrees plus sister-line and designation links)
  D.lineage.nodes.forEach(n => { if (!NODE[n.id]) NODE[n.id] = {key: n.id, label: n.label, year: +n.year || null, reg: n.kind === 'register variety', cg: n.kind === 'CGIAR line', centre: n.cgiar_center, ptype: n.parent_type || ''};
    else if (n.kind === 'CGIAR line') NODE[n.id].cg = true; });
  D.lineage.edges.forEach(e => { if (!NODE[e.source] || !NODE[e.target]) return;
    (PARENTS[e.target] = PARENTS[e.target] || []).push({key: e.source, role: e.role, basis: e.basis});
    (KIDS[e.source] = KIDS[e.source] || []).push({key: e.target, role: e.role}); });
} else {
  Object.entries(D.parents || {}).forEach(([child, ps]) => ps.forEach(x => {
    const k = nodeKey(x);
    if (!NODE[k]) NODE[k] = {key: k, label: x.l, year: null, reg: false, cg: x.cg === 'Y', centre: x.c};
    else if (x.cg === 'Y') NODE[k].cg = true;
    (KIDS[k] = KIDS[k] || []).push({key: child, role: x.role});
    (PARENTS[child] = PARENTS[child] || []).push({key: k, role: x.role, dose: x.dose});
  }));
}
function descendants(k) {   // every APPROVED variety descending from k (through any line), with the shortest number of generations
  const seen = new Map(), q = [[k, 0]];
  while (q.length) { const [n, g] = q.shift(); (KIDS[n] || []).forEach(c => { if (!seen.has(c.key)) { seen.set(c.key, g + 1); q.push([c.key, g + 1]); } }); }
  return new Map([...seen].filter(([key]) => NODE[key] && NODE[key].reg));
}
const FOUNDERS = Object.keys(KIDS).map(k => ({k, d: descendants(k)})).filter(x => x.d.size >= 2)
  .sort((a, b) => b.d.size - a.d.size || (NODE[a.k].label > NODE[b.k].label ? 1 : -1));
const DEPTH = [['0', 'Itself a CGIAR line', 'var(--d0)'], ['1', 'CGIAR parent', 'var(--d1)'], ['2', 'CGIAR grandparent', 'var(--d2)'], ['3+', 'CGIAR ancestor 3–5 generations back', 'var(--d3)'],
  ['collab', 'Collaboration or funding only', 'url(#hcol)'], ['none', 'No CGIAR line in the traceable pedigree', 'none'], ['unknown', 'Pedigree unknown', 'url(#h5)']];
const depthCat = r => r.cgiar_role === '5' || !r.cgiar_role ? 'unknown' : r.cgiar_role === '4' ? 'none' : r.cgiar_role === '3' ? 'collab'
  : r.depth_to_cgiar === '' || r.depth_to_cgiar == null ? (r.cgiar_role === '1' ? '0' : '1') : (+r.depth_to_cgiar >= 3 ? '3+' : String(+r.depth_to_cgiar));
const swatch = c => c[2] === 'resid' ? '<i class="sw resid"></i>' : c[2] === 'none' ? '<i class="sw empty"></i>' : c[2] === 'url(#h5)' ? '<i class="sw hatch"></i>' : c[2] === 'url(#hcol)' ? '<i class="sw hcol"></i>' : `<i class="sw" style="background:${c[2]}"></i>`;
// Figure 4: inbred approvals by generations to the nearest CGIAR line, five-year periods
function fig4() {
  const svg = $('#f4'); if (!svg) return; svg.innerHTML = ''; hatchDefs(svg);
  const defs = svg.querySelector('defs'), pc = el('pattern', {id: 'hcol', width: 5, height: 5, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(-45)'}, defs);
  el('rect', {width: 5, height: 5, fill: 'var(--bg)'}, pc); el('rect', {width: 2, height: 5, fill: 'var(--d2)'}, pc);
  $('#lg4').innerHTML = DEPTH.map(c => `<span>${swatch(c)}${c[1]}</span>`).join('');
  const W = widthOf(svg), m = {l: 64, r: 34, t: 6, b: 22}, rowH = 22, P = y => Math.floor(y / 5) * 5;
  const pers = []; for (let p = P(STATS.year_min); p <= STATS.year_max; p += 5) pers.push(p);
  const H = m.t + pers.length * rowH + m.b; svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const rows = pers.map(p => inbreds.filter(r => +r.approval_year && P(+r.approval_year) === p));
  const max = Math.ceil(Math.max(...rows.map(x => x.length)) / 10) * 10, xs = v => m.l + v / max * (W - m.l - m.r);
  for (let v = 0; v <= max; v += 10) { el('line', {x1: xs(v), x2: xs(v), y1: m.t, y2: H - m.b, class: v ? 'gl' : 'ax'}, svg); el('text', {x: xs(v), y: H - 6, 'text-anchor': 'middle'}, svg).textContent = v; }
  const table = [];
  pers.forEach((p, i) => {
    const rs = rows[i], c = Object.fromEntries(DEPTH.map(d => [d[0], rs.filter(r => depthCat(r) === d[0]).length]));
    const y = m.t + i * rowH + 4, h = rowH - 8, last = p + 4 >= STATS.year_max, lab = `${Math.max(p, STATS.year_min)}–${String(Math.min(p + 4, STATS.year_max)).slice(2)}`;
    el('text', {x: m.l - 8, y: y + h / 2 + 4, 'text-anchor': 'end', class: 'lab'}, svg).textContent = lab + (last ? '*' : '');
    let acc = 0;
    DEPTH.forEach(([k, , fillc]) => { if (!c[k]) return; const w = xs(acc + c[k]) - xs(acc);
      el('rect', {x: xs(acc) + 0.5, y, width: Math.max(0, w - 1), height: h, fill: fillc === 'none' ? 'var(--bg)' : fillc, stroke: fillc === 'none' ? 'var(--ink-3)' : 'none', 'stroke-width': 1}, svg); acc += c[k]; });
    el('text', {x: xs(rs.length) + 5, y: y + h / 2 + 4, class: 'lab'}, svg).textContent = rs.length;
    const hit = el('rect', {x: 0, y: y - 4, width: W, height: rowH, fill: 'transparent'}, svg);
    hover(hit, () => `<b>${lab}</b> · ${rs.length} inbred varieties${last ? ' (period incomplete)' : ''}` + DEPTH.filter(d => c[d[0]]).map(d => `<div class="r"><span class="k">${d[1]}</span><span>${c[d[0]]}</span></div>`).join(''));
    table.push([lab + (last ? '*' : ''), ...DEPTH.map(d => c[d[0]]), rs.length]);
  });
  dataTable('f4data', ['Period', ...DEPTH.map(d => d[1]), 'All inbred'], table, '* Period incomplete: approvals to February 2026.');
}
// Figure 5: lines with the most descendants among approved varieties
function fig5() {
  const svg = $('#f5'); if (!svg) return; svg.innerHTML = '';
  const top = FOUNDERS.slice(0, 14), W = widthOf(svg), lw = narrow(W) ? 120 : 170, m = {l: lw, r: 40, t: 6, b: 22}, rowH = 24, H = m.t + top.length * rowH + m.b;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const G = [['1', 'Children', 'var(--d1)'], ['2', 'Grandchildren', 'var(--d2)'], ['3', 'Later generations', 'var(--d3)']];
  $('#lg5').innerHTML = G.map(g => `<span><i class="sw" style="background:${g[2]}"></i>${g[1]}</span>`).join('') + '<span><b>● Bold name</b>: line bred at a CGIAR centre</span>';
  const max = Math.ceil(Math.max(...top.map(f => f.d.size)) / 10) * 10, xs = v => m.l + v / max * (W - m.l - m.r);
  for (let v = 0; v <= max; v += 10) { el('line', {x1: xs(v), x2: xs(v), y1: m.t, y2: H - m.b, class: v ? 'gl' : 'ax'}, svg); el('text', {x: xs(v), y: H - 6, 'text-anchor': 'middle'}, svg).textContent = v; }
  const table = [];
  top.forEach((f, i) => {
    const n = NODE[f.k], y = m.t + i * rowH + 5, h = rowH - 10, by = {1: 0, 2: 0, 3: 0};
    f.d.forEach(g => by[Math.min(3, g)]++);
    const a = el('a', {href: '#L-' + encodeURIComponent(f.k)}, svg);
    el('text', {x: m.l - 8, y: y + h / 2 + 4, 'text-anchor': 'end', class: 'lab link' + (n.cg ? ' cg' : '')}, a).textContent = clip(n.label, narrow(W) ? 16 : 26) + (n.cg ? ' ●' : '');
    let acc = 0; G.forEach(([g, , col]) => { if (!by[g]) return; el('rect', {x: xs(acc) + 0.5, y, width: Math.max(0, xs(acc + by[g]) - xs(acc) - 1), height: h, fill: col}, svg); acc += by[g]; });
    el('text', {x: xs(f.d.size) + 5, y: y + h / 2 + 4, class: 'lab'}, svg).textContent = f.d.size;
    const hit = el('rect', {x: m.l, y: y - 5, width: W - m.l, height: rowH, fill: 'transparent', style: 'cursor:pointer'}, svg);
    hit.addEventListener('click', () => { location.hash = 'L-' + encodeURIComponent(f.k); });
    hover(hit, () => `<b>${esc(n.label)}</b>${n.cg ? ' · CGIAR line' : ''} · ${f.d.size} approved varieties descend from it` + G.map(g => `<div class="r"><span class="k">${g[1]}</span><span>${by[g[0]]}</span></div>`).join('') + '<div class="k">Select to see its family tree.</div>');
    table.push([`<a href="#L-${encodeURIComponent(f.k)}">${esc(n.label)}</a>${n.cg ? ' (CGIAR line)' : ''}`, by[1], by[2], by[3], f.d.size]);
  });
  dataTable('f5data', ['Line', 'Children', 'Grandchildren', 'Later generations', 'All descendants'], table);
}
// Figure 6: share of rice plots in household surveys sown to varieties by CGIAR link (from the survey crosswalk)
function fig6() {
  const svg = $('#f6'), P = D.plot_cgiar || []; if (!svg) return;
  if (!P.length) { $('#f6wrap').hidden = true; return; }
  svg.innerHTML = ''; hatchDefs(svg);
  { const pc = el('pattern', {id: 'hcol', width: 5, height: 5, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(-45)'}, svg.querySelector('defs'));
    el('rect', {width: 5, height: 5, fill: 'var(--bg)'}, pc); el('rect', {width: 2, height: 5, fill: 'var(--d2)'}, pc); }
  const CATS = [['d0', 'Itself a CGIAR line', 'var(--d0)'], ['d1', 'CGIAR parent', 'var(--d1)'], ['d2', 'CGIAR grandparent', 'var(--d2)'], ['d3', 'CGIAR ancestor 3–5 generations back', 'var(--d3)'],
    ['collab', 'Collaboration or funding only', 'url(#hcol)'], ['none', 'No CGIAR line in the pedigree', 'none'], ['unknown', 'Pedigree unknown', 'url(#h5)'],
    ['brand_family', 'Brand family (several hybrids)', 'var(--c4)'], ['not_approved', 'Never approved (e.g. Swarna, Miniket)', 'var(--na)'], ['other', 'Residual code ("other", local or unlisted)', 'resid']];
  $('#lg6').innerHTML = CATS.map(c => `<span>${swatch(c)}${c[1]}</span>`).join('');
  const rounds = [...new Set(P.map(p => p.round))];
  const W = widthOf(svg), m = {l: narrow(W) ? 100 : 130, r: 10, t: 6, b: 22}, rowH = 38, H = m.t + rounds.length * rowH + m.b, xs = v => m.l + v * (W - m.l - m.r);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  [0, .25, .5, .75, 1].forEach(v => { el('line', {x1: xs(v), x2: xs(v), y1: m.t, y2: H - m.b, class: v ? 'gl' : 'ax'}, svg); el('text', {x: xs(v), y: H - 6, 'text-anchor': 'middle'}, svg).textContent = Math.round(v * 100) + '%'; });
  const table = [];
  rounds.forEach((rd, i) => {
    const rows = P.filter(p => p.round === rd), n = +((rows[0] || {}).denom || 0), y = m.t + i * rowH + 6, h = rowH - 16, star = /2011/.test(rd) ? '*' : '';
    el('text', {x: m.l - 8, y: y + h / 2 + 2, 'text-anchor': 'end', class: 'lab'}, svg).textContent = rd + star;
    el('text', {x: m.l - 8, y: y + h / 2 + 15, 'text-anchor': 'end'}, svg).textContent = `n=${fmt(n)} plots`;
    let acc = 0; const by = {};
    CATS.forEach(([k, , col]) => { const s = rows.filter(p => p.cat === k).reduce((a, p) => a + (+p.share || 0), 0); by[k] = s; if (!s) return;
      el('rect', {x: xs(acc) + 0.5, y, width: Math.max(0, xs(acc + s) - xs(acc) - 1), height: h, fill: col === 'none' ? 'var(--bg)' : col === 'resid' ? 'var(--c5)' : col, stroke: col === 'none' || col === 'resid' ? 'var(--ink-3)' : 'none', 'stroke-width': 1}, svg); acc += s; });
    const hit = el('rect', {x: 0, y: y - 6, width: W, height: rowH, fill: 'transparent'}, svg);
    hover(hit, () => `<b>${esc(rd)}</b> · ${fmt(n)} rice plots with a variety code` + CATS.filter(c => by[c[0]]).map(c => `<div class="r"><span class="k">${c[1]}</span><span>${Math.round(by[c[0]] * 1000) / 10}%</span></div>`).join(''));
    table.push([esc(rd) + star + ` (n=${fmt(n)})`, ...CATS.map(c => (Math.round(by[c[0]] * 1000) / 10) + '%')]);
  });
  dataTable('f6data', ['Survey round', ...CATS.map(c => c[1])], table, 'Shares of rice plot reports that carry a variety code, matched through the crosswalk. * The 2011–12 code list had no codes for Swarna, Miniket or local varieties, so those plots fall under the residual code and the round is not comparable with later ones.');
}
// Lineage explorer: ancestors to the left, descendants to the right, generations as columns
let LIN = null;
const VAGUE = /group name|unnamed|accession not stated|local type/;
const PTYPE = {'group name (not one variety)': 'The source prints a group or class name, not one variety; the exact parent cannot be identified.',
  'unnamed germplasm': 'The source does not name this parent.', 'wild species (accession not stated)': 'The source names the species only, not the accession used.',
  'local type name (not traceable to one line)': 'A local type name; it cannot be traced to one released variety.',
  'traditional variety (landrace)': 'A traditional variety (landrace) used as a parent.', 'wild species accession': 'A genebank accession of a wild species.',
  'named variety': 'A named variety from outside the register used as a parent.', 'breeding line or numbered variety': 'A breeding line or numbered variety from outside the register used as a parent.',
  'CGIAR line': 'A CGIAR line used as a parent.'};
const ptypeText = n => n.reg ? 'Select to centre the tree on it.' : (PTYPE[n.ptype] || 'A parent from outside the register.');
function lineage(k) {
  const svg = $('#lin'); if (!svg) return;
  if (!NODE[k]) { $('#lininfo').textContent = `No variety or breeding line with the identifier ${k} is in the pedigree graph. Choose one from the list.`; svg.innerHTML = ''; return; }
  LIN = k; svg.innerHTML = '';
  const n0 = NODE[k], r0 = BYID[k];
  const anc = [[k]], seenA = new Set([k]);
  for (let g = 1; g <= 5; g++) { const next = []; anc[g - 1].forEach(x => (PARENTS[x] || []).forEach(p => { if (!seenA.has(p.key)) { seenA.add(p.key); next.push(p.key); } })); if (!next.length) break; anc.push(next); }
  const des = [[k]], seenD = new Set([k]);
  for (let g = 1; g <= 4; g++) { const next = []; des[g - 1].forEach(x => (KIDS[x] || []).forEach(c => { if (!seenD.has(c.key)) { seenD.add(c.key); next.push(c.key); } })); if (!next.length) break; des.push(next); }
  des.forEach(col => col.sort((a, b) => (NODE[a].year || 9999) - (NODE[b].year || 9999)));
  const cols = [...anc.slice(1).reverse(), [k], ...des.slice(1)], centre = anc.length - 1, MAXN = 18;
  const W = Math.max(widthOf(svg), cols.length * 150), colW = W / cols.length, boxW = Math.min(138, colW - 14), boxH = 34, gapY = 8;
  const shown = cols.map(c => c.slice(0, MAXN)), H = 40 + Math.max(...shown.map(c => c.length + (cols[shown.indexOf(c)].length > MAXN ? 1 : 0))) * (boxH + gapY);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.style.minWidth = (cols.length * 150) + 'px';
  const pos = {};
  shown.forEach((c, j) => { const tot = c.length * (boxH + gapY), y0 = 34 + (H - 34 - tot) / 2;
    c.forEach((key, i) => pos[key] = {x: j * colW + (colW - boxW) / 2, y: y0 + i * (boxH + gapY)});
    const g = j - centre;
    el('text', {x: j * colW + colW / 2, y: 14, 'text-anchor': 'middle', class: 'lab'}, svg).textContent = g === 0 ? 'Selected' : g < 0 ? (g === -1 ? 'Parents' : g === -2 ? 'Grandparents' : `${-g} generations back`) : (g === 1 ? 'Children' : g === 2 ? 'Grandchildren' : `${g} generations on`);
    if (cols[j].length > MAXN) el('text', {x: j * colW + colW / 2, y: y0 + c.length * (boxH + gapY) + 12, 'text-anchor': 'middle'}, svg).textContent = `+${cols[j].length - MAXN} more`; });
  const edges = el('g', {}, svg);
  Object.keys(pos).forEach(key => (PARENTS[key] || []).forEach(p => { if (!pos[p.key] || !pos[key]) return;
    const a = pos[p.key], b = pos[key]; if (a.x >= b.x) return;
    const x1 = a.x + boxW, y1 = a.y + boxH / 2, x2 = b.x, y2 = b.y + boxH / 2, mx = (x1 + x2) / 2;
    el('path', {d: `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`, fill: 'none', stroke: NODE[p.key].cg ? 'var(--d1)' : 'var(--ink-3)', 'stroke-width': NODE[p.key].cg ? 1.6 : 1, opacity: 0.8,
      'stroke-dasharray': /inferred|sister/.test(p.basis || '') ? '1 3' : /mutant|somaclone|selection/.test(p.role || '') ? '3 2' : ''}, edges); }));
  Object.entries(pos).forEach(([key, p]) => {
    const n = NODE[key], isC = key === k, a = el('a', {href: n.reg ? '#L-' + encodeURIComponent(key) : '#L-' + encodeURIComponent(key), class: 'lnode'}, svg);
    el('rect', {x: p.x, y: p.y, width: boxW, height: boxH, rx: 2, fill: n.cg ? 'var(--d0)' : 'var(--surface)', stroke: n.cg ? 'none' : 'var(--ink-3)', 'stroke-dasharray': n.reg || n.cg ? '' : VAGUE.test(n.ptype) ? '1 2' : '3 2'}, a);
    if (isC) el('rect', {x: p.x - 3, y: p.y - 3, width: boxW + 6, height: boxH + 6, rx: 3, fill: 'none', stroke: 'var(--warn)', 'stroke-width': 2.5}, a);
    const fg = n.cg ? 'var(--bg)' : 'var(--ink)';
    el('text', {x: p.x + 7, y: p.y + 14, style: `fill:${fg};font-size:11.5px;font-weight:${isC ? 650 : 500}${VAGUE.test(n.ptype) ? ';font-style:italic' : ''}`}, a).textContent = clip(n.label, Math.floor(boxW / 6.6));
    el('text', {x: p.x + 7, y: p.y + 27, style: `fill:${fg};font-size:10.5px;opacity:.85`}, a).textContent = [n.reg ? `approved ${n.year || ''}` : (n.cg ? '' : 'breeding line'), n.cg ? `CGIAR line${n.centre ? ' · ' + n.centre : ''}` : ''].filter(Boolean).join(' · ');
    a.addEventListener('mousemove', ev => showTip(ev, `<b>${esc(n.label)}</b>${n.cg ? ' · CGIAR line' : ''}${n.reg ? ` · approved ${n.year || ''} · CGIAR link ${esc(BYID[key].cgiar_role || '5')}` : ' · not an approved variety'}<div class="k">${n.reg ? 'Select to centre the tree on it.' : ptypeText(n)}</div>`));
    a.addEventListener('mouseleave', hideTip);
  });
  const nA = seenA.size - 1, nD = [...seenD].filter(x => x !== k && NODE[x] && NODE[x].reg).length;
  $('#lininfo').innerHTML = `<b>${T(n0.label)}</b>${r0 ? ` · approved ${esc(r0.approval_date)} · ${esc(r0.developer_group)} · CGIAR link ${esc(r0.cgiar_role || '5')} (${esc(CODES[r0.cgiar_role || '5'])})` : n0.cg ? ' · CGIAR line' : ' · ' + esc(n0.ptype || 'not an approved variety') + '. ' + ptypeText(n0).replace(/\.$/, '')}. ` +
    `${nA ? `${nA} recorded ancestor${nA > 1 ? 's' : ''}` : 'No recorded parents'}${nD ? `; ${nD} approved descendant${nD > 1 ? 's' : ''}` : '; no approved descendants'}.` +
    (r0 ? ` <a href="#${esc(k)}">Open the full record</a>.` : '');
  $('#linq').value = n0.label;
}
const drawFigures = () => { if ($('#figures').classList.contains('active')) { fig1(); fig2(); fig3(); } if ($('#cgiar').classList.contains('active')) { fig4(); fig5(); fig6(); lineage(LIN || 'RICE-BRRI_DHAN29'); } };
let rz; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawFigures, 150); });
(function () {
  const opts = Object.values(NODE).filter(n => n.reg || KIDS[n.key]).sort((a, b) => a.label.localeCompare(b.label));
  $('#linlist').innerHTML = opts.map(n => `<option value="${esc(n.label)}"></option>`).join('');
  const go = () => { const v = $('#linq').value.trim().toLowerCase(); const n = opts.find(o => o.label.toLowerCase() === v) || opts.find(o => o.label.toLowerCase().includes(v)); if (n) location.hash = 'L-' + encodeURIComponent(n.key); };
  $('#linform').addEventListener('submit', e => { e.preventDefault(); go(); });
})();

// ---------- register ----------
const fg = $('#fg'), fc = $('#fc'), ff = $('#ff');
fg.innerHTML = '<option value="">All</option>' + [...new Set(R.map(r => r.developer_group))].sort().map(g => `<option>${esc(g)}</option>`).join('');
fc.innerHTML += ['1', '2', '3', '4', '5'].map(k => `<option value="${k}">${k} · ${CODES[k]}</option>`).join('');
ff.innerHTML += [...new Set(R.flatMap(tagsOf))].sort().map(t => `<option>${esc(t)}</option>`).join('');
$('#ckey').innerHTML = 'CGIAR link: ' + ['1', '2', '3', '4', '5'].map(k => `<span class="code cc${k}">${k}</span> ${CODES[k].toLowerCase()}`).join(' · ') + '.';
R.forEach(r => { r.name = r.variety_name || r.official_name_en || r.official_name_bn;
  r._s = [r.variety_name, r.official_name_en, r.official_name_bn, r.popular_name, r.aliases, r.breeding_line, r.pedigree, r.developer, r.variety_id, r.feature_tags].join(' ').toLowerCase();
  r._n = [r.variety_name, r.official_name_en, r.official_name_bn, r.popular_name].join(' ').toLowerCase().replace(/[\s\-]+/g, ''); });
let sortK = 'approval_date', sortDir = -1, page = 0, open = null; const PER = 40;
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
const CHECK = {key_check: 'matched the NSB meeting-date key', visual_check: 'confirmed on the page image by a vision-language model', two_source: 'two independent sources agree',
  unvalidated: 'single machine-readable source', text: 'machine-readable text'};
const readable = s => (s || '').split(/;\s*/).filter(Boolean).map(x => { const m = x.match(/^([\w ]+)=(\w+)(?:\s*\(([^)]*)\))?/);
  return m ? `${m[1].replace(/_/g, ' ')}: ${CHECK[m[2]] || m[2].replace(/_/g, ' ')}` : x.replace(/_/g, ' '); }).join('; ');
const FLAG = {year_only: 'only the year is documented', date_single_source: 'date from a single source', institute_claim_only: 'documented only by the institute'};
const readableFlags = s => (s || '').split(/;\s*/).filter(Boolean).map(f => f.startsWith('has_conflicts') ? '' : (FLAG[f] || f.replace(/_/g, ' '))).filter(Boolean).join('; ');
const EVSRC = {special_traits_official: 'the official description (special traits)', identifying_traits_official: 'the official description (identifying traits)',
  stress_tolerance: 'the stress tolerance stated in the NSB minutes', quality_traits: 'the grain quality stated in the NSB minutes', key_traits: 'an institute or CGIAR summary',
  ecosystem: 'the stated ecosystem', recommended_region: 'the recommended region', cgiar_spia_flags: 'a SPIA (2025) flag', 'key_traits (TRIVSA screening)': 'a TRIVSA disease or stress rating'};
const readableEvidence = s => (s || '').split(' | ').filter(Boolean).map(x => { const i = x.indexOf(': '); if (i < 0) return x; const t = x.slice(0, i), src = x.slice(i + 2).split(', ');
  return `${t[0].toUpperCase() + t.slice(1)}, from ${src.map(c => EVSRC[c] || c.replace(/_/g, ' ')).join(' and ')}.`; }).join(' ');
const EVENT = {release: 'released', registration: 'registered', extension_season_or_region: 'approval extended to a further season or region',
  denotification_proposed_deferred: 'withdrawal proposed and deferred', rename: 'renamed', 'recommendation_pending/deferred': 'decision deferred',
  import_permission: 'seed import permitted', provisional_release: 'released provisionally', full_release_after_provisional: 'full release after provisional release',
  condition_change: 'conditions of approval changed', status_change_other: 'status changed', suspension: 'suspended',
  registration_renewal_or_extension: 'registration renewed or extended', rejection: 'rejected'};
const parentsHtml = r => ((D.parents || {})[r.variety_id] || []).map(x => {
  const name = x.id ? `<a href="#${esc(x.id)}">${T(x.l)}</a>` : T(x.l);
  const tag = x.cg === 'Y' ? ` <span class="bn">${esc(x.c || 'CGIAR')} line</span>` : '';
  const role = x.role && x.role !== 'unknown' ? ` <span class="bn">${esc(x.role.replace(/_/g, ' '))}${x.dose ? ', ×' + esc(x.dose) : ''}</span>` : '';
  return name + tag + role; }).join('<br>');
const laterDecisions = r => ((D.events || {})[r.variety_id] || []).filter(x => !/^(release|registration)$/.test(x.t)).slice().sort((a, b) => (a.d || '').localeCompare(b.d || ''))
  .map(x => `${esc(x.d || '')} · NSB ${esc(x.m)} · ${esc(EVENT[x.t] || x.t.replace(/_/g, ' '))}${x.x ? ': ' + T(x.x) : ''}`).join('<br>');
const depthHtml = r => r.depth_to_cgiar === '' || r.depth_to_cgiar == null ? '' : r.depth_to_cgiar === '0' ?
  (/mutant|somaclon|selection/i.test(r.cgiar_derivation || '') ? (() => {
    const src = ((D.parents || {})[r.variety_id] || []).find(x => /mutant|somaclone|selection/.test(x.role || '')) || {};
    const line = src.l || (r.nearest_cgiar_ancestor !== r.name ? r.nearest_cgiar_ancestor : '');
    const kind = /selection/i.test(src.role || r.cgiar_derivation) ? 'selection' : /somaclon/i.test(src.role || '') ? 'somaclonal derivative' : 'mutant';
    return `0: a ${kind} of the CGIAR line ${esc(line || 'named in the pedigree')}, made in Bangladesh`; })() : 'the variety is itself a CGIAR line') :
  `${esc(r.depth_to_cgiar)} (${r.depth_to_cgiar === '1' ? 'parent' : r.depth_to_cgiar === '2' ? 'grandparent' : r.depth_to_cgiar + ' generations back'})${r.nearest_cgiar_ancestor ? ': ' + esc(r.nearest_cgiar_ancestor) : ''}`;
const links = s => (s || '').split(' | ').filter(u => /^https?:/.test(u)).map(u => link(u, u.replace(/^https?:\/\/(www\.)?/, '').slice(0, 70))).join('<br>');
const ROUTE = {NSB_release: 'Release by the National Seed Board (ছাড়করণ)', NSB_registration: 'Registration by the National Seed Board (নিবন্ধন)', pre_NSB_recommended: 'Recommended before the National Seed Board existed'};
const status = r => r.legal_status_2026 || r.status_as_of_2026 || '';
function detail(r) {
  const dl = arr => `<dl class="dl">` + arr.filter(x => x[1]).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('') + '</dl>';
  const ident = [['Name as printed', T(r.official_name_en)], ['Bangla name', T(r.official_name_bn)], ['Popular name', T(r.popular_name)], ['Other names', T(r.aliases)],
    ['Developer as printed in the source', T(r.developer)], ['Developer', esc([r.developer_std, r.developer_type].filter(Boolean).join(' · '))],
    ['National research institute', esc(r.nars_institute)], ['Breeding division', r.nars_division ? esc(r.nars_division) + (r.nars_division_basis ? ` <span class="bn">${esc(r.nars_division_basis)}</span>` : '') : ''],
    ['Proposer at the Board meeting (as printed)', T(r.proposer_as_printed)],
    ['Approval route', T(ROUTE[r.release_category] || r.release_category)], ['Year released by the institute', esc(r.institute_release_year && r.institute_release_year !== r.approval_year ? r.institute_release_year + ' (the Board approval year is ' + r.approval_year + ')' : '')], ['Approving meeting', T(r.approval_reference)],
    ['Gazette notification', esc([r.gazette_date, r.gazette_status].filter(Boolean).join(' · '))],
    ['Legal status at the 115th meeting (5 Feb 2026)', status(r) ? esc(status(r)) + (r.status_basis ? `<div class="bn">${T(r.status_basis)}</div>` : '') : ''],
    ['Board decisions after approval', laterDecisions(r)], ['Hybrid seed source', esc(r.hybrid_seed_source && r.hybrid_seed_source !== 'unknown' ? r.hybrid_seed_source : '')],
    ['Identifier', `<code>${esc(r.variety_id)}</code> · <a href="#${esc(r.variety_id)}">permanent link</a>`]];
  const ped = [['Breeding line', T(r.breeding_line)], ['Pedigree', T(r.pedigree)], ['Parents', parentsHtml(r)], ['Breeding method', esc(r.breeding_method)],
    ['CGIAR link', r.cgiar_role ? `<span class="code cc${esc(r.cgiar_role)}">${esc(r.cgiar_role)}</span> ${esc(CODES[r.cgiar_role])}` : ''],
    ['Generations to the nearest CGIAR line', depthHtml(r)], ['CGIAR centre', esc(r.cgiar_center)], ['CGIAR lineage', T(r.cgiar_lineage)],
    ['Family tree', NODE[r.variety_id] ? `<a href="#L-${encodeURIComponent(r.variety_id)}">Show the ancestors and descendants of this variety</a>` : '']];
  const tr = [['Stated traits', tagsOf(r).length ? `<span class="tags">${tagsOf(r).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</span>` : (r.trait_text_available === 'no' ? 'no trait description found in the sources' : 'none stated')],
    ['Where each trait is stated', esc(readableEvidence(r.feature_evidence))], ['Special traits (official)', T(r.special_traits_official)], ['Identifying traits (official)', T(r.identifying_traits_official)],
    ['Season', esc(r.season_std || r.season)], ['Ecosystem', T([r.ecosystem_std, r.ecosystem].filter(Boolean).join(' · '))], ['Grain class', esc(r.grain_class)],
    ['Duration (days)', T(r.duration_days)], ['Yield (t/ha)', T(r.yield_t_ha) + (r.yield_basis ? ` <span class="bn">${esc(r.yield_basis)}</span>` : '')],
    ['Yield criterion over the check variety (%)', esc(r.yield_criterion_pct || r.yield_advantage_pct)], ['Check variety', T(r.check_variety)], ['Recommended region', T(r.recommended_region || r.region_scope)],
    ['Grain and quality', T(r.quality_traits)], ['Stress tolerance', T(r.stress_tolerance)], ['DUS result', T(r.dus_result)], ['Trial sites (VCU)', T(r.vcu_sites)]];
  const SEAS = ['aus', 'aman', 'boro'], ROWS = [['Yield potential (t/ha)', 'yield_potential', '_t_ha'], ['Duration (days)', 'duration', '_days'], ['Plant height (cm)', 'plant_height', '_cm']];
  const sw = ROWS.filter(([, g, u]) => SEAS.some(x => r[`${g}_${x}${u}`]));
  const seasonTable = sw.length ? `<table class="mini"><thead><tr><th></th>${SEAS.map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>` +
    sw.map(([l, g, u]) => `<tr><th>${l}</th>${SEAS.map(x => `<td>${esc(r[`${g}_${x}${u}`] || '')}</td>`).join('')}</tr>`).join('') + '</tbody></table>' : '';
  const att = [['By season, from official lists and handbooks', seasonTable], ['Variety type', esc(r.variety_type)], ['Germplasm origin', T(r.germplasm_origin)],
    ['Grain type', esc(r.grain_type)], ['Grain size as printed', T(r.grain_size_text)], ['Aleurone colour', esc(r.aleurone_colour)], ['Length/breadth ratio', esc(r.lb_ratio)],
    ['Amylose (%)', esc(r.amylose_pct)], ['Protein (%)', esc(r.protein_pct)], ['Zinc (mg/kg)', esc(r.zinc_mg_kg)], ['Iron (mg/kg)', esc(r.iron_mg_kg)], ['Glycemic index', esc(r.glycemic_index)],
    ['Target ecosystem', T(r.target_ecosystem)],
    ['Where these values are printed', esc(['yield_potential', 'duration', 'plant_height', 'grain', 'grain_quality', 'germplasm_origin', 'target_ecosystem'].map(g => r[g + '_source'] ? g.replace(/_/g, ' ') + ': ' + r[g + '_source'] : '').filter(Boolean).join(' · '))]];
  const evid = [['Codes in household surveys', esc((r.survey_codes || '').split(' | ').join('; '))], ['What CGIAR sources say', T(r.cgiar_independent)],
    ['CGIAR sources', links(r.cgiar_source_urls)], ['CGIAR evidence document', links(r.cgiar_evidence_url)], ['Key papers', links(r.key_papers)],
    ['Adoption (as reported)', T(r.adoption)], ['Market segment (GloMIP)', esc((r.market_segment || '').replace(/^[\s|]+|[\s|]+$/g, '').replace(/\s*\|\s*\|\s*/g, ' | '))], ['How the values were verified', esc(readable(r.validation_summary))],
    ['Where sources disagree', T((r.conflict_note || r.conflict_fields || '').replace(/\s*\((?:DS|RB|[A-Z]{2})-[A-Z]?\d+\)/g, '').split(' | ').join('; '))],
    ['Main source', sourceCell(r)], ['Quality notes', esc(r.quality_notes || readableFlags(r.flags))]];
  const decs = (D.decisions || {})[r.variety_id] || [];
  const decHtml = decs.length ? `<details class="sec"><summary>National Seed Board decisions (${decs.length}), with the text of the minutes</summary>` + decs.map(x =>
    `<details class="dec"><summary>${esc(x.d)} · NSB ${esc(x.m)} · ${esc((x.t || '').replace(/_/g, ' '))}${x.src ? ' · ' + link(x.src, 'minutes, p. ' + (x.pg || '')) : ''}</summary>
     ${x.h && !(x.p || '').startsWith(x.h.slice(0, 60)) ? `<p class="bn">${T(x.h)}</p>` : ''}<p class="mins">${T(x.p)}</p>
     ${x.dec ? `<p><b>Decision:</b> ${T(x.dec)}</p>` : ''}</details>`).join('') +
    '<p class="note">Text as read from the minutes (OCR or text layer; numbers verified on page images). Full text and every attribute: bgd_nsb_decisions_full.csv.</p></details>' : '';
  return `<div class="rechead" id="rec-${esc(r.variety_id)}"><h3 class="rectitle">${esc(r.name)} <span lang="bn" class="bn">${esc(r.official_name_bn)}</span></h3>
      <p class="recsub">${esc(r.developer_group)} · ${esc(sector(r))} ${esc(r.rice_type)} · approved ${esc(r.approval_date)}${/NSB \d/.test(r.approval_reference || '') ? ' · ' + esc(nsbLong(r.approval_reference)) : ''}</p></div>
    <h4>Identity and approval</h4>${dl(ident)}<h4>Pedigree and CGIAR link</h4>${dl(ped)}<h4>Traits and agronomy</h4>${dl(tr)}${att.some(x => x[1]) ? `<h4>Attributes by season and grain quality</h4>${dl(att)}` : ''}
    <details class="sec"><summary>Evidence, sources and literature</summary>${dl(evid)}</details>${decHtml}`;
}
const nsbShort = ref => { const m = (ref || '').match(/NSB (\d+\w*) meeting/); return m ? m[1] : clip(ref, 30); };
const nsbLong = ref => { const m = (ref || '').match(/NSB (\d+\w*) meeting/); return m ? `${m[1]} NSB meeting` : ''; };
const shortStats = r => [/^[\d.\-–— ]+$/.test(r.duration_days || '') ? r.duration_days + ' days' : '', /^[\d.\-–— ]+$/.test(r.yield_t_ha || '') ? r.yield_t_ha + ' t/ha' : ''].filter(Boolean).join(' · ');
function render() {
  const rows = filtered(), pages = Math.max(1, Math.ceil(rows.length / PER)); page = Math.min(page, pages - 1);
  $('#cnt').textContent = `${rows.length} of ${R.length} varieties`;
  $('#pg').textContent = `Page ${page + 1} of ${pages}`; $('#prev').disabled = page === 0; $('#next').disabled = page >= pages - 1;
  const tb = $('#tb tbody'); tb.innerHTML = '';
  rows.slice(page * PER, page * PER + PER).forEach(r => {
    const tr = document.createElement('tr'); tr.className = 'row' + (open === r.variety_id ? ' isopen' : ''); tr.id = 'row-' + r.variety_id;
    const code = r.cgiar_role || '5', tg = tagsOf(r), isOpen = open === r.variety_id;
    tr.innerHTML = `<td><button type="button" class="vname" aria-expanded="${isOpen}" aria-controls="det-${esc(r.variety_id)}">${esc(r.name)}</button><div class="bn" lang="bn">${esc(r.official_name_bn)}</div></td>
      <td>${esc(r.developer_group)}<div class="bn">${esc(sector(r))} · ${esc(r.rice_type)}</div></td>
      <td class="num">${esc(r.approval_date)}</td><td class="num">${esc(nsbShort(r.approval_reference))}</td>
      <td>${tg.length ? `<span class="tags">${tg.slice(0, 4).map(t => `<span class="tag">${esc(t)}</span>`).join('')}${tg.length > 4 ? `<span class="bn">+${tg.length - 4}</span>` : ''}</span>` : ''}${shortStats(r) ? `<div class="bn">${esc(shortStats(r))}</div>` : ''}</td>
      <td><span class="code cc${code}" title="${esc(CODES[code])}">${code}</span>${r.cgiar_center ? ' <span class="bn">' + esc(r.cgiar_center) + '</span>' : ''}</td>
      <td>${sourceCell(r)}</td>`;
    const toggle = () => { open = isOpen ? null : r.variety_id; render();
      try { history.replaceState(null, '', '#' + (open || 'register')); } catch (e) {}
      document.title = (open ? r.name + ' · ' : 'Register · ') + SITE_TITLE;
      const b = document.querySelector(`#row-${CSS.escape(r.variety_id)} button.vname`); if (b) b.focus({preventScroll: true}); };
    tr.querySelector('button.vname').addEventListener('click', toggle);
    tr.addEventListener('click', e => { if (e.target.closest('a,button')) return; toggle(); });
    tb.appendChild(tr);
    if (isOpen) { const d = document.createElement('tr'); d.className = 'det'; d.id = 'det-' + r.variety_id; d.innerHTML = `<td colspan="7">${detail(r)}</td>`; tb.appendChild(d); }
  });
  document.querySelectorAll('#tb th[data-k]').forEach(th => th.setAttribute('aria-sort', th.dataset.k === sortK ? (sortDir > 0 ? 'ascending' : 'descending') : 'none'));
}
['#q', '#fs', '#fg', '#ft', '#ff', '#fc'].forEach(s => $(s).addEventListener('input', () => { page = 0; render(); }));
$('#prev').onclick = () => { page--; render(); }; $('#next').onclick = () => { page++; render(); };
document.querySelectorAll('#tb th[data-k]').forEach(th => { const lab = th.textContent; th.innerHTML = `<button type="button" class="sort">${lab}</button>`;
  th.querySelector('button').addEventListener('click', () => { const k = th.dataset.k; sortDir = sortK === k ? -sortDir : (k === 'approval_date' ? -1 : 1); sortK = k; render(); }); });
if (innerWidth < 600) $('details.filters').open = false;   // on a phone the filters start folded
// overview search box hands the query to the register
$('#ovq').addEventListener('submit', e => { e.preventDefault(); $('#q').value = $('#ovqi').value; page = 0; open = null; render(); location.hash = 'register'; });

// ---------- views and routing ----------
const VIEWS = [...document.querySelectorAll('main > section[data-view]')].map(x => x.dataset.view);
function setNavHeight() { document.documentElement.style.setProperty('--navh', ($('nav.views').offsetHeight || 46) + 'px'); }
function showView(v, focus) {
  if (!VIEWS.includes(v) || (v === 'board' && !(D.attendance || []).length)) v = 'overview';
  document.querySelectorAll('main > section[data-view]').forEach(x => x.classList.toggle('active', x.dataset.view === v));
  document.querySelectorAll('nav.views a').forEach(a => { const on = a.dataset.view === v; a.classList.toggle('active', on); if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  const h = $('#' + v + ' h2'); document.title = (v === 'overview' || !h ? '' : h.textContent + ' · ') + SITE_TITLE;
  if (focus && h) { h.tabIndex = -1; h.focus({preventScroll: true}); }
  setNavHeight(); drawFigures();
  return v;
}
function route(ev) {
  const h = decodeURIComponent(location.hash.slice(1));
  if (h.startsWith('RICE-')) { showView('register'); openFromHash(h); }
  else if (h.startsWith('L-')) { showView('cgiar'); lineage(h.slice(2)); const box = $('#linbox'); if (box) box.scrollIntoView({block: 'start'}); }
  else { showView(h || 'overview', !!ev); if (h !== 'register' || !open) scrollTo({top: 0}); }
}
function openFromHash(id) {
  const r = BYID[id]; if (!r) return;
  ['#q', '#fs', '#fg', '#ft', '#ff', '#fc'].forEach(s => $(s).value = ''); open = id; sortK = 'approval_date'; sortDir = -1;
  page = Math.floor(filtered().indexOf(r) / PER); render();
  document.title = r.name + ' · ' + SITE_TITLE;
  const row = document.getElementById('row-' + id); if (row) row.scrollIntoView({block: 'start'});
}
render(); route(); addEventListener('hashchange', route); addEventListener('resize', setNavHeight);
window.__register = {rows: R, detail, lineage, NODE};
// CSV of the rows currently selected by the filters
$('#csv').addEventListener('click', () => {
  const cols = ['variety_id', 'variety_name', 'official_name_bn', 'developer_group', 'sector', 'rice_type', 'release_category', 'approval_date', 'approval_reference',
    'gazette_date', 'breeding_line', 'pedigree', 'cgiar_role', 'depth_to_cgiar', 'cgiar_center', 'feature_tags', 'duration_days', 'yield_t_ha', 'source_url'];
  const q = v => /[",\n]/.test(v = String(v ?? '')) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const csv = '﻿' + [cols.join(','), ...filtered().map(r => cols.map(c => q(r[c])).join(','))].join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
  a.download = 'bgd_rice_varieties_selection.csv'; document.body.appendChild(a); a.click(); a.remove();
});

// ---------- board contacts (internal build only) ----------
if ((D.attendance || []).length && $('#board')) {
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
      <td>${T(x.name_en || x.name_as_written)}${x.name_en && x.name_en !== x.name_as_written ? `<div class="bn">${T(x.name_as_written)}</div>` : ''}</td>
      <td>${T(x.designation)}</td><td>${esc(x.organisation_std || x.organisation)}${x.organisation_std && x.organisation && x.organisation !== x.organisation_std ? `<div class="bn">${T(x.organisation)}</div>` : ''}</td>
      <td class="num">${tel(x.phone)}</td><td>${mail(x.email)}</td><td>${esc(x.read_confidence)}</td>
      <td>${x.source_url ? link(x.source_url, 'minutes, p. ' + x.page) : esc('p. ' + x.page)}</td></tr>`).join('');
  };
  ['#bq', '#bo', '#bm'].forEach(s => $(s).addEventListener('input', draw)); draw();
}

// ---------- fish ----------
D.fish.slice().sort((a, b) => (a.release_date || '9').localeCompare(b.release_date || '9')).forEach(f => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${esc(f.strain_name_std || f.strain_name)}<div class="bn">${T((f.strain_name || '').replace(/\s*\(TVC wording\)/, ''))}</div></td><td><i>${esc((f.species_scientific || '').split('(')[0])}</i></td>
    <td>${esc(f.release_basis)}</td><td>${esc(f.government_act)}</td><td class="num">${esc(f.release_date || '—')}</td>
    <td><span class="code cc${f.cgiar_role || '5'}">${esc(f.cgiar_role || '5')}</span></td>`;
  $('#fishtb tbody').appendChild(tr);
});
D.fish_events.slice().sort((a, b) => (a.release_date || '9').localeCompare(b.release_date || '9')).forEach(e => {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${esc(e.strain_name || e.event_id)}</td><td>${esc((e.event_type || '').replace(/^germplasm /, '').replace(/\(.*\)/, '').replace(/\s*->\s*/g, ' to ').trim())}</td><td class="num">${esc(e.release_date || 'planned')}</td><td>${esc((e.developer || '').split('(')[0])}</td><td class="bn">${T(e.notes || '')}</td>`;
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
  const ref = a.source_url && !offline(a.source_url_status) ? link(a.source_url, clip(a.approval_reference || 'source', 90)) : T(a.approval_reference || '');
  tr.innerHTML = `<td class="num">${esc(a.approval_date || 'undated')}</td><td>${esc((a.name || '').replace(/\s*->\s*/g, ' to '))}<div class="bn"><i>${esc(a.species_scientific || '')}</i></div></td><td>${esc(TYPE[a.approval_type] || a.approval_type)}</td><td>${esc(a.approving_body || '')}</td><td>${ref}</td>`;
  $('#fishk tbody').appendChild(tr);
});

// ---------- verification tables ----------
(function () {
  const q = D.qa || {};
  (q.ocr_bands || []).forEach(b => { const tr = document.createElement('tr'); tr.innerHTML = `<td>${esc(b[0])}</td><td class="num r">${fmt(b[1])}</td><td class="num r">${fmt(b[2])}</td>`; $('#qa1 tbody').appendChild(tr); });
  const lab = {key_check: 'Matched the NSB meeting-date key', visual_check: 'Confirmed on the page image (vision-language model)', two_source: 'Two independent sources agree', text: 'Machine-readable text, HTML, API or spreadsheet', unvalidated: 'Machine-readable, single source'};
  const agg = {}; (q.by_check || []).forEach(([m, c, n]) => { const k = (m === 'ocr' && c === 'unvalidated') ? 'ocr_unvalidated' : c; agg[k] = (agg[k] || 0) + n; });
  ['key_check', 'visual_check', 'two_source', 'unvalidated', 'text', 'ocr_unvalidated'].filter(k => agg[k]).forEach(k => { const tr = document.createElement('tr');
    tr.innerHTML = `<td>${esc(k === 'ocr_unvalidated' ? 'Read by OCR, not confirmed (kept out of the register)' : lab[k])}</td><td class="num r">${fmt(agg[k])}</td>`; $('#qa2 tbody').appendChild(tr); });
  $('#qanote').textContent = `${fmt(q.evidence_rows || 0)} evidence rows from ${fmt(q.n_sources || 0)} source files; ${fmt(q.n_conflicts || 0)} disagreeing values kept in the conflicts file. Mean OCR word confidence across ${fmt(q.ocr_pages || 0)} scanned pages: ${q.ocr_mean_conf ?? '–'}.`;
})();

// ---------- completeness and disagreements ----------
(function () {
  const inb = inbreds, hyb = R.filter(r => r.rice_type === 'hybrid');
  const F = [['Exact date of the approving meeting', r => (r.approval_date || '').length === 10], ['NSB meeting reference', r => /NSB \d/.test(r.approval_reference || '')],
    ['Gazette notification date', r => r.gazette_date], ['Breeding line', r => r.breeding_line], ['Pedigree', r => r.pedigree],
    ['Known CGIAR link (codes 1 to 4)', r => r.cgiar_role && r.cgiar_role !== '5'], ['Season', r => r.season_std || r.season],
    ['Duration', r => r.duration_min_days || r.duration_days], ['Yield', r => r.yield_t_ha], ['Ecosystem', r => r.ecosystem_std || r.ecosystem],
    ['Grain class', r => r.grain_class], ['Recommended region', r => r.recommended_region || r.region_scope], ['Any trait description', r => r.trait_text_available === 'yes'],
    ['At least one stated trait', r => r.feature_tags], ['Key paper', r => r.key_papers], ['Code in a household survey', r => r.survey_codes]];
  const cell = (rows, f) => { const n = rows.filter(f).length; return `${n} <span class="bn">(${pct(n, rows.length)})</span>`; };
  $('#compl tbody').innerHTML = F.map(([k, f]) => `<tr><td>${k}</td><td class="num r">${cell(inb, f)}</td><td class="num r">${cell(hyb, f)}</td></tr>`).join('');
  $('#compl thead').innerHTML = `<tr><th scope="col">Field</th><th scope="col" class="r">Inbred (n=${inb.length})</th><th scope="col" class="r">Hybrid (n=${hyb.length})</th></tr>`;
  const KIND = {substantive: 'different values', compatible: 'same value stated differently', date_1_year: 'dates one year apart', date_2plus_years: 'dates two or more years apart',
    date_same_year: 'different day in the same year', later_decision: 'a later Board decision changed it', later_notification: 'a later gazette notice changed it', formatting_only: 'formatting only'};
  $('#confl tbody').innerHTML = (D.conflicts_by_field || []).slice(0, 14).map(c =>
    `<tr><td>${esc(c.field.replace(/_/g, ' '))}</td><td class="num r">${c.n}</td><td>${esc(KIND[c.top] || c.top.replace(/_/g, ' '))}</td></tr>`).join('');
})();

// ---------- surveys ----------
(function () {
  const T2 = D.crosswalk_summary || []; if (!T2.length) return;
  $('#cwtb tbody').innerHTML = T2.map(x => `<tr><td>${esc(x.label)}</td><td class="num r">${x.n}</td><td class="num r">${x.resolved}</td><td class="num r">${x.brand_family}</td>
    <td class="num r">${x.not_approved_variety}</td><td class="num r">${x.generic_label}</td><td class="num r">${x.unmatched}</td></tr>`).join('');
  const PC = D.plot_coverage || []; if (!PC.length || !$('#pctb')) return;
  const cats = [...new Set(PC.map(p => p.category))], rounds = [...new Set(PC.map(p => p.round))];
  $('#pctb thead').innerHTML = `<tr><th scope="col">Survey round</th>${cats.map(c => `<th scope="col" class="r">${esc(c.replace(/_/g, ' '))}</th>`).join('')}<th scope="col" class="r">Plots</th></tr>`;
  $('#pctb tbody').innerHTML = rounds.map(rd => { const rs = PC.filter(p => p.round === rd), n = rs.reduce((a, p) => a + (+p.n_plots || 0), 0);
    return `<tr><th scope="row">${esc(rd)}</th>${cats.map(c => { const x = rs.find(p => p.category === c); return `<td class="num r">${x ? (Math.round(+x.share * 1000) / 10) + '%' : '–'}</td>`; }).join('')}<td class="num r">${fmt(n)}</td></tr>`; }).join('');
  $('#pcwrap').hidden = false;
})();

// ---------- references ----------
(function () {
  const by = {}; (D.references || []).forEach(r => (by[r.group] = by[r.group] || []).push(r));
  let n = 0;
  $('#reflist').innerHTML = Object.entries(by).map(([g, rs]) => `<div class="refgroup">${esc(g)}</div><ol class="refs" start="${n + 1}">` + rs.map(r => { n++;
    const main = r.url && !offline(r.url_status) ? link(r.url, r.url.includes('doi.org/') ? r.url.replace('https://', '') : 'source') : '';
    const arc = r.archived_url ? (main ? ' · ' : '') + link(r.archived_url, 'archived copy') : '';
    const off = r.url && offline(r.url_status) ? ' <span class="st">original offline</span>' : r.url && r.url_status === 'unchecked' ? ' <span class="st">link not checked</span>' : '';
    return `<li>${T(r.citation)} ${main}${arc}${off}</li>`; }).join('') + '</ol>').join('');
})();

// ---------- files ----------
(D.files || []).forEach(f => { const tr = document.createElement('tr');
  const href = f.path ? f.path : (D.download_base ?? 'data/') + f.file;
  const name = D.download_base !== null ? `<a href="${esc(href)}">${esc(f.file)}</a>` : esc(f.file);
  tr.innerHTML = `<td class="mono">${name}</td><td>${esc(f.desc)}</td><td>${esc(f.unit)}</td><td class="num r">${f.rows === '' ? '' : fmt(f.rows)}</td><td class="num r">${f.cols ?? ''}</td><td class="num r">${f.mb < 0.1 ? '&lt;0.1' : f.mb}</td>`;
  $('#filetb tbody').appendChild(tr); });
})();
