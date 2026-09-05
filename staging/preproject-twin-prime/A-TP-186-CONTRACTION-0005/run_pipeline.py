#!/usr/bin/env python3
"""Build the native helper, reconstruct missing inputs, and run a fresh certificate.

Example: python3 -B run_pipeline.py --output fresh-run
Prerequisites: Python 3.10+, a C++17 compiler, GMP development headers/library.
No network access. No existing numerical run directory is overwritten.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,time,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PRED=ROOT/'predecessors'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
    if not x:raise ValueError(m)
def python_command():return [sys.executable]+(['-O'] if sys.flags.optimize else [])+['-B']

def prepare():
    """Rebuild the exact frozen seed and marginal arrays only when absent."""
    sys.path.insert(0,str(PRED));from fractions import Fraction as F
    import low_kernel as lk
    seed=PRED/'seed-enclosures.bin.zlib'
    if not seed.exists():
        x=json.loads((PRED/'source-row.json').read_text());bits=x['precision_bits']
        d=lk.seed_cells(x['first_index'],x['cells'],F(x['h'])*x['slope'],bits)
        width=(bits+7)//8+1;header=struct.pack('>8sIII',b'TPSEED03',bits,x['cells'],width)
        co=zlib.compressobj(level=6)
        with seed.open('xb') as f:
            f.write(co.compress(header))
            for a,b in zip(d['seed_lower'],d['seed_upper']):f.write(co.compress(a.to_bytes(width,'big')+b.to_bytes(width,'big')))
            f.write(co.flush())
    require(sha(seed)=='7d4ca048cd34981def5e16c8d0ce0af366b8b2154a7b9c53aa1932ba6aed7a1c','seed bytes differ from frozen input')
    arrays=PRED/'arrays'
    if not arrays.exists():
        subprocess.run(python_command()+[str(PRED/'run_marginals.py'),'--output-dir',str(arrays)],check=True)
    gp=arrays/'generation.json'
    require(sha(gp)=='6806eb35348db6792d3ebdcab5a0d0159123790aef013c418242e4ac7002e115','incomplete or changed marginal generation')
    g=json.loads(gp.read_text())
    for row in g['columns']+g['caps']:require(sha(arrays/row['file'])==row['sha256'],'changed marginal data '+row['file'])

def scientific_result(r):
    return {k:v for k,v in r.items() if k not in ['seconds','convolution_counts']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--compare',type=Path)
    args=ap.parse_args();require(not args.output.exists(),'fresh output path required')
    compiler=shutil.which('g++');require(compiler,'g++ not available')
    subprocess.run([compiler,'-O3','-std=c++17','-shared','-fPIC',str(ROOT/'packed_gmp.cpp'),'-lgmp','-o',str(ROOT/'packed_gmp.so')],check=True)
    prepare();args.output.mkdir(parents=True);start=time.monotonic()
    checks=subprocess.run(python_command()+[str(ROOT/'test_contraction.py')],text=True,capture_output=True,check=True)
    (args.output/'tests.json').write_text(checks.stdout)
    for script,extra in [('kernel_stage.py',[]),('contract_stage.py',['--kernel',str(args.output/'kernel')])]:
        stage='kernel' if script.startswith('kernel') else 'contraction'
        with (args.output/(stage+'.log')).open('w') as log:
            subprocess.run(python_command()+[str(ROOT/script)]+extra+['--output',str(args.output/stage)],stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((args.output/'contraction'/'result.json').read_text());same=None
    if args.compare:
        old=json.loads((args.compare/'result.json').read_text())
        require(scientific_result(result)==scientific_result(old),'scientific result differs on replay')
        same=True
    (args.output/'execution.json').write_text(json.dumps(dict(completed=True,elapsed_seconds=time.monotonic()-start,python=sys.version,optimize=sys.flags.optimize,scientific_replay_equal=same,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in ROOT.glob('*.py')}),indent=2)+'\n')
    print(json.dumps(dict(completed=True,root_11=result['root_11_certified'],face_10=result['face_10_certified'],scientific_replay_equal=same,output=str(args.output)),indent=2))
if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print('FAIL:',e,file=sys.stderr);raise SystemExit(1)
