a = [4, 22, 42, 50]
b = [[2],[6, 11],[14],[]]
d = []

for i, j in enumerate(a):
    # 如果b[i]为空,则直接拿a的值
    if not b[i]:
        d.append(j)
    elif i == 0:
        d = d+b[0]

    else:
        # 如果b[i]不为空，则进行偏移
        for y in b[i]:
            d.append(a[i-1] + y+1)

print(d)