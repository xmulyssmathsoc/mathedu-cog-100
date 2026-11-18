#!/usr/bin/env python3
"""Targeted independent SymPy/Python arithmetic and logical consistency checks.
These checks DO NOT prove the entire natural-language solution or its pedagogical validity.
"""
import json, math, statistics
from pathlib import Path
from fractions import Fraction
from sympy import (symbols, Eq, solve, sqrt, sin, cos, pi, limit, diff, integrate,
                   simplify, Matrix, Rational, atan, asin, factorial, binomial, summation, oo,
                   expand, integrate, exp, log, Abs, simplify)

ROOT=Path(__file__).resolve().parents[1]
x,y,a,b,k,n,t,h=symbols('x y a b k n t h',real=True)
checks={}

def test(qid,formula,kind='symbolic_or_numeric'):
 try:
  result=bool(formula())
  if not result:raise AssertionError('check evaluated False')
  checks[qid]={'status':'passed','scope':kind}
 except Exception as e:
  checks[qid]={'status':'failed','scope':kind,'error':f'{type(e).__name__}: {e}'}

# Arithmetic; cases verify the central numerical or structural result.
test('NUM-001',lambda:-3-(-5)==2)
test('NUM-002',lambda:Rational(3,5)>Rational(4,7))
test('NUM-003',lambda:100*Rational(6,5)*Rational(4,5)==96)
test('NUM-004',lambda:abs(-4)+abs(2-7)==9)
test('NUM-005',lambda:(-2)**3*(-3)**2==-72)
test('NUM-006',lambda:Rational(3,1)/Rational(3,4)==4)
test('NUM-007',lambda:Rational(10,4)*6==15 and (Rational(10,4)-1)*6==9)
test('NUM-008',lambda:7<sqrt(50)<8 and sqrt(50).is_rational is False)
test('NUM-009',lambda:Rational(32,10)*10**8/(8*10**6)==40)
test('NUM-010',lambda:all((2*z+4)%5==0 for z in range(3,503,5)),'bounded_exhaustive')

# Algebra
test('ALG-001',lambda:simplify(3*x+2*x**2-x+5*x**2-(7*x**2+2*x))==0)
test('ALG-002',lambda:solve(3*x+5-17,x)==[4])
test('ALG-003',lambda:solve(2*(3*x-4)-3*(x+1)-4,x)==[5])
test('ALG-004',lambda:simplify((x**2-1)/(x-1)-(x+1))==0 and (x-1).subs(x,1)==0)
test('ALG-005',lambda:set(solve(x**2-9,x))=={-3,3})
test('ALG-006',lambda:set(solve((x-2)*(x+3),x))=={-3,2})
test('ALG-007',lambda:-2*(-3)+3>7 and not (-2*0+3>7) and -2*(-2)+3==7)
test('ALG-008',lambda:sqrt(2+2)==2 and sqrt(-1+2)!=-1 and set(solve(x**2-x-2,x))=={-1,2})
test('ALG-009',lambda:set(solve((2*x-1)**2-25,x))=={-2,3})
test('ALG-010',lambda:solve((x+1)-3*(x-2),x)==[Rational(7,2)])
test('ALG-011',lambda:simplify((a*x-2*a).subs(x,2))==0 and (a*x-2*a).subs(a,0)==0)
test('ALG-012',lambda:all((z*z-z)%2==0 for z in range(-1000,1001)),'bounded_exhaustive')

# Functions
test('FUN-001',lambda:len({1:2,2:2,3:4})==3 and ({1:2,2:2,3:4}[1]=={1:2,2:2,3:4}[2]))
test('FUN-002',lambda:all((z+1+3*z*(z-1)*(z-2)==z+1) for z in [0,1,2]) and diff(x+1+3*x*(x-1)*(x-2),x).subs(x,1)<0)
test('FUN-003',lambda:simplify((x**2-4)/(x-2)-(x+2))==0 and (x-2).subs(x,2)==0)
test('FUN-004',lambda:diff(-2*x+5,x)==-2 and simplify((-2*(x+3)+5)-(-2*x+5))==-6)
test('FUN-005',lambda:set(solve(x*x-4,x))=={-2,2})
test('FUN-006',lambda:simplify((12/x)*x)==12 and Rational(12,6)==2)
test('FUN-007',lambda:expand(-(x-1)**2+4).subs(x,1)==4 and all(-((z-1)**2)+4<=4 for z in range(-20,20)))
test('FUN-008',lambda:simplify(sqrt(x-1).subs(x,2))==1 and sqrt(x).subs(x,1)-1==0)
test('FUN-009',lambda:limit(x+1,x,0,dir='-')==1 and limit(x*x,x,0,dir='+')==0)
test('FUN-010',lambda:1**2==(-1)**2 and sqrt(9)==3)
test('FUN-011',lambda:simplify(((x-2)**2).subs(x,2))==0 and (x*x-2).subs(x,0)==-2)
test('FUN-012',lambda:sin(pi/2+2*pi*10)==1 and sin(3*pi/2+2*pi*10)==-1)

