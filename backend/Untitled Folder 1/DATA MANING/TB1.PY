 
import math
##EX 1/1
L1=[2,5,7,9,10,5,15,2,18,49,17,4]
L2=[]
for i in range(0,12):

 L2.insert(i, L1[i]**2)
print(L2)   
##EX1/3
D={}
for i in range(0,12):
     D={L1[i]:L2[i]} 
     print(D)
 ##EX1/4
 

L1=[2,5,7,9,10,5,15,2,18,49,17,4]
L1= L1 + L2 
print(L1)
L1=[2,5,7,9,10,5,15,2,18,49,17,4]
L1.extend(L2)
print(L1)
 ##EX1/5
S1=set(L1)
print(S1)
## tous les doublons sont automatiquement supprimés et ne conservent pas l’ordre


## ex 1/6

S2 = set()
for i in S1:
    if i % 2 != 0:     
        S2.add(i)

print(S2)

# 7. 
D2=dict()
for J in D.keys():  
    if J  in S1 and J%2 != 0:
        D2.update({J:D[J]})
print("D après suppression =", D2)

# 8. 
n = len(S1)
print("Nombre d’éléments dans S1 =", n)

# 9.
D[n] = "S1"
print("D final =", D)


## ex 2

x = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6]
m = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6]

def tri_bulles(x):
    x = x.copy()  

    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            if x[i] < x[j]:  
                m = x[i]
                x[i] = x[j]
                x[j] = m

    return x 

v= tri_bulles(m)
print(v)
 
def somme(x):
    y = x[0]  
    for i in range(1, len(x)): 
        y = y + x[i]
    return y  

x = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6]
b = somme(x)
print(b)

def mean (x):
    j=somme(x)
    f=len(x)
    m=j/f
    return m

print(mean(x))
        
def median(x):
    x = sorted(x)  
    n = len(x)

    if n % 2 == 0:
        
        d = x[n // 2 +1] + x[n // 2]
        g = d / 2
    else:
        
        g = x[n // 2]

    return g



x = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6]
k = median(x)
print(k)
##2/6
def var_pop(x: list[float]) -> float:
    n = len(x)
    m = mean(x)
    return sum((xi - m)**2 for xi in x) / n
##2/7
def var_sample(x: list[float]) -> float:
    n = len(x)
    m = mean(x)
    return sum((xi - m)**2 for xi in x) / (n - 1)
 ##2/8
def std_pop(x: list[float]) -> float:
    return var_pop(x) ** 0.5
##2/9
def std_sample(x: list[float]) :
    return var_sample(x) ** 0.5
 ##exercice 3:
 ##1
def minmax_scale(x: list[float]) -> list[float]:
    xmin = min(x)
    xmax = max(x)
    if xmax == xmin:
        return [0.0] * len(x)
    x_norm = [(xi - xmin) / (xmax - xmin) for xi in x]
    return x_norm
x = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6]
x_norm = minmax_scale(x)
print("Liste normalisée :", x_norm)
print("Min =", min(x_norm), "Max =", max(x_norm))
##2:
def zscore_pop(x: list[float]) :
    n = len(x)
    if n == 0:
        return []
    mean = sum(x) / n
    variance = sum((xi - mean) ** 2 for xi in x) / n
    sigma = variance ** 0.5
    if sigma == 0:
        return [0.0] * n
    z = [(xi - mean) / sigma for xi in x]
    return z
z = zscore_pop(x)
print("Z-scores :", z)

# 
mean_z = sum(z) / len(z)
variance_z = sum((zi - mean_z) ** 2 for zi in z) / len(z)
std_z = variance_z ** 0.5

print("Moyenne des Z =", mean_z)
print("Écart-type des Z =", std_z)




