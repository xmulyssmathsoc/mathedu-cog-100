#!/usr/bin/env python3
"""30 executable *targeted* mathematical checks for supplemental illustrative cases.
Not an audit of all natural-language explanations or teaching hypotheses.
"""
import json, math
from fractions import Fraction as F
from pathlib import Path
import sympy as s
ROOT=Path(__file__).resolve().parents[1]
x,k,h=s.symbols('x k h',real=True)
pi=s.pi

def near(a,b,tol=1e-8):return abs(float(a-b))<tol

def check01():return 100*F(6,5)*F(4,5)==96 and 200*F(11,10)*F(9,10)==198 and 80*F(3,4)*F(5,4)==75

def check02():return s.sqrt(50).is_rational is False and s.sqrt(72).is_rational is False and s.sqrt(81)==9

def check03():return s.simplify((2*(5*k+3)+4)/5-(2*k+2))==0 and s.simplify((3*(4*k+3)+3)/4-(3*k+3))==0

def check04():return s.cancel((x*x-1)/(x-1))==x+1 and s.denom((x*x-1)/(x-1)).subs(x,1)==0

def check05():return s.solve_univariate_inequality(-2*x+3>7,x).as_set()==s.Interval.open(-s.oo,-2) and s.solve_univariate_inequality(-3*x+2<=11,x).as_set()==s.Interval(-3,s.oo)

def check06():return s.solveset(s.sqrt(x+2)-x,x,domain=s.S.Reals)==s.FiniteSet(2) and s.solveset(s.sqrt(x+12)-x,x,domain=s.S.Reals)==s.FiniteSet(4)

def check07():return s.simplify((x*x-4)/(x-2)-(x+2))==0 and (x-2).subs(x,2)==0

def check08():return s.sqrt((x-1))==s.sqrt(x-1) and s.sqrt(0)-1==-1 and s.simplify(1/(x+2)-1/(x+2))==0

def check09():return s.limit(x+1,x,0,dir='-')==1 and s.limit(x*x,x,0,dir='+')==0 and s.limit(x+2,x,0,dir='-')==s.limit(x*x+2,x,0,dir='+')==2

def check10():return F(1,2)*8*5==20 and F(1,2)*10*6==30

def check11():
 b=math.degrees(math.asin(.7))
 b2=180-b
 t=math.degrees(math.asin(2/3))
 return near(b,44.427004,1e-5) and 30+b2<180 and 30+180-t<180

def check12():return F(abs(3*1+4*2-12),5)==F(1,5) and F(abs(3*(-1)+0-12),5)==3

def check13():return s.simplify(s.sin(5*pi/6)-s.Rational(1,2))==0 and s.simplify(s.cos(5*pi/6)+s.sqrt(3)/2)==0 and s.simplify(s.sin(7*pi/6)+s.Rational(1,2))==0

def check14():return s.simplify(s.sin(3*(x+2*pi/3))-s.sin(3*x))==0 and s.simplify(s.sin((x+4*pi)/2)-s.sin(x/2))==0

def check15():
 b=math.degrees(math.asin(.35));bt=math.degrees(math.asin(5/7))
 return 30+(180-b)>180 and 30+b<180 and 30+(180-bt)<180 and near(bt,45.58469,1e-4)

def check16():return 5*4==20 and math.comb(5,2)==10 and 6*5==30 and math.comb(6,2)==15

def check17():return F(1,6)*F(1,6)!=0 and F(3,6)*F(2,6)==F(1,6)

def check18():return F(90,90+495)==F(2,13) and F(9,100)/ (F(9,100)+F(9,100))==F(1,2)

def check19():
 a=[1,2,2,3,12];b=[5,5,6,6,48]
 return sum(a)/5==4 and sorted(a)[2]==2 and sum(b)/5==14 and sorted(b)[2]==6 and F(1+2+2+3+120,5)==F(128,5)

def check20():
 # Structural counterexample to interpreting correlation as causal:
 # common exogenous H determines X and Y; no X->Y arrow is assumed.
 H=[0,0,1,1];X=H[:];Y=H[:]
 avg=sum(X)/len(X);cov=sum((a-avg)*(b-avg) for a,b in zip(X,Y))
 return cov>0 and X==Y

