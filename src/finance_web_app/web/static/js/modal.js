// Native <dialog> modals: open triggers carry data-open-modal="<dialog id>",
// close buttons carry data-close-modal, clicking the backdrop closes, and a
// dialog with data-open-on-load opens immediately (used when a submit failed
// validation so the error and form stay in view). No dependencies.
(function () {
  "use strict";

  document.querySelectorAll("[data-open-modal]").forEach(function (trigger) {
    var dialog = document.getElementById(trigger.getAttribute("data-open-modal"));
    if (dialog && typeof dialog.showModal === "function") {
      trigger.addEventListener("click", function () {
        dialog.showModal();
      });
    }
  });

  document.querySelectorAll("[data-close-modal]").forEach(function (button) {
    button.addEventListener("click", function () {
      var dialog = button.closest("dialog");
      if (dialog) {
        dialog.close();
      }
    });
  });

  document.querySelectorAll("dialog.modal").forEach(function (dialog) {
    // Click on the backdrop (the dialog element itself) closes it.
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });
    if (dialog.hasAttribute("data-open-on-load") && typeof dialog.showModal === "function") {
      dialog.showModal();
    }
  });
})();
