# BinaryBuild — バイナリエディタ（MVP）

## 概要

- Windows優先、Python + PySide6で実装する簡易バイナリエディタのMVPです。
- 機能: ファイルを開く、16進/ASCII/UTF-8表示、バイトの上書き編集、保存、PE情報表示、チェックサム表示、差分比較（初期実装は限定範囲）

## セットアップ

1. Python 3.9+ をインストールしてください。
2. 仮想環境を作成し、依存をインストールします:

   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

## 実行

- モジュールとして実行: `python -m src.main`
- 簡易ランチャーを使う: `python run.py`

## ビルド（exe化）

PyInstallerを使ってWindows用の実行ファイルを作成するための簡易ラッパーを `compiler.py` として用意しました。

例:

```powershell
# 単一ファイルの実行ファイルを作る
python compiler.py --onefile --nogui --name BinaryBuild --icon path\to\icon.ico

# 再ビルド（古い build/ と dist/ を削除）
python compiler.py --onefile --rebuild --nogui
```

このスクリプトはPySide6のプラグインディレクトリを自動検出して `--add-data` に追加します。`--nogui` は `--windowed` のエイリアスで、コンソールウィンドウを抑制します（WindowsやmacOSでGUIアプリとして配布する際に使用します）。PyInstallerが見つからない場合は自動でインストールするオプションがあります（デフォルトで有効）。

## 注意

- まだMVPのため、巨大ファイルや挿入モード、Undo拡張などは限定的です。
- 実行ファイルを編集する場合はバックアップを取ってください。

## GitHub 公開

- 補助スクリプト: Windowsなら `scripts\prepare_commit.bat` をレビューして実行すると初回の `git init` / `commit` / `tag` を自動で作れます（実行前に内容を確認してください）。
- 推奨の手順:

```powershell
# レポジトリ作成（gh がインストールされている場合）
gh repo create <your-username>/BinaryBuild --public --source=. --remote=origin --push
# または手動でリモートを追加して push
# git remote add origin https://github.com/your-username/BinaryBuild.git
# git push -u origin main --tags
```

