window.KYOTEI_DATA = {
  "updated": "2026-06-22 01:54",
  "today_label": "2026年6月22日",
  "pred_date": null,
  "pred_is_today": false,
  "week_label": "6/22（月）〜6/28（日）",
  "month_label": "2026年6月",
  "ev_threshold": 1.3,
  "weekly_demo": {
    "total_bets": 0,
    "total_hits": 0,
    "total_invested": 0,
    "total_returned": 0,
    "roi": 0.0,
    "daily": [],
    "start_label": "6/22",
    "end_label": "6/28"
  },
  "monthly_demo": {
    "total_bets": 0,
    "total_hits": 0,
    "total_invested": 0,
    "total_returned": 0,
    "roi": 0.0,
    "daily": [],
    "start_label": "6/1",
    "end_label": "6/30"
  },
  "today_preds": [],
  "weekly_perfs": [
    {
      "week_label": "6/22〜6/28",
      "start": "2026-06-22",
      "end": "2026-06-28",
      "is_current": true,
      "perf": {
        "1.15": {
          "bets": 0,
          "hits": 0,
          "hit_rate": 0.0,
          "invested": 0,
          "returned": 0,
          "roi": 0.0
        },
        "1.2": {
          "bets": 0,
          "hits": 0,
          "hit_rate": 0.0,
          "invested": 0,
          "returned": 0,
          "roi": 0.0
        },
        "1.3": {
          "bets": 0,
          "hits": 0,
          "hit_rate": 0.0,
          "invested": 0,
          "returned": 0,
          "roi": 0.0
        }
      }
    },
    {
      "week_label": "6/15〜6/21",
      "start": "2026-06-15",
      "end": "2026-06-21",
      "is_current": false,
      "perf": {
        "1.15": {
          "bets": 641,
          "hits": 13,
          "hit_rate": 2.0,
          "invested": 64100,
          "returned": 0,
          "roi": 0.0
        },
        "1.2": {
          "bets": 641,
          "hits": 13,
          "hit_rate": 2.0,
          "invested": 64100,
          "returned": 0,
          "roi": 0.0
        },
        "1.3": {
          "bets": 641,
          "hits": 13,
          "hit_rate": 2.0,
          "invested": 64100,
          "returned": 0,
          "roi": 0.0
        }
      }
    }
  ],
  "features": [
    {
      "name": "出走表スクレイピング",
      "desc": "boatrace.jp から全開催場の出走表・直前情報を自動取得"
    },
    {
      "name": "3連単EV計算",
      "desc": "全120通りの期待値（推定確率×オッズ）を算出"
    },
    {
      "name": "オッズ収束フィルター",
      "desc": "発走2時間以内のレースのみ分析（オッズ安定後）"
    },
    {
      "name": "推奨レース絞り込み",
      "desc": "EV≥1.3 の組み合わせを上位5件まで推奨"
    },
    {
      "name": "結果自動照合",
      "desc": "当日夕方に全結果を取得し予測と照合・的中フラグを記録"
    },
    {
      "name": "回収率検証",
      "desc": "EV閾値1.15/1.20/1.30別に的中率・回収率を週次集計"
    },
    {
      "name": "MLモデル学習",
      "desc": "ロジスティック回帰による的中確率の補正学習（50件以上で起動）"
    },
    {
      "name": "メール通知",
      "desc": "朝の予測と夕方の検証結果をGmail経由で自動送信"
    },
    {
      "name": "デモ収益シミュレーション",
      "desc": "推奨レースに仮想100円投票した場合の週次・月次リターンを計算"
    },
    {
      "name": "ダッシュボード自動更新",
      "desc": "予測実行後にGitHub Pagesへ自動プッシュ"
    }
  ]
};