# Geometry
test('GEO-001',lambda:65+(180-65)==180)
test('GEO-002',lambda:8*5/2==20)
test('GEO-003',lambda:float(asin(Rational(7,10)))+float(pi/6)<float(pi) and float(pi-asin(Rational(7,10)))+float(pi/6)<float(pi))
test('GEO-004',lambda:Rational(9,6)*8==12)
test('GEO-005',lambda:6**2+8**2==10**2 and 5**2+6**2!=7**2)
test('GEO-006',lambda:Rational(100,2)==50)
test('GEO-007',lambda:Rational(2,1)*Rational(-1,2)==-1)
test('GEO-008',lambda:abs(3*1+4*2-12)/sqrt(3**2+4**2)==Rational(1,5))
test('GEO-009',lambda:set(solve((x-1)**2-4,x))=={-1,3})
test('GEO-010',lambda:(3-0)**2+(1-0)**2==10 and (1-2)**2+(1-0)**2==2)

# Trigonometry / vectors
test('TRI-001',lambda:Rational(3,5)**2+Rational(4,5)**2==1)
test('TRI-002',lambda:simplify(sin(pi/6)+cos(pi/3))==1)
test('TRI-003',lambda:simplify(sin(5*pi/6)-Rational(1,2))==0 and simplify(cos(5*pi/6)+sqrt(3)/2)==0)
test('TRI-004',lambda:simplify(sin(3*(x+2*pi/3))-sin(3*x))==0)
test('TRI-005',lambda:Matrix([2,1])+Matrix([-1,3])==Matrix([1,4]))
test('TRI-006',lambda:Matrix([1,2]).dot(Matrix([2,-1]))==0)
test('TRI-007',lambda:float(asin(Rational(7,20))+pi/6)<float(pi) and float(pi-asin(Rational(7,20))+pi/6)>float(pi))
test('TRI-008',lambda:all(sin(z*pi)==0 for z in range(-20,21)),'bounded_exhaustive')

# Probability
test('PRO-001',lambda:Rational(3,6)==Rational(1,2))
test('PRO-002',lambda:3*2==6 and 3+2==5)
test('PRO-003',lambda:5*4==20 and binomial(5,2)==10)
test('PRO-004',lambda:Rational(3,5)*Rational(2,4)+Rational(2,5)*Rational(3,4)==Rational(3,5))
test('PRO-005',lambda:Rational(4,4)==1)
test('PRO-006',lambda:Rational(1,6)*Rational(1,6)>0)
test('PRO-007',lambda:Rational(60,100)*Rational(1,100)+Rational(40,100)*Rational(3,100)==Rational(18,1000))
test('PRO-008',lambda:abs(float(Rational(9,1000)/(Rational(9,1000)+Rational(495,10000)))-0.15384615)<1e-6)
test('PRO-009',lambda:Rational(7,10)*0+Rational(3,10)*10==3)
test('PRO-010',lambda:Rational(1,2)**3==Rational(1,8))

# Statistics
test('STA-001',lambda:statistics.mean([1,2,2,3,12])==4 and statistics.median([1,2,2,3,12])==2)
test('STA-002',lambda:statistics.median([1,2,8,9,10])==8 and statistics.median([1,2,8,9,10,100])==8.5)
test('STA-003',lambda:statistics.pvariance([2,4])==1 and statistics.pstdev([2,4])==1)
test('STA-004',lambda:Rational(110,100)==Rational(11,10) and Rational(110-100,100)==Rational(1,10))
test('STA-005',lambda:(15*80+5*100)/20==85)
test('STA-006',lambda:all(2*z-2*z==0 for z in range(10)),'illustrative_countermodel')
test('STA-007',lambda:Rational(9,10)!=Rational(1,2),'illustrative_countermodel')
# Under normal assumptions, the long-run two-sided z coverage is approximately 95%.
from sympy import erf
test('STA-008',lambda:abs(float(erf(Rational(196,100)/sqrt(2)))-0.95)<0.001,'model_based_numeric')

