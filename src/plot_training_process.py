import os
import matplotlib.pyplot as plt

iterations = []
acc = []
with open('./sanxia_2014/segnet_train_log.txt') as f:
    count = 0
    for line in f:
        items = line.strip().split()
        if len(items) > 5 and items[4] == 'Iteration' and items[6] == 'loss':
            print('iteration', items[5].split(',')[0])
            iterations.append(int(items[5].split(',')[0]))

            count = count + 1
        if len(items) > 10 and items[4] == 'Train' and items[5] == 'net' and items[6] == 'output' and items[7] == '#0:' and items[8] == 'accuracy' and items[9] == '=':
            print('acc', items[10])
            acc.append(float(items[10]))

            count = count + 1
        

if (len(iterations) != len(acc)):
    print(len(iterations), len(acc))
    print('not consistent!!')
    #exit()


with open('plot.csv', 'w')as f:
    f.write('#iter,accuracy\n')

    for i in range(len(iterations)):
        f.write('%s,%s\n' % (iterations[i], acc[i]))
f.close()

plt.figure(1)
plt.plot(iterations, acc)
plt.savefig('plot.png')