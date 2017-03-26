# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = pyi_crypto.PyiBlockCipher(key='snoopyxu19910319')


a = Analysis(['../src/predict.py'],
             pathex=['/home/atlasxu/workspace/deep-planet'],
             binaries=[],
             datas=collect_data_files("skimage.io._plugins"),
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
          name='predict',
          debug=False,
          strip=False,
          upx=True,
          console=True )
