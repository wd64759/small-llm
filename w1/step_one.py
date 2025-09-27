import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
num_points = 100

x0 = np.random.randn(num_points, 2) + np.array([2, 2])
y0 = np.zeros((num_points,1))

x1 = np.random.randn(num_points, 2) + np.array([6, 6])
y1 = np.ones((num_points,1))

x = np.vstack((x0, x1))
y = np.vstack((y0, y1))

plt.scatter(x[:,0], x[:,1], c=y.ravel())
plt.show()

