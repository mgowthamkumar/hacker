a=int(input())
b=int(input())
mat=[]
for i in range(a):
    row=[]
    for j in range(b):
        row.append(int(input()))
    mat.append(row)
for i in range(a):
    for j in range(b):
        print(mat[i][j],end=" ")
    print()