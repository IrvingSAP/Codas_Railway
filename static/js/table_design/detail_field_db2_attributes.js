(function () {
  var form = document.getElementById("db2-attrs-form");
  if (!form) return;

  var udfSelect = document.getElementById("sel-user_defined_field");
  var allRows = form.querySelectorAll(".attr-row");
  var otherRows = form.querySelectorAll(".attr-row:not(.attr-row-udf)");
  var otherSelects = form.querySelectorAll(
    ".attr-row:not(.attr-row-udf) [data-row-select]"
  );

  function inputsInRow(row) {
    return row.querySelectorAll("[data-attr-input]");
  }

  function rowHasInput(row) {
    return row.getAttribute("data-input") === "si";
  }

  function setRowInputsEnabled(row, on) {
    if (!rowHasInput(row)) return;
    inputsInRow(row).forEach(function (el) {
      el.disabled = !on;
    });
  }

  function syncRow(row) {
    var sel = row.querySelector("[data-row-select]");
    var active = sel && sel.checked;
    row.classList.toggle("bg-white/[0.03]", active);
    if (udfSelect && udfSelect.checked) return;
    setRowInputsEnabled(row, active);
  }

  function applyUserDefinedLock() {
    if (!udfSelect) return;
    var udfOn = udfSelect.checked;

    if (udfOn) {
      otherSelects.forEach(function (cb) {
        cb.checked = false;
        cb.disabled = true;
      });
      otherRows.forEach(function (row) {
        row.classList.add("is-locked");
        setRowInputsEnabled(row, false);
      });
      var udfRow = form.querySelector(".attr-row-udf");
      if (udfRow) {
        udfRow.classList.add("is-udf-active");
        setRowInputsEnabled(udfRow, true);
      }
    } else {
      otherSelects.forEach(function (cb) {
        cb.disabled = false;
      });
      otherRows.forEach(function (row) {
        row.classList.remove("is-locked");
      });
      var udfRow = form.querySelector(".attr-row-udf");
      if (udfRow) udfRow.classList.remove("is-udf-active");
      allRows.forEach(syncRow);
    }
  }

  form.querySelectorAll("[data-row-select]").forEach(function (cb) {
    cb.addEventListener("change", function () {
      if (cb === udfSelect && udfSelect.checked) {
        applyUserDefinedLock();
        return;
      }
      if (udfSelect && udfSelect.checked) return;
      var row = cb.closest(".attr-row");
      if (row) syncRow(row);
    });
  });

  if (udfSelect) {
    udfSelect.addEventListener("change", applyUserDefinedLock);
  }

  form.addEventListener("submit", function () {
    form.querySelectorAll("[data-attr-input]").forEach(function (el) {
      el.disabled = false;
    });
  });

  allRows.forEach(function (row) {
    if (rowHasInput(row)) setRowInputsEnabled(row, false);
  });
  if (udfSelect && udfSelect.checked) {
    applyUserDefinedLock();
  } else {
    allRows.forEach(syncRow);
  }
})();
