// UI-only: hide the length fields when the recurrence is "Once Only".
// No business logic — the server validates that length is required otherwise.
(function () {
  "use strict";
  var recurrence = document.getElementById("commitment-recurrence");
  var lengthFields = document.getElementById("commitment-length-fields");
  if (!recurrence || !lengthFields) {
    return;
  }
  function sync() {
    lengthFields.hidden = recurrence.value === "ONCE_ONLY";
  }
  recurrence.addEventListener("change", sync);
  sync();
})();