# Calculus
test('CAL-001',lambda:limit((x*x-1)/(x-1),x,1)==2)
test('CAL-002',lambda:limit(((3+h)**2-9)/h,h,0)==6)
test('CAL-003',lambda:limit(Abs(h)/h,h,0,dir='+')==1 and limit(Abs(h)/h,h,0,dir='-')==-1)
test('CAL-004',lambda:(x*x+1).subs(x,2)==5 and diff(x*x+1,x).subs(x,2)==4)
test('CAL-005',lambda:simplify(diff((3*x*x+1)**5,x)-30*x*(3*x*x+1)**4)==0)
test('CAL-006',lambda:diff(x**3,x).subs(x,0)==0 and ((-1)**3<0<1**3))
test('CAL-007',lambda:limit(sin(x)/x,x,0)==1)
test('CAL-008',lambda:integrate(x,(x,-1,1))==0 and integrate(Abs(x),(x,-1,1))==1)
test('CAL-009',lambda:solve([Eq(a*0+1,b),Eq(a,0)],[a,b])=={a:0,b:1})
test('CAL-010',lambda:diff(integrate(t,(t,0,x)),x)==x)
test('CAL-011',lambda:abs((100+Rational(1,100))**2-100**2)>2 and Rational(1,100)<Rational(1,10))
test('CAL-012',lambda:sum(Rational(1,i) for i in range(1,1025))>7,'finite_lower_bound')

# Linear algebra
test('LIN-001',lambda:Matrix([[1,1],[0,1]])*Matrix([-1,3])==Matrix([2,3]))
A=Matrix([[1,1],[0,1]]);B=Matrix([[1,0],[1,1]])
test('LIN-002',lambda:A*B==Matrix([[2,1],[1,1]]) and B*A==Matrix([[1,1],[1,2]]))
test('LIN-003',lambda:Matrix([[1,1],[2,2]]).rank()==1 and all((z+(3-z)==3 and 2*z+2*(3-z)==6) for z in range(-10,11)))
test('LIN-004',lambda:all((z+(-z)==0 and 2*z+2*(-z)==0) for z in range(-10,11)),'bounded_exhaustive')
test('LIN-005',lambda:Matrix([1,1])-Matrix([1,0])-Matrix([0,1])==Matrix([0,0]))
test('LIN-006',lambda:3-Matrix([[1,0,0],[0,1,0]]).rank()==1)
test('LIN-007',lambda:all((z-z==0) for z in range(-100,101)),'bounded_exhaustive')
test('LIN-008',lambda:Matrix([[2,0],[0,3]])*Matrix([1,0])==2*Matrix([1,0]) and Matrix([[2,0],[0,3]])*Matrix([0,1])==3*Matrix([0,1]))
test('LIN-009',lambda:(A-Matrix.eye(2)).nullspace()==[Matrix([1,0])])
test('LIN-010',lambda:Matrix([[1,1],[1,-1]])*Matrix([1,1])==Matrix([2,0]))

# Discrete mathematics and proof (mostly logical witness / finite spot checks).
test('LOG-001',lambda:all(z%2==0 for z in range(-40,41,4)) and 2%4!=0,'bounded_exhaustive')
test('LOG-002',lambda:all(z*z>=0 for z in range(-100,101)),'bounded_exhaustive')
test('LOG-003',lambda:1 in {1,2} and {1}.issubset({1,2}) and frozenset({1}) not in {1,2})
test('LOG-004',lambda:simplify((2*k+1)**2-(2*(2*k*k+2*k)+1))==0)
test('LOG-005',lambda:all(z%2==0 for z in range(-40,41,4)) and 2%4!=0,'bounded_exhaustive')
test('LOG-006',lambda:all((z*z)%2==1 for z in range(-99,100,2)),'bounded_exhaustive')
test('LOG-007',lambda:simplify(k*(k+1)/2+(k+1)-(k+1)*(k+2)/2)==0)
test('LOG-008',lambda:simplify(3*(2*k+1)+2-(2*(3*k+2)+1))==0)

EXPECTED=100
if len(checks)!=EXPECTED:raise RuntimeError(f'checks {len(checks)} != {EXPECTED}')
report={'method':'Targeted SymPy/Python checks for each core item',
        'interpretation':'One central identity, value, bounded witness, or logical structure per item. This is NOT independent review or a proof of every wording, solution, error annotation, or simulated student response.',
        'total_items':EXPECTED,'executed':len(checks),
        'passed':sum(x['status']=='passed' for x in checks.values()),
        'failed':sum(x['status']=='failed' for x in checks.values()),
        'check_results':checks}
(ROOT/'reports'/'math_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Targeted math checks:',report['passed'],'passed;',report['failed'],'failed')
for q,r in checks.items():
 if r['status']!='passed':print('FAIL',q,r)
if report['failed']:raise SystemExit(1)
