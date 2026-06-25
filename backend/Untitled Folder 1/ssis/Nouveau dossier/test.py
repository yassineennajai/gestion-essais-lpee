import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as p 
d = np.array([1,2,3,4,5,6,7,8,9,10])
y = np.array([10,9,8,7,6,5,4,3,2,1])

df = p.DataFrame({
    "d": d,
    "y": y
})
# حساب مصفوفة الارتباط
corr = df.corr()

# رسم الخريطة الحرارية
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
plt.show()

