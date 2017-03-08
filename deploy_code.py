import py_compile 
import compileall
import shutil
import os

src_dir = 'pretrain_scripts'
dist_dir = 'dist'

# clean
shutil.rmtree(dist_dir)
os.mkdir(dist_dir)

files = os.listdir(src_dir)
for file in files:
    filename, file_extension = os.path.splitext(file)
    if file_extension == '.pyc':
        oldfile = os.path.join(src_dir, file)
        os.remove(oldfile)

# gen pyc code
compileall.compile_dir(src_dir)

# distribute
files = os.listdir(src_dir)
for file in files:
    filename, file_extension = os.path.splitext(file)
    if file_extension != '.pyc':
		#print 'unsupport file extension', file_extension
		continue

    oldfile = os.path.join(src_dir, file)
    newfile = os.path.join(dist_dir, file)

    print('dist: %s -> %s' % (oldfile, newfile))
    shutil.copy(oldfile, newfile)

#shutil.copy('config.py', dist_dir)