def robust_iqr(x: list[float]) -> list[float]:
    
    if len(x) == 0:
        return []

    data = sorted(x)
    n = len(data)

    # Médiane Q2
    Q2 = median(data)

    # Diviser en deux moitiés
    if n % 2 == 0:
        lower_half = data[:n // 2]
        upper_half = data[n // 2:]
    else:
        lower_half = data[:n // 2]      # exclure la médiane
        upper_half = data[n // 2 + 1:]  # exclure la médiane

    # Q1 et Q3
    Q1 = median(lower_half)
    Q3 = median(upper_half)

    # Éviter la division par zéro
    if Q3 - Q1 == 0:
        return [0.0] * len(x)

    # Normalisation robuste
    r = [(xi - Q2) / (Q3 - Q1) for xi in x]
    return r
### ex 4 2

def dist_euclid(x, y):
    return math.sqrt(sum((a - b)**2 for a, b in zip(x, y)))
## ex 4/3

def dist_manhattan(x, y):
    return sum(abs(a - b) for a, b in zip(x, y))
## ex 4/4
def sim_jaccard_binary(a, b):
    inter = sum(1 for i, j in zip(a, b) if i == j == 1)
    union = sum(1 for i, j in zip(a, b) if i == 1 or j == 1)
    return inter / union if union != 0 else 0.0
##ex4/5
x1 = [5.1, 3.5, 1.4, 0.2]
x2 = [4.9, 3.0, 1.4, 0.2]
x3 = [6.2, 3.4, 5.4, 1.3]
x4 = [5.9, 3.0, 5.1, 1.4]
x5 = [4.7, 3.2, 1.6, 0.4]
X = [x1, x2, x3, x4, x5]

print("\nMatrice des distances euclidiennes (5x5) :")
D = [[round(dist_euclid(a, b), 3) for b in X] for a in X]
for row in D:
    print(row)
## ex 4/5

d_euclid = dist_euclid(x1, x2)
d_manhattan = dist_manhattan(x1, x2)

print("\nDistance Euclidienne (x1, x2):", round(d_euclid, 4))
print("Distance Manhattan  (x1, x2):", round(d_manhattan, 4))
## ex 5/1

# --- Données ---
x = [5.1, 4.9, 6.2, 5.9, 6.7, 5.0, 6.4, 7.0, 5.4, 6.9]
y = [1.4, 1.4, 4.3, 4.2, 5.6, 1.3, 4.5, 5.4, 1.7, 5.1]

# --- Moyenne ---
def mean(l):
    return sum(l) / len(l)

# --- Corrélation de Pearson ---
def pearson_corr(x, y):
    x_mean = mean(x)
    y_mean = mean(y)
    num = sum((a - x_mean)*(b - y_mean) for a,b in zip(x,y))
    den = math.sqrt(sum((a - x_mean)**2 for a in x) * sum((b - y_mean)**2 for b in y))
    return num / den

# --- Régression linéaire ---
def regression_lineaire(x, y):
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(a*b for a,b in zip(x,y))
    sum_x2 = sum(a*a for a in x)
    a = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x**2)
    b = mean(y) - a * mean(x)
    return a, b

# --- Exécution ---
r = pearson_corr(x, y)
print("Coefficient de corrélation de Pearson r =", round(r, 4))

a, b = regression_lineaire(x, y)
print(f"Pente a = {a:.4f}")
print(f"Ordonnée à l'origine b = {b:.4f}")

x0 = 6.0
y0 = a * x0 + b
print(f"Valeur prédite de y pour x0=6.0 est y0 = {y0:.4f}")

# Interprétation 
if r > 0.8:
    relation = "forte corrélation positive"
elif r > 0.5:
    relation = "corrélation modérée"
elif r > 0:
    relation = "faible corrélation positive"
elif r < -0.8:
    relation = "forte corrélation négative"
elif r < -0.5:
    relation = "corrélation modérée négative"
elif r < 0:
    relation = "faible corrélation négative"
else:
    relation = "aucune corrélation"

print("→ Interprétation :", relation)
