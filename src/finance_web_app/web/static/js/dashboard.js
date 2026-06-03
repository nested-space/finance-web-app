// Dashboard charts + month navigation. Reads the server-shaped payload embedded
// in the page and draws it with Chart.js; on prev/next it refetches the same
// payload from /finance/api/model and swaps the data in place. No aggregation or
// business logic here — only drawing, formatting, and fetching.
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
  var MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  function gbp(value) {
    return "£" + Number(value).toFixed(2);
  }
  function palette(count) {
    var colours = [];
    for (var i = 0; i < count; i += 1) {
      colours.push(SERIES[i % SERIES.length]);
    }
    return colours;
  }

  var current = JSON.parse(dataEl.textContent);
  var charts = {};

  function makeChart(id, config) {
    var canvas = document.getElementById(id);
    return canvas ? new Chart(canvas, config) : null;
  }

  function build(p) {
    charts.finance = makeChart("chart-finance-model", {
      type: "line",
      data: {
        labels: p.labels,
        datasets: [{ label: "Balance", data: p.finance_model.balance, borderColor: BRAND, backgroundColor: BRAND, tension: 0.2, fill: false }],
      },
      options: { responsive: true, plugins: { legend: { display: false } } },
    });
    charts.flows = makeChart("chart-income-outgoings", {
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
    charts.budget = makeChart("chart-budget-breakdown", {
      type: "doughnut",
      data: {
        labels: p.budget_breakdown.labels,
        datasets: [{ data: p.budget_breakdown.values, backgroundColor: palette(p.budget_breakdown.labels.length) }],
      },
      options: { responsive: true },
    });
    charts.commitments = makeChart("chart-commitments", {
      type: "pie",
      data: {
        labels: p.commitments_by_category.labels,
        datasets: [{ data: p.commitments_by_category.values, backgroundColor: palette(p.commitments_by_category.labels.length) }],
      },
      options: { responsive: true },
    });
  }

  function updateCharts(p) {
    if (charts.finance) {
      charts.finance.data.labels = p.labels;
      charts.finance.data.datasets[0].data = p.finance_model.balance;
      charts.finance.update();
    }
    if (charts.flows) {
      charts.flows.data.labels = p.labels;
      charts.flows.data.datasets[0].data = p.income_outgoings.income;
      charts.flows.data.datasets[1].data = p.income_outgoings.outgoings;
      charts.flows.update();
    }
    if (charts.budget) {
      charts.budget.data.labels = p.budget_breakdown.labels;
      charts.budget.data.datasets[0].data = p.budget_breakdown.values;
      charts.budget.data.datasets[0].backgroundColor = palette(p.budget_breakdown.labels.length);
      charts.budget.update();
    }
    if (charts.commitments) {
      charts.commitments.data.labels = p.commitments_by_category.labels;
      charts.commitments.data.datasets[0].data = p.commitments_by_category.values;
      charts.commitments.data.datasets[0].backgroundColor = palette(p.commitments_by_category.labels.length);
      charts.commitments.update();
    }
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = text;
    }
  }

  function applyInsights(p) {
    var ins = p.insights;
    setText("insight-total-income", gbp(ins.total_income));
    setText("insight-total-outgoings", gbp(ins.total_outgoings));
    setText("insight-net", gbp(ins.net));
    setText("insight-closing-balance", gbp(ins.closing_balance));
    setText(
      "insight-largest-expense",
      ins.largest_expense ? ins.largest_expense.name + " — " + gbp(ins.largest_expense.amount) : "—"
    );
    setText("insight-over-budget", ins.over_budget.length ? ins.over_budget.join(", ") : "None");
  }

  function applyMeta(p) {
    setText("dashboard-month", MONTHS[p.month] + " " + p.year);
    var prev = shift(p.year, p.month, -1);
    var next = shift(p.year, p.month, 1);
    var prevEl = document.getElementById("nav-prev");
    var nextEl = document.getElementById("nav-next");
    if (prevEl) prevEl.setAttribute("href", "/finance/" + prev[0] + "/" + prev[1]);
    if (nextEl) nextEl.setAttribute("href", "/finance/" + next[0] + "/" + next[1]);
  }

  function shift(year, month, delta) {
    var index = year * 12 + (month - 1) + delta;
    return [Math.floor(index / 12), (index % 12) + 1];
  }

  function navigate(year, month) {
    fetch("/finance/api/model/" + year + "/" + month, { headers: { Accept: "application/json" } })
      .then(function (resp) {
        if (!resp.ok) throw new Error("nav failed");
        return resp.json();
      })
      .then(function (p) {
        current = p;
        updateCharts(p);
        applyInsights(p);
        applyMeta(p);
        history.pushState(null, "", "/finance/" + year + "/" + month);
      })
      .catch(function () {
        window.location.href = "/finance/" + year + "/" + month;
      });
  }

  function onNav(delta) {
    return function (event) {
      event.preventDefault();
      var target = shift(current.year, current.month, delta);
      navigate(target[0], target[1]);
    };
  }

  build(current);
  var prevButton = document.getElementById("nav-prev");
  var nextButton = document.getElementById("nav-next");
  if (prevButton) prevButton.addEventListener("click", onNav(-1));
  if (nextButton) nextButton.addEventListener("click", onNav(1));
})();
