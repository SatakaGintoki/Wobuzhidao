"""Independent table check and PDF page renders for the final manuscript."""
from pathlib import Path
import json,re,hashlib,argparse
import numpy as np
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'paper/guosai2026'
Q=P/'qa'

def main():
    global Q
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reading-stem',default='reading')
    parser.add_argument('--qa-dir',default='qa')
    args=parser.parse_args()
    Q=P/args.qa_dir
    Q.mkdir(exist_ok=True)
    counts={}
    for q in range(1,5):
        with np.load(ROOT/f'results/q{q}_solution.npz') as z:
            for f in (('T','C') if q<3 else ('C',)):
                text=(P/f'tables/q{q}{f}.tex').read_text(encoding='utf8')
                rows=[s for s in text.splitlines() if re.match(r'^\d',s)]
                got=[]
                for line in rows:
                    cells=line.replace('\\\\','').split('&')
                    got.append([float(x.strip()) if x.strip() not in ('','---') else np.nan for x in cells])
                got=np.asarray(got)
                if q<3:
                    times=np.array([100,300,600,900,1200,1500,1800]) if q==1 else np.arange(1800,10801,1800)
                    indices=np.searchsorted(z['times'],times)
                    expected=z[f+'_out'][indices][:,[0,5,10,15,20]]
                    t=times if q==1 else times/3600
                elif q==3:
                    expected=z['C_table'];t=z['table_hours']
                else:
                    expected=z['table_C'];t=z['table_times_s']/3600
                    ids=np.searchsorted(z['times_s'],z['table_times_s'])
                    assert np.allclose(got[:,-1],np.round(z['radius_m'][ids]*100,4))
                actual=got[:,1:1+expected.shape[1]]
                assert actual.shape==expected.shape
                assert np.array_equal(np.isnan(actual),np.isnan(expected))
                good=np.isfinite(expected)
                formatted=np.array([float(f'{x:.4f}') for x in expected[good]])
                assert np.array_equal(actual[good],formatted),(q,f)
                assert np.allclose(got[:,0],t,rtol=0,atol=1e-7)
                counts[f'q{q}{f}']=int(good.sum())
    original=json.loads((P/'qa/table_sources.json').read_text(encoding='utf8'))['source_sha256']
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in original.items())
    # Gather page statistics and render contact sheets plus full body pages.
    pdf_summary={}
    stems=['reading','main']
    if (P/'ai_details.pdf').exists():
        stems.append('ai_details')
    for stem in stems:
        file_stem=args.reading_stem if stem=='reading' else stem
        doc=pdfium.PdfDocument(str(P/f'{file_stem}.pdf'))
        thumbs=[]; stats=[]; all_text=[]
        for i in range(len(doc)):
            page=doc[i];textpage=page.get_textpage();txt=textpage.get_text_range();all_text.append(txt)
            stats.append({'page':i+1,'size_pt':list(page.get_size()),'chars':len(txt),'start':txt[:90]})
            if stem!='main' or i>=21:
                scale=1.25 if stem!='main' else .55
                im=page.render(scale=scale).to_pil().convert('RGB')
                if stem!='main':
                    im.save(Q/f'{stem}_{i+1:03}.png')
                im.thumbnail((298,423))
                tile=Image.new('RGB',(318,455),'#dfe4e8');tile.paste(im,((318-im.width)//2,8))
                ImageDraw.Draw(tile).text((12,433),f'{stem} / {i+1}',fill='black')
                thumbs.append(tile)
            textpage.close();page.close()
        stride=12 if stem=='main' else 6
        cols=4 if stem=='main' else 3
        for start in range(0,len(thumbs),stride):
            pack=thumbs[start:start+stride];sheet=Image.new('RGB',(cols*318,((len(pack)+cols-1)//cols)*455),'white')
            for j,im in enumerate(pack):sheet.paste(im,((j%cols)*318,(j//cols)*455))
            sheet.save(Q/f'{stem}_contact_{start//stride+1}.png')
        full='\n'.join(all_text)
        assert 'chens' not in full.lower(),(stem,'identity leak')
        assert '??' not in full,(stem,'unresolved reference')
        assert all(s['chars']>10 for s in stats),(stem,'blank page')
        (Q/f'{stem}_text.txt').write_text(full,encoding='utf8')
        pdf_summary[stem]={'pages':len(doc),'bytes':(P/f'{file_stem}.pdf').stat().st_size,'page_stats':stats}
        doc.close()
    assert pdf_summary['reading']['pages']-1<=30
    for f in ['reading','main']:
        file_stem=args.reading_stem if f=='reading' else f
        log=(P/f'{file_stem}.log').read_text(encoding='utf8',errors='replace')
        assert 'Overfull' not in log
        assert 'undefined references' not in log
        assert 'Missing character' not in log
    out={'table_cells':counts,'total_cells':sum(counts.values()),'source_hashes_unchanged':True,'pdfs':pdf_summary}
    (Q/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'table_cells':counts,'pdfs':{k:{'pages':v['pages'],'bytes':v['bytes']} for k,v in pdf_summary.items()}}))

if __name__=='__main__':main()
