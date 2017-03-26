# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = pyi_crypto.PyiBlockCipher(key='snoopyxu19910319')


a = Analysis(['../src/delete_project.py'],
             pathex=['/home/atlasxu/workspace/deep-planet'],
             binaries=[],
             datas=[],
             hiddenimports=[],
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
          name='delete_project',
          debug=False,
          strip=False,
          upx=True,
          console=True )
