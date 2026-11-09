import re,html,sys
def txt(f):
    t=open(f,encoding='utf-8',errors='replace').read()
    m=re.search(r'<main.*?</main>',t,flags=re.S); t=m.group(0) if m else t
    t=re.sub(r'<script.*?</script>|<style.*?</style>|<nav.*?</nav>','',t,flags=re.S)
    t=re.sub(r'</(tr|p|div|li|h\d)>','\n',t); t=re.sub(r'</t[dh]>',' | ',t)
    s=html.unescape(re.sub(r'<[^>]+>',' ',t)); s=re.sub(r'[ \t]+',' ',s); s=re.sub(r'\n\s*\n+','\n',s)
    return s
if __name__=='__main__':
    for f in sys.argv[1:]: print('=====',f); print(txt(f)[:int(__import__('os').environ.get('N','4000'))])
