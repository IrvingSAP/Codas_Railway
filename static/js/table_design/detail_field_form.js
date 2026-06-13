/**
 * Formulario de campo DetailTable: longitud/decimales según tipo DB2 y nombre corto/largo.
 * Config JSON en #codas-detail-field-config (generada en Django).
 */
(function () {
  function readConfig() {
    var el = document.getElementById("codas-detail-field-config");
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  function badgeInfo(text) {
    return (
      '<span class="inline-flex rounded-md bg-sky-500/15 px-2 py-0.5 text-[11px] font-medium text-sky-200">' +
      text +
      "</span>"
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    var config = readConfig();
    var form = document.getElementById("detail-field-form");
    if (!config || !form) return;

    var typeField = form.querySelector("select[name='field_type']");
    var lengthField = form.querySelector("input[name='field_length']");
    var decimalsField = form.querySelector("input[name='decimal_places']");
    var isKeyField = form.querySelector("input[name='is_key']");
    var orderKeyField = form.querySelector("input[name='order_key']");
    var shortField = form.querySelector("input[name='field_name_short']");
    var longField = form.querySelector("input[name='field_name_long']");
    var wrapLen = document.getElementById("wrap-field-length");
    var wrapDec = document.getElementById("wrap-field-decimals");
    var wrapAlloc = document.getElementById("wrap-allocate-length");
    var wrapIdentity = document.getElementById("wrap-identity");
    var wrapCcsid = document.getElementById("wrap-ccsid");
    var wrapOk = document.getElementById("wrap-order-key");
    var badgeLength = document.getElementById("badge-field-length");
    var badgeDecimals = document.getElementById("badge-field-decimals");
    var badgeAllocate = document.getElementById("badge-allocate");
    var badgeOrderKey = document.getElementById("badge-field-order-key");
    var allocField = form.querySelector("input[name='allocate_length']");
    var isIdentityField = form.querySelector("input[name='is_identity']");
    var ccsidField = form.querySelector("input[name='ccsid']");
    var nullableField = form.querySelector("input[name='nullable']");

    if (
      !typeField ||
      !lengthField ||
      !decimalsField ||
      !isKeyField ||
      !orderKeyField ||
      !wrapLen ||
      !wrapDec ||
      !wrapOk
    ) {
      return;
    }

    var DECIMAL = config.DECIMAL;
    var NUMERIC = config.NUMERIC;
    var fixedLengths = config.fixedLengths || {};
    var lengthRequired = config.lengthRequired || [];
    var noLengthTypes = config.noLengthTypes || [];
    var allocateForTypes = config.allocateForTypes || [];
    var identityForTypes = config.identityForTypes || [];
    var ccsidForTypes = config.ccsidForTypes || [];

    function isAllocateType(t) {
      return allocateForTypes.indexOf(t) !== -1;
    }
    function isIdentityType(t) {
      return identityForTypes.indexOf(t) !== -1;
    }
    function isCcsidType(t) {
      return ccsidForTypes.indexOf(t) !== -1;
    }

    function clearBadges() {
      if (badgeLength) badgeLength.innerHTML = "";
      if (badgeDecimals) badgeDecimals.innerHTML = "";
      if (badgeAllocate) badgeAllocate.innerHTML = "";
      if (badgeOrderKey) badgeOrderKey.innerHTML = "";
      [lengthField, decimalsField, orderKeyField, allocField].forEach(function (el) {
        if (el) el.classList.remove("field-js-highlight");
      });
    }

    function applyAllocateRow() {
      if (!wrapAlloc || !allocField) return;
      if (isAllocateType(typeField.value)) {
        wrapAlloc.classList.remove("hidden");
        allocField.readOnly = false;
        allocField.disabled = false;
        if (badgeAllocate) badgeAllocate.innerHTML = badgeInfo("VARCHAR / VARGRAPHIC");
        allocField.classList.add("field-js-highlight");
      } else {
        wrapAlloc.classList.add("hidden");
        allocField.value = "";
        allocField.readOnly = true;
        allocField.disabled = false;
        if (badgeAllocate) badgeAllocate.innerHTML = "";
        allocField.classList.remove("field-js-highlight");
      }
    }

    function applyIdentityRow() {
      if (!wrapIdentity || !isIdentityField) return;
      if (isIdentityType(typeField.value)) {
        wrapIdentity.classList.remove("hidden");
        isIdentityField.disabled = false;
      } else {
        wrapIdentity.classList.add("hidden");
        isIdentityField.checked = false;
        isIdentityField.disabled = false;
      }
    }

    function applyCcsidRow() {
      if (!wrapCcsid || !ccsidField) return;
      if (isCcsidType(typeField.value)) {
        wrapCcsid.classList.remove("hidden");
        ccsidField.readOnly = false;
        ccsidField.disabled = false;
      } else {
        wrapCcsid.classList.add("hidden");
        ccsidField.value = "";
        ccsidField.readOnly = true;
        ccsidField.disabled = false;
      }
    }

    function setReadonlyPair(lenReadonly, decReadonly) {
      lengthField.readOnly = lenReadonly;
      decimalsField.readOnly = decReadonly;
    }

    function updateFields() {
      clearBadges();
      var type = typeField.value;
      wrapLen.classList.remove("hidden");
      setReadonlyPair(false, false);

      if (Object.prototype.hasOwnProperty.call(fixedLengths, type)) {
        lengthField.value = String(fixedLengths[type]);
        lengthField.readOnly = true;
        decimalsField.value = "0";
        decimalsField.readOnly = true;
        wrapDec.classList.add("hidden");
        if (badgeLength) badgeLength.innerHTML = badgeInfo("Longitud fija");
        lengthField.classList.add("field-js-highlight");
        applyAllocateRow();
        applyIdentityRow();
        applyCcsidRow();
        return;
      }

      if (lengthRequired.indexOf(type) !== -1) {
        decimalsField.value = "";
        decimalsField.readOnly = true;
        wrapDec.classList.add("hidden");
        lengthField.readOnly = false;
        if (badgeLength) badgeLength.innerHTML = badgeInfo("Requiere longitud");
        lengthField.classList.add("field-js-highlight");
        applyAllocateRow();
        applyIdentityRow();
        applyCcsidRow();
        return;
      }

      if (type === DECIMAL || type === NUMERIC) {
        wrapDec.classList.remove("hidden");
        lengthField.readOnly = false;
        decimalsField.readOnly = false;
        if (badgeLength) badgeLength.innerHTML = badgeInfo("Requiere longitud");
        if (badgeDecimals) badgeDecimals.innerHTML = badgeInfo("Requiere decimales");
        lengthField.classList.add("field-js-highlight");
        decimalsField.classList.add("field-js-highlight");
        applyAllocateRow();
        applyIdentityRow();
        applyCcsidRow();
        return;
      }

      if (noLengthTypes.indexOf(type) !== -1) {
        lengthField.value = "0";
        lengthField.readOnly = true;
        decimalsField.value = "0";
        decimalsField.readOnly = true;
        wrapDec.classList.add("hidden");
        applyAllocateRow();
        applyIdentityRow();
        applyCcsidRow();
        return;
      }

      lengthField.value = "0";
      lengthField.readOnly = true;
      decimalsField.value = "";
      decimalsField.readOnly = true;
      wrapDec.classList.add("hidden");
      applyAllocateRow();
      applyIdentityRow();
      applyCcsidRow();
    }

    function updateKeyFields() {
      if (badgeOrderKey) badgeOrderKey.innerHTML = "";
      orderKeyField.classList.remove("field-js-highlight");
      if (isKeyField.checked) {
        orderKeyField.readOnly = false;
        orderKeyField.disabled = false;
        wrapOk.classList.remove("hidden");
        if (badgeOrderKey) badgeOrderKey.innerHTML = badgeInfo("Llave / orden PK");
        orderKeyField.classList.add("field-js-highlight");
      } else {
        orderKeyField.value = "";
        orderKeyField.readOnly = true;
        orderKeyField.disabled = true;
        wrapOk.classList.add("hidden");
      }
    }

    typeField.addEventListener("change", function () {
      updateFields();
      updateKeyFields();
    });
    isKeyField.addEventListener("change", updateKeyFields);
    if (isIdentityField && nullableField) {
      isIdentityField.addEventListener("change", function () {
        if (isIdentityField.checked) nullableField.checked = false;
      });
    }

    if (shortField) {
      shortField.addEventListener("input", function () {
        shortField.value = shortField.value.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
      });
    }
    if (longField) {
      longField.addEventListener("input", function () {
        longField.value = longField.value
          .replace(/\s+/g, "_")
          .replace(/-/g, "_")
          .replace(/[^A-Za-z0-9_]/g, "")
          .toUpperCase();
      });
    }

    form.addEventListener("submit", function () {
      lengthField.readOnly = false;
      decimalsField.readOnly = false;
      if (allocField) {
        allocField.readOnly = false;
        allocField.disabled = false;
      }
      if (isIdentityField) isIdentityField.disabled = false;
      if (ccsidField) {
        ccsidField.readOnly = false;
        ccsidField.disabled = false;
      }
    });

    updateFields();
    updateKeyFields();
  });
})();
