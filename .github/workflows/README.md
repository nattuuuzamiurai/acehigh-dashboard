# Claude 自動 PR レビュー

`claude-pr-review.yml` は、プルリクエストが **作成・更新** されたときに Claude が
自動でコードレビューを行うワークフローです。

## 動作

- トリガー: PR の `opened` / `synchronize` / `reopened` / `ready_for_review`
  （＝ PR が来た時・更新された時。定期実行ではなくイベント駆動）
- レビュー結果:
  - 問題がなければ **承認 (Approve)**
  - 問題があれば **変更要求 (Request changes)** ＋ 修正項目のコメント
- コメント・本文はすべて日本語

## セットアップ（初回のみ・必須）

1. Anthropic API キーをリポジトリのシークレットに登録する
   - GitHub → リポジトリの **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: Anthropic Console で発行した API キー
   - 組織で共通化する場合は Organization secret にすると全リポで共有できます。

これだけで、以降 PR が作成されるたびに自動でレビューが走ります。

## 他のリポジトリにも適用する

このワークフロー（`.github/workflows/claude-pr-review.yml`）を対象リポジトリに
コピーし、同じく `ANTHROPIC_API_KEY` シークレットを設定してください。
Organization secret を使えば、シークレットの再設定は不要です。

## カスタマイズ

- レビューの観点や口調は `claude-pr-review.yml` 内の `prompt:` を編集して調整できます。
- ドラフト PR はレビュー対象外（`ready_for_review` になった時点でレビュー）です。
