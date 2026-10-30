"""Render a source-checked teaching dependency graph as SVG (Python standard library)."""
import html, textwrap, json, argparse
from pathlib import Path
E=lambda s:html.escape(str(s),quote=True)

def validate_graph(g):
    nodes={n['id']:n for n in g['nodes']}
    assert len(nodes)==len(g['nodes']), 'Duplicate node ID'
    assert nodes and g['edges'], 'Graph is empty'
    assert len({(n['row'],n['col']) for n in nodes.values()})==len(nodes), 'Node collision'
    for n in nodes.values():
        assert n['row']>=0 and n['col']>=0 and n['kind'] in ('input','process','output')
        assert len(n['label'])<=33, 'Keep schematic labels short'
    used=set()
    for edge in g['edges']:
        assert edge['from'] in nodes and edge['to'] in nodes, 'Missing edge endpoint'
        used.update([edge['from'],edge['to']])
    assert used==set(nodes),'Disconnected node'

def diagram_svg(g,identifier='flow'):
    validate_graph(g)
    maxcol=max(n['col'] for n in g['nodes'])
    width=360+maxcol*290
    height=150+max(n['row'] for n in g['nodes'])*140
    nodes={n['id']:dict(n,x=60+n['col']*290,y=30+n['row']*140) for n in g['nodes']}
    descriptions='；'.join(nodes[e['from']]['label']+' → '+nodes[e['to']]['label'] for e in g['edges'])
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" role="img" aria-labelledby="{identifier}-title {identifier}-desc"><title id="{identifier}-title">辅助示意：方法的信息依赖关系</title><desc id="{identifier}-desc">{E(descriptions)}</desc><defs><marker id="{identifier}-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="none" stroke="#608575" stroke-width="1.5"/></marker></defs>'
    for i,e in enumerate(g['edges']):
        a,b=nodes[e['from']],nodes[e['to']]
        ax,ay=a['x']+120,a['y']+82
        bx,by=b['x']+120,b['y']
        if a['row']==b['row']:
            right=a['x']<b['x'];sx=a['x']+(240 if right else 0);ex=b['x']+(0 if right else 240)
            path=f'M{sx:g} {a["y"]+41:g}H{ex:g}'
        elif e.get('route') or b['row']-a['row']>1 or b['row']<a['row']:
            side=e.get('route', 'left' if a['col']<=maxcol/2 else 'right')
            rail=14+(i%3)*12 if side=='left' else width-14-(i%3)*12
            # Long dependencies pass in the margin, outside the node columns.
            sy=ay+18+(i%2)*7;ey=by-18-(i%2)*7
            path=f'M{ax:g} {ay:g}V{sy:g}H{rail:g}V{ey:g}H{bx:g}V{by:g}'
        else:
            mid=(ay+by)/2
            path=f'M{ax:g} {ay:g}V{mid:g}H{bx:g}V{by:g}'
        svg+=f'<path class="dependency" d="{path}" fill="none" stroke="#608575" stroke-width="2" marker-end="url(#{identifier}-arrow)"/>'
    for n in nodes.values():
        color={'input':'#f7edda','process':'#fffef9','output':'#dceadd'}[n['kind']]
        lines=textwrap.wrap(n['label'],width=11,break_long_words=True,break_on_hyphens=False)
        y0=n['y']+41-(len(lines)-1)*12+7
        svg+=f'<rect x="{n["x"]:g}" y="{n["y"]:g}" width="240" height="82" rx="9" fill="{color}" stroke="#a3bca9"/>'
        svg+='<text text-anchor="middle" font-size="20">'+''.join(f'<tspan x="{n["x"]+120:g}" y="{y0+j*24:g}">{E(t)}</tspan>' for j,t in enumerate(lines))+'</text>'
    return svg+'</svg>'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8-sig'))
    graph=data['diagram']['graph'] if 'diagram' in data else data
    svg=diagram_svg(graph)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(svg,encoding='utf8')
    print(args.output)

if __name__=='__main__':main()
