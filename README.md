# depcheck-lite

**使っていない依存、宣言し忘れた依存を一発で洗い出す。** `package.json`(JavaScript / TypeScript)と `requirements.txt`(Python)に対応。Python 3.10+ の標準ライブラリのみ、単一ファイル、Node も pip も不要。

```console
$ python depcheck_lite.py
[javascript]
  unused dependencies: left-pad
  unused devDependencies: jest
  used but not declared: lodash
[python]
  unused dependencies: leftover
  used but not declared: numpy
```

## 仕組み
- **JavaScript**: `import … from`, `require()`, 動的 `import()` を `.js .jsx .ts .tsx .mjs .cjs .vue .svelte` から抽出。`scripts` や設定に名前が出てくるツール(`eslint` など)、`@types/foo`(`foo` を使っている場合)は使用中とみなします
- **Python**: `import` / `from … import` を AST ではなく正規表現で抽出し、標準ライブラリとプロジェクト内モジュールを除外。`PIL→pillow`、`yaml→pyyaml`、`cv2→opencv-python` など代表的な別名に対応
- `node_modules`、`venv`、`dist`、`build` などは無視

## インストール
```
pip install git+https://github.com/sndryu1/depcheck-lite.git
```
(PyPI 公開後は `pip install depcheck-lite`)

**実行ファイル(Python 不要):** [Releases](https://github.com/sndryu1/depcheck-lite/releases) から Windows / macOS / Linux 用をダウンロード。

または単一ファイルだけ取得:
```
curl -O https://raw.githubusercontent.com/sndryu1/depcheck-lite/main/depcheck_lite.py
```

## 使い方
```
python depcheck_lite.py [path] [--json]
```
- 終了コード: `0` 問題なし / `1` 問題あり / `2` 対象ファイルなし
- CI: `- run: python depcheck_lite.py`

## 制限(正直に)
静的な文字列照合なので、動的に組み立てた `require(name)` や、プラグインとして設定ファイル内だけで読み込まれる依存は検出できず、誤って「未使用」になることがあります。削除前に確認してください。

## テスト
`python -m unittest discover tests`

## License
MIT
