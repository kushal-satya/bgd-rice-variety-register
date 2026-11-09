"""One-off patch of viz_template.html: sector (public/private) x type (inbred/hybrid) encoding,
sector filter, and an 'About this register' section replacing the comparison section."""
import pathlib, re

p = pathlib.Path(__file__).resolve().parent / "viz_template.html"
s = p.read_text(encoding="utf-8")

# colour tokens: teal = public, ochre = private (validated pair); hybrids drawn hatched
s = s.replace("--s-pub:#008C84; --s-pvt:#7656C4; --s-hyb:#C2701F;", "--s-pub:#008C84; --s-pvt:#C2701F;")
s = s.replace("--s-pub:#1E9A95; --s-pvt:#9478E4; --s-hyb:#D27E28;", "--s-pub:#1E9A95; --s-pvt:#D27E28;")
s = s.replace(".sw.hatch{", ".sw.hp{background:repeating-linear-gradient(45deg,var(--s-pub) 0 2px,var(--bg) 2px 4px);outline:1px solid var(--s-pub);outline-offset:-1px}\n"
              ".sw.hv{background:repeating-linear-gradient(45deg,var(--s-pvt) 0 2px,var(--bg) 2px 4px);outline:1px solid var(--s-pvt);outline-offset:-1px}\n.sw.hatch{", 1)

# legend
s = s.replace('''        <span><i class="sw" style="background:var(--s-pub)"></i>Public inbred</span>
        <span><i class="sw" style="background:var(--s-pvt)"></i>Private or NGO inbred</span>
        <span><i class="sw" style="background:var(--s-hyb)"></i>Hybrid</span>''',
'''        <span><i class="sw" style="background:var(--s-pub)"></i>Public inbred</span>
        <span><i class="sw hp"></i>Public hybrid</span>
        <span><i class="sw" style="background:var(--s-pvt)"></i>Private inbred</span>
        <span><i class="sw hv"></i>Private hybrid</span>''')
s = s.replace("Hybrids: private companies, BADC and BRRI.",
              "Colour shows who developed the variety: public (BRRI, BINA, universities, BADC) or private (companies and NGOs such as BRAC). Hatching marks hybrids.")

# series logic
s = s.replace("const series = r => r.rice_type === 'hybrid' ? 'hyb' : (r.developer_group === 'Private or NGO inbred' ? 'pvt' : 'pub');",
              "const sector = r => /^(Private company|Private or NGO inbred)$/.test(r.developer_group) ? 'private' : 'public';\n"
              "const series = r => (sector(r) === 'public' ? 'pub_' : 'pvt_') + (r.rice_type === 'hybrid' ? 'hyb' : 'inb');")
s = s.replace("const SER = [['pub','Public inbred','var(--s-pub)'],['pvt','Private or NGO inbred','var(--s-pvt)'],['hyb','Hybrid','var(--s-hyb)']];",
              "const SER = [['pub_inb','Public inbred','var(--s-pub)','background:var(--s-pub)',''],['pub_hyb','Public hybrid','url(#hp)','','hp'],"
              "['pvt_inb','Private inbred','var(--s-pvt)','background:var(--s-pvt)',''],['pvt_hyb','Private hybrid','url(#hv)','','hv']];")
s = s.replace("years.forEach(y => cnt[y] = {pub:0,pvt:0,hyb:0});", "years.forEach(y => cnt[y] = {pub_inb:0,pub_hyb:0,pvt_inb:0,pvt_hyb:0});")
s = s.replace("const max = Math.max(...years.map(y => cnt[y].pub+cnt[y].pvt+cnt[y].hyb));",
              "const sum = c => c.pub_inb+c.pub_hyb+c.pvt_inb+c.pvt_hyb;\n  const max = Math.max(...years.map(y => sum(cnt[y])));\n"
              "  const defs = el('defs',{},svg);\n"
              "  [['hp','var(--s-pub)'],['hv','var(--s-pvt)']].forEach(([id,col]) => { const pt = el('pattern',{id,width:4,height:4,patternUnits:'userSpaceOnUse',patternTransform:'rotate(45)'},defs);\n"
              "    el('rect',{width:4,height:4,fill:'var(--bg)'},pt); el('rect',{width:2,height:4,fill:col},pt); });")
s = s.replace("let acc = 0; const c = cnt[y], tot = c.pub+c.pvt+c.hyb;", "let acc = 0; const c = cnt[y], tot = sum(c);")
s = s.replace("el('rect',{x, y:yTop+gap, width:w, height:Math.max(0,hgt-gap), fill:s[2], rx: j===segs.length-1 ? 1.5 : 0},svg); acc += v; });",
              "const rr = el('rect',{x, y:yTop+gap, width:w, height:Math.max(0,hgt-gap), fill:s[2], rx: j===segs.length-1 ? 1.5 : 0},svg);\n"
              "      if (s[4]) { rr.setAttribute('stroke', s[4]==='hp' ? 'var(--s-pub)' : 'var(--s-pvt)'); rr.setAttribute('stroke-width','0.8'); }\n      acc += v; });")
