import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys

iterations = []
acc = []
loss = []
class_index = 0
if len(sys.argv) > 2:
    class_index = int(sys.argv[2])

with open(sys.argv[1]) as f:
    count = 0
    for line in f:
        items = line.strip().split()
        hasx = False
        hasacc = False
        hasloss = False
        if len(items) > 5 and items[4] == 'Iteration' and items[6] == 'loss':
            print('iteration', items[5].split(',')[0])
            iterations.append(int(items[5].split(',')[0]))
	    hasx = True
            count = count + 1

        if len(items) > 10 and items[4] == 'Train' and items[5] == 'net' and items[6] == 'output' and items[7] == ('#%d:' % class_index) and items[9] == '=':
            print('acc', items[10])
            acc.append(float(items[10]))
            hasacc = True
        
        if len(items) > 10 and items[4] == 'Train' and items[5] == 'net' and items[6] == 'output' and items[7] == '#1:' and items[8] == 'loss' and items[9] == '=':
            print('loss', items[10])
            loss.append(float(items[10]))
            hasloss = True
            count = count + 1
        

if (len(iterations) != len(acc)):
    print(len(iterations), len(acc))
    print('not consistent!!')
    if len(iterations) > len(acc):
	iterations.pop()
    else:
	acc.pop()
	
if (len(iterations) != len(loss)):
    print(len(iterations), len(loss))
    print('not consistent!!')
    if len(iterations) > len(loss):
        iterations.pop()
    else:
        loss.pop()

plt.figure(1)
plt.plot(iterations, acc)
plt.savefig('plot_acc_%d.png' % (class_index))

plt.figure(2)
plt.plot(iterations, loss)
plt.savefig('plot_loss.png')
