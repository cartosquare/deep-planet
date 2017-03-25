# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = pyi_crypto.PyiBlockCipher(key='snoopyxu19910319')


a = Analysis(['../src/pretrain.py'],
             pathex=['/home/atlasxu/workspace/deep-planet'],
             binaries=[],
             datas=[('/usr/bin/gdaladdo', '.'), ('/usr/bin/gdalbuildvrt', '.'), ('/usr/bin/gdal_translate', '.'), ('/usr/bin/gdalwarp', '.')] + collect_data_files("skimage.io._plugins"),
             hiddenimports=collect_submodules('skimage.io._plugins'),
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='pretrain',
          debug=False,
          strip=False,
          upx=True,
          console=True )