s = s.replace("`<div class=\"r\"><span class=\"k\"><i class=\"sw\" style=\"background:${s[2]}\"></i>${s[1]}</span><span>${c[s[0]]}</span></div>`",
              "`<div class=\"r\"><span class=\"k\"><i class=\"sw ${s[4]}\" style=\"${s[3]}\"></i>${s[1]}</span><span>${c[s[0]]}</span></div>`")
s = s.replace("const yt = ys(c.pub+c.pvt+c.hyb) - 4;", "const yt = ys(sum(c)) - 4;")

# sector filter in the register
s = s.replace('''    <label for="fg">Developer<select id="fg"></select></label>''',
              '''    <label for="fs">Sector<select id="fs"><option value="">All</option><option value="public">Public</option><option value="private">Private (companies, NGOs)</option></select></label>
    <label for="fg">Developer<select id="fg"></select></label>''')
s = s.replace("(!fg.value || r.developer_group===fg.value)", "(!$('#fs').value || sector(r)===$('#fs').value) && (!fg.value || r.developer_group===fg.value)")
s = s.replace("['#q','#fg','#ft','#fc'].forEach", "['#q','#fs','#fg','#ft','#fc'].forEach")
s = s.replace("<td>${esc(r.developer_group)}<div class=\"bn\">${esc(r.rice_type)}</div></td>",
              "<td>${esc(r.developer_group)}<div class=\"bn\">${sector(r)} · ${esc(r.rice_type)}</div></td>")

# replace comparison section with a plain description
i = s.index('<section id="valueadd">'); j = s.index("</section>", i) + len("</section>")
s = s[:i] + '''<section id="about">
  <h2>About this register</h2>
  <div class="defs" id="aboutlist"></div>
</section>''' + s[j:]
i = s.index("// Value add (numbers computed from the data at build time)"); j = s.index("})();", i) + len("})();")
s = s[:i] + '''// About (numbers computed from the data at build time)
(function(){
  const pub = R.filter(r => sector(r)==='public'), pvt = R.filter(r => sector(r)==='private');
  const cnt = (a, t) => a.filter(r => r.rice_type===t).length;
  const dated = R.filter(r => (r.approval_date||'').length === 10).length, gaz = R.filter(r => r.gazette_date).length;
  const cg = R.filter(r => ['1','2','3'].includes(r.cgiar_role)).length, links = R.filter(r => r.cgiar_source_urls).length;
  const items = [
    ['What it is', `Every rice variety approved for cultivation in Bangladesh, ${Math.min(...R.map(r=>+r.approval_year).filter(Boolean))}–${Math.max(...R.map(r=>+r.approval_year).filter(Boolean))}: ${R.length} varieties, plus the improved fish strains released or promoted by government and CGIAR bodies.`],
    ['Who developed them', `Public: ${pub.length} (${cnt(pub,'inbred')} inbred, ${cnt(pub,'hybrid')} hybrid) from BRRI, BINA, universities and BADC. Private: ${pvt.length} (${cnt(pvt,'inbred')} inbred, ${cnt(pvt,'hybrid')} hybrid) from seed companies and NGOs such as BRAC.`],
    ['Approval record', `${dated} varieties have the exact National Seed Board meeting date and number; ${gaz} have a Bangladesh Gazette notification date. Hybrids carry the regions they are registered for.`],
    ['CGIAR link', `${cg} varieties have a documented CGIAR line, parent, grandparent or collaboration, each with the quote and the page it comes from; ${links} link directly to CGIAR publications or records.`],
    ['Names', 'Official English and Bangla names, a uniform name for joining, popular names, and survey and market names such as Miniket, linked to DNA fingerprinting evidence.'],
    ['Sources', 'NSB minutes 1–115, SCA lists and compendium, the Ministry of Agriculture hybrid list, Bangladesh Gazette, BRRI and BINA records, CGIAR publications and databases. Every value traces to a page of an archived copy; disagreements between sources are kept, not resolved silently.']];
  $('#aboutlist').innerHTML = items.map(([h,t]) => `<div><h3>${esc(h)}</h3><p>${esc(t)}</p></div>`).join('');
})();''' + s[j:]
p.write_text(s, encoding="utf-8")
print("patched; leftover --s-hyb:", s.count("--s-hyb"), "| SER hp:", s.count("url(#hp)"))
