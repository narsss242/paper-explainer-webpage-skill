"""Check a local static teaching site without requesting external URLs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import argparse
import json

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.refs=[];self.tags=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append(tag)
        if tag=='title':self.in_title=True
        if 'id' in a:self.ids.append(a['id'])
        for key in ('src','href'):
            if key in a:self.refs.append(a[key])
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,text):
        if self.in_title:self.title.append(text)

def check(root,paths,expected=None,allow_interactive=False):
    parsed={};errors=[];local_count=0;external_count=0
    if expected is not None and len(paths)!=expected:
        errors.append(f'Expected {expected} pages, found {len(paths)}')
    if not paths:errors.append('No HTML pages selected')
    for path in paths:
        try:text=path.read_text(encoding='utf-8-sig')
        except (OSError,UnicodeError) as e:errors.append(f'{path}: {e}');continue
        p=Page();p.feed(text);parsed[path]=p
        if not ''.join(p.title).strip():errors.append(f'{path}: missing title')
        if len(set(p.ids))!=len(p.ids):errors.append(f'{path}: duplicate IDs')
        if not allow_interactive and set(p.tags)&{'input','form','button','script','textarea','select'}:
            errors.append(f'{path}: contains interactive/script elements; review scope or use --allow-interactive intentionally')
    cache=dict(parsed)
    for path,p in parsed.items():
        for link in p.refs:
            u=urlsplit(link)
            if u.scheme or u.netloc:
                external_count+=1;continue
            local_count+=1
            dest=(path.parent/unquote(u.path)).resolve() if u.path else path
            if not dest.is_file():errors.append(f'{path}: missing local target {link}');continue
            if u.fragment and dest.suffix.lower() in ('.html','.htm'):
                if dest not in cache:
                    q=Page()
                    try:q.feed(dest.read_text(encoding='utf-8-sig'));cache[dest]=q
                    except (OSError,UnicodeError) as e:errors.append(f'{dest}: {e}');continue
                if unquote(u.fragment) not in cache[dest].ids:
                    errors.append(f'{path}: missing anchor {link}')
    return dict(root=str(root),pages=len(parsed),local_references_checked=local_count,
                external_references_not_requested=external_count,errors=errors)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root',type=Path)
    ap.add_argument('--pages',nargs='+',help='Explicit root-relative HTML files (default: all HTML under root)')
    ap.add_argument('--expected-pages',type=int)
    ap.add_argument('--allow-interactive',action='store_true',help='Only when the requested site intentionally includes forms or scripts')
    ap.add_argument('--report',type=Path)
    args=ap.parse_args();root=args.root.resolve()
    if not root.is_dir():ap.error(f'Not a directory: {root}')
    paths=sorted({(root/p).resolve() for p in args.pages}) if args.pages else sorted(root.rglob('*.html'))
    report=check(root,paths,args.expected_pages,args.allow_interactive)
    output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(output+'\n',encoding='utf8')
    print(output)
    raise SystemExit(1 if report['errors'] else 0)

if __name__=='__main__':main()
