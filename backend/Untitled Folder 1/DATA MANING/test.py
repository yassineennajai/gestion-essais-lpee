import pandas as pd

df = pd.DataFrame({
    "ville": ["Casa", "Casa", "Rabat", "Rabat", "Casa"],
    "age": [20, 25, 30, 22, 28],
    "salaire": [3000, 3200, 4000, 3500, 3100]
})
import seaborn as sns
import matplotlib.pyplot as plt

sns.boxplot(data=df, x="ville", y="age")
plt.show()


print(df)