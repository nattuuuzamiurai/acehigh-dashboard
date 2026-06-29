// ============================================================
// chaipo_worker.js — チャイポ検証シミュレーター Web Worker
// poker.js + montecarlo.js を importScripts で読み込む
// ============================================================

importScripts('../チャイポ/poker.js', '../チャイポ/montecarlo.js');

// メインスレッドからのメッセージ受信
self.onmessage = function(e) {
  const { totalHands = 10000, batchSize = 200 } = e.data;

  const stats = {
    total:        0,
    busts:        0,
    flCount:      0,
    flByType:     { trips: 0, pair14: 0, pair13: 0, pair12: 0 },
    royaltySum:   0,
    handRankDist: {
      top:    Array(10).fill(0),
      middle: Array(10).fill(0),
      bottom: Array(10).fill(0),
    },
  };

  const deck = Poker.buildDeck();
  let processed = 0;

  function runBatch() {
    const end = Math.min(processed + batchSize, totalHands);

    for (let i = processed; i < end; i++) {
      const result = MC.simulateOneHand(deck);
      stats.total++;

      if (result.isBurst) {
        stats.busts++;
      } else {
        stats.royaltySum += result.royalty;

        if (result.fl) {
          stats.flCount++;
          if      (result.fl.type === 'trips')      stats.flByType.trips++;
          else if (result.fl.pairRank === 14)        stats.flByType.pair14++;
          else if (result.fl.pairRank === 13)        stats.flByType.pair13++;
          else if (result.fl.pairRank === 12)        stats.flByType.pair12++;
        }

        const te = Poker.evaluateHand(result.board.top, true);
        const me = Poker.evaluateHand(result.board.middle, false);
        const be = Poker.evaluateHand(result.board.bottom, false);
        stats.handRankDist.top[te.rank]++;
        stats.handRankDist.middle[me.rank]++;
        stats.handRankDist.bottom[be.rank]++;
      }
    }

    processed = end;

    self.postMessage({
      type: 'progress',
      processed,
      totalHands,
      stats: buildSnapshot(stats),
    });

    if (processed < totalHands) {
      setTimeout(runBatch, 0);
    } else {
      self.postMessage({
        type: 'done',
        stats: buildSnapshot(stats),
      });
    }
  }

  runBatch();
};

function buildSnapshot(s) {
  const n     = s.total;
  const valid = n - s.busts;
  return {
    total:        n,
    burstRate:    n > 0 ? s.busts / n : 0,
    flRate:       n > 0 ? s.flCount / n : 0,
    flByType:     { ...s.flByType },
    avgRoyalty:   valid > 0 ? s.royaltySum / valid : 0,
    handRankDist: s.handRankDist,
  };
}
