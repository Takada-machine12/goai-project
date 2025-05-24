# 囲碁AI プロジェクト

## 概要
このプロジェクトは、ディープラーニングとモンテカルロ木探索を用いた囲碁AIの実装です。

## 特徴
- モンテカルロ木探索（MCTS）の実装
- ディープラーニングモデル（CNN）による評価関数
- 自己対戦による強化学習

## セットアップ
```bash
# 環境構築
conda create -n goai python=3.10
conda activate goai
pip install -r requirements.txt