def check21():
 # Illustrates that a fixed parameter is either covered or not by each realized interval.
 mu=1;intervals=[(0,2),(2,3)]
 covers=[a<=mu<=b for a,b in intervals]
 return covers==[True,False]

def check22():return s.limit(s.Abs(h)/h,h,0,dir='+')==1 and s.limit(s.Abs(h)/h,h,0,dir='-')==-1 and s.limit(s.Abs(h),h,0)==0

def check23():return s.diff(x**3,x).subs(x,0)==0 and (-F(1,10))**3<0<F(1,10)**3 and s.diff(x**4,x).subs(x,0)==0

def check24():
 n=s.symbols('n',integer=True,positive=True)
 return (s.summation(1/n,(n,1,s.oo))==s.oo and
         sum(F(1,j) for j in range(8,16))>=F(1,2) and
         all(1/math.sqrt(j)>=1/j for j in range(1,101)))

def check25():
 A=s.Matrix([[1,1],[0,1]]);B=s.Matrix([[1,0],[1,1]])
 C=s.Matrix([[1,0],[0,2]]);D=s.Matrix([[0,1],[0,0]])
 return A*B==s.Matrix([[2,1],[1,1]]) and B*A==s.Matrix([[1,1],[1,2]]) and C*D!=D*C

def check26():
 M=s.Matrix([[1,0,1],[0,1,1]])
 return M.rank()==2 and M*s.Matrix([-1,-1,1])==s.zeros(2,1)

def check27():
 A=s.Matrix([[1,1],[0,1]]);V=(A-s.eye(2)).nullspace()
 return len(V)==1 and not A.is_diagonalizable() and s.eye(2).is_diagonalizable()

def check28():return 6%2==0 and 6%4!=0 and 3%3==0 and 3%6!=0

def check29():return s.reduce_inequalities([x**2<0],x)==s.false and s.reduce_inequalities([x**2>=0],x)==s.true

def check30():return s.simplify(k*(k+1)/2+(k+1)-(k+1)*(k+2)/2)==0 and s.simplify(k*k+(2*k+1)-(k+1)**2)==0

NAMES={
 1:'percentage_compounded_baseline',2:'rationality_approximation',3:'remainder_reduction',
 4:'rational_expression_domain',5:'negative_inequality',6:'squaring_extraneous_root',
 7:'function_domain_difference',8:'composition_order_domain',9:'one_sided_continuity',
 10:'triangle_altitude',11:'ssa_ambiguity',12:'point_line_distance',
 13:'trigonometric_quadrant_sign',14:'trigonometric_period',15:'ssa_angle_constraints',
 16:'ordered_vs_unordered_selections',17:'mutual_exclusivity_vs_independence',18:'bayes_base_rates',
 19:'median_mean_outlier',20:'confounded_correlation_counterexample',21:'interval_coverage_logic',
 22:'continuous_not_differentiable',23:'stationary_point_not_extremum',24:'harmonic_series_divergence',
 25:'matrix_product_noncommutativity',26:'vector_dependence',27:'diagonalizability',
 28:'converse_counterexample',29:'quantifier_negation',30:'induction_step_identity'}

def main():
 results=[]
 for n in range(1,31):
  try:passed=bool(globals()[f'check{n:02d}']());message=''
  except Exception as e:passed=False;message=f'{type(e).__name__}: {e}'
  results.append({'case_id':f'EC-{n:03d}','check_name':NAMES[n],'passed':passed,'error':message})
 report={'total':len(results),'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),
  'scope':'one or more executable key mathematical assertions for each case; not an independent review of complete written solutions or real student errors',
  'checks':results}
 p=ROOT/'reports'/'30道错误案例数学校验.json'
 p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Targeted case checks:',report['passed'],'/',report['total'])
 for r in results:
  if not r['passed']:print('FAIL',r)
 if report['failed']:raise SystemExit(1)

if __name__=='__main__':main()
