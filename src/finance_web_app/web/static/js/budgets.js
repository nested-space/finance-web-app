// Budgets page charts: spend-vs-budget bar, 6-month cumulative history line, and
// a budget breakdown pie. Reads the server-shaped payload embedded in the page;
// no aggregation here.
(function () {
  "use strict";

  var dataEl = document.getElementById("budgets-charts");
  if (!dataEl || typeof Chart === "undefined") {
    return;
  }
  var p = JSON.parse(dataEl.textContent);

  var styles = getComputedStyle(document.documentElement);
  function cssVar(name) {
    return styles.getPropertyValue(name).trim();
  }
  var SERIES = ["--s1", "--s2", "--s3", "--s4", "--s5"].map(cssVar);
  function palette(count) {
    var colours = [];
    for (var i = 0; i < count; i += 1) {
      colours.push(SERIES[i % SERIES.length]);
    }
    return colours;
  }
  function makeChart(id, config) {
    var canvas = document.getElementById(id);
    return canvas ? new Chart(canvas, config) : null;
  }

  makeChart("chart-spend-vs-budget", {
    type: "bar",
    data: {
      labels: p.spend_vs_budget.labels,
      datasets: [
        { label: "Spend", data: p.spend_vs_budget.spend, backgroundColor: SERIES[0] },
        { label: "Budget", data: p.spend_vs_budget.budget, backgroundColor: SERIES[1] },
      ],
    },
    options: { responsive: true },
  });

  makeChart("chart-budget-history", {
    type: "line",
    data: {
      labels: p.history.labels,
      datasets: [
        { label: "Budget", data: p.history.budget_cumulative, borderColor: SERIES[1], backgroundColor: SERIES[1], tension: 0.2, fill: false },
        { label: "Spend", data: p.history.spend_cumulative, borderColor: SERIES[0], backgroundColor: SERIES[0], tension: 0.2, fill: false },
      ],
    },
    options: { responsive: true },
  });

  makeChart("chart-budget-breakdown", {
    type: "doughnut",
    data: {
      labels: p.breakdown.labels,
      datasets: [{ data: p.breakdown.values, backgroundColor: palette(p.breakdown.labels.length) }],
    },
    options: { responsive: true },
  });
})();
