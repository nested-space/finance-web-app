// Dashboard charts. Reads the server-shaped payload embedded in the page and
// draws it with Chart.js. Month navigation is plain server-side links (full page
// loads), so there's no fetching here — only drawing and formatting.
(function () {
  "use strict";

  var dataEl = document.getElementById("dashboard-data");
  if (!dataEl || typeof Chart === "undefined") {
    return;
  }

  var styles = getComputedStyle(document.documentElement);
  function cssVar(name) {
    return styles.getPropertyValue(name).trim();
  }
  var BRAND = cssVar("--brand");
  var SERIES = ["--s1", "--s2", "--s3", "--s4", "--s5"].map(cssVar);

  function palette(count) {
    var colours = [];
    for (var i = 0; i < count; i += 1) {
      colours.push(SERIES[i % SERIES.length]);
    }
    return colours;
  }

  var current = JSON.parse(dataEl.textContent);

  function makeChart(id, config) {
    var canvas = document.getElementById(id);
    return canvas ? new Chart(canvas, config) : null;
  }

  function build(p) {
    makeChart("chart-finance-model", {
      type: "line",
      data: {
        labels: p.labels,
        datasets: [{ label: "Balance", data: p.finance_model.balance, borderColor: BRAND, backgroundColor: BRAND, tension: 0.2, fill: false }],
      },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
    makeChart("chart-income-outgoings", {
      type: "bar",
      data: {
        labels: p.labels,
        datasets: [
          { label: "Income", data: p.income_outgoings.income, backgroundColor: SERIES[0] },
          { label: "Outgoings", data: p.income_outgoings.outgoings, backgroundColor: SERIES[1] },
        ],
      },
      options: { responsive: true },
    });
    makeChart("chart-budget-breakdown", {
      type: "doughnut",
      data: {
        labels: p.budget_breakdown.labels,
        datasets: [{ data: p.budget_breakdown.values, backgroundColor: palette(p.budget_breakdown.labels.length) }],
      },
      options: { responsive: true },
    });
    makeChart("chart-commitments", {
      type: "pie",
      data: {
        labels: p.commitments_by_category.labels,
        datasets: [{ data: p.commitments_by_category.values, backgroundColor: palette(p.commitments_by_category.labels.length) }],
      },
      options: { responsive: true },
    });
  }

  build(current);
})();
