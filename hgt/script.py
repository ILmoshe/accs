import numpy as np

rows = 3601
cols = 3601

data = np.zeros((rows, cols), dtype=np.int16)
# hgt/N34E035.hgt
file_name = "N34E035.hgt"

with open(file_name, "wb") as f:
    f.write(data)
