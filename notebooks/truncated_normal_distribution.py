import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm


def sample(i):
    a = norm.cdf(0, loc=0.9, scale=0.5)
    b = norm.cdf(1, loc=0.9, scale=0.5)
    u = np.random.uniform(low=a, high=b)
    result = norm.ppf(u, loc=0.9, scale=0.5)
    if i == 1:
        print(result)
    return result


data = [sample(i) for i in range(0, 5000)]
plt.hist(data, bins=100)
plt.show()
plt.close()
