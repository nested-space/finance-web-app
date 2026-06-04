// Expenses page charts: a cumulative spend-vs-budget curve (filterable by
// category via /finance/api/expenses), a 6-month cumulative spend line, and a
// spend breakdown pie. Reads the embedded payload; no aggregation here.
(function () {
  "use strict";

  var dataEl = document.getElementById("expenses-charts");
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

  var curveChart = makeChart("chart-expense-curve", {
    type: "line",
    data: {
      labels: p.current_month.labels,
      datasets: [
        { label: "Spend", data: p.current_month.spend_cumulative, borderColor: SERIES[0], backgroundColor: SERIES[0], tension: 0.1, fill: false },
        { label: "Budget", data: p.current_month.budget_cumulative, borderColor: SERIES[1], backgroundColor: SERIES[1], borderDash: [6, 4], fill: false },
      ],
    },
    options: { responsive: true },
  });

  makeChart("chart-expense-history", {
    type: "line",
    data: {
      labels: p.history.labels,
      datasets: [{ label: "Spend", data: p.history.spend_cumulative, borderColor: SERIES[0], backgroundColor: SERIES[0], tension: 0.2, fill: false }],
    },
    options: { responsive: true },
  });

  makeChart("chart-expense-breakdown", {
    type: "doughnut",
    data: {
      labels: p.breakdown.labels,
      datasets: [{ data: p.breakdown.values, backgroundColor: palette(p.breakdown.labels.length) }],
    },
    options: { responsive: true },
  });

  var filter = document.getElementById("expense-category-filter");
  if (filter && curveChart) {
    filter.addEventListener("change", function () {
      var boxes = Array.prototype.slice.call(filter.querySelectorAll("input:checked"));
      var query = boxes
        .map(function (box) {
          return "category=" + encodeURIComponent(box.value);
        })
        .join("&");
      var url = "/finance/api/expenses/" + p.year + "/" + p.month + (query ? "?" + query : "");
      fetch(url, { headers: { Accept: "application/json" } })
        .then(function (resp) {
          if (!resp.ok) throw new Error("filter failed");
          return resp.json();
        })
        .then(function (curve) {
          curveChart.data.labels = curve.labels;
          curveChart.data.datasets[0].data = curve.spend_cumulative;
          curveChart.data.datasets[1].data = curve.budget_cumulative;
          curveChart.update();
        })
        .catch(function () {});
    });
  }
})();
