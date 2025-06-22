
export function computeMetricsFromTranscripts(transcripts) {
  const metrics = {
    totalCalls: 0,
    csatScores: [],
    cesScores: [],
    hallucinationStats: [],
    legalRisks: [],
    productMentions: {},
    sentimentCount: {
      positive: 0,
      neutral: 0,
      negative: 0,
    }
  };

  for (const transcript of transcripts) {
    metrics.totalCalls++;

    for (const op of transcript.operator_results) {
      const name = op.name.toLowerCase();

      if (name.includes('csat') && op.text_generation_results?.result) {
        const match = op.text_generation_results.result.match(/CSAT Score:\s*(\d)/);
        if (match) metrics.csatScores.push(parseInt(match[1]));
      }

      if (name.includes('effort') && op.text_generation_results?.result) {
        const match = op.text_generation_results.result.match(/CES Score:\s*(\d)/);
        if (match) metrics.cesScores.push(parseInt(match[1]));
      }

      if (name.includes('hallucination') && op.text_generation_results?.result) {
        const hallucData = parseHallucination(op.text_generation_results.result);
        if (hallucData) metrics.hallucinationStats.push(hallucData);
      }

      if (name.includes('legal liabilities') && op.text_generation_results?.result) {
        const risks = parseLegalRisks(op.text_generation_results.result);
        metrics.legalRisks.push(...risks);
      }

      if (name.includes('product interest') && op.text_generation_results?.result) {
        const products = extractProducts(op.text_generation_results.result);
        products.forEach(p => {
          metrics.productMentions[p] = (metrics.productMentions[p] || 0) + 1;
        });
      }

      if (name.includes('sentiment') && op.predicted_label) {
        const label = op.predicted_label.toLowerCase();
        metrics.sentimentCount[label] = (metrics.sentimentCount[label] || 0) + 1;
      }
    }
  }

  // Compute averages
  metrics.avgCSAT = average(metrics.csatScores);
  metrics.avgCES = average(metrics.cesScores);
  metrics.totalHallucinations = metrics.hallucinationStats.reduce((acc, h) => acc + (h.occurrences || 0), 0);
  metrics.totalLegalRiskScore = metrics.legalRisks.reduce((acc, r) => acc + (r.score || 0), 0);

  return metrics;
}

function average(arr) {
  if (!arr.length) return 0;
  return (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
}

function parseHallucination(text) {
  const match = text.match(/Occurrences:\s*(\d+)/);
  return {
    occurrences: match ? parseInt(match[1]) : 0,
    likelihood: text.match(/Likelihood of Hallucinations:\s*(.*)/)?.[1] || "Unknown"
  };
}

function parseLegalRisks(text) {
  const risks = [];
  const regex = /Risk Score:\s*(\d+), Risk Factor:\s*(.*?)\n\s*- Report: (.*?)(?=Risk Score:|\n\n|$)/gs;
  let match;
  while ((match = regex.exec(text)) !== null) {
    risks.push({
      score: parseInt(match[1]),
      factor: match[2].trim(),
      report: match[3].trim()
    });
  }
  return risks;
}

function extractProducts(text) {
  const bulletPoints = text.match(/(?<=\*\*).*?(?=\*\*)/g);
  return bulletPoints || [];
}
