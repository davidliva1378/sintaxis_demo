(async () => {
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  const firstCell = () =>
    $("table.table-striped tbody tr:first-child td:first-child")?.innerText?.trim() || null;

  const getUl = () => $("ul.pagination");

  function getActiveLi() {
    const ul = getUl(); if (!ul) return null;
    return ul.querySelector("li.active") || null;
  }

  function getCurrentPage() {
    const li = getActiveLi(); if (!li) return null;
    const span = li.querySelector("span");
    const txt = span?.textContent?.trim() || "";
    return /^\d+$/.test(txt) ? Number(txt) : null;
  }

  function getMaxVisibleNumber() {
    const ul = getUl(); if (!ul) return null;
    const nums = $$("li a, li span", ul)
      .map(el => (el.textContent || "").trim())
      .filter(t => /^\d+$/.test(t))
      .map(Number);
    return nums.length ? Math.max(...nums) : null;
  }

  // Busca el próximo número a la derecha del <li.active>
  function getNextNumberLinkToRight(curr) {
    const ul = getUl(); if (!ul) return null;
    const lis = $$("li", ul);
    const idxActive = lis.findIndex(li => li.classList.contains("active"));
    if (idxActive < 0) return null;

    for (let i = idxActive + 1; i < lis.length; i++) {
      const a = lis[i].querySelector("a");
      if (!a) continue;
      const t = (a.textContent || "").trim();
      if (/^\d+$/.test(t) && Number(t) > curr) return a;
      // si aparece otro botón (», etc.) lo salteamos acá; esto es SOLO números
    }
    return null;
  }

  // Busca SOLO un botón de avanzar ventana (») A LA DERECHA del activo
  function getRightNextWindowBtn() {
    const ul = getUl(); if (!ul) return null;
    const lis = $$("li", ul);
    const idxActive = lis.findIndex(li => li.classList.contains("active"));
    if (idxActive < 0) return null;

    for (let i = idxActive + 1; i < lis.length; i++) {
      const li = lis[i];
      const a = li.querySelector("a");
      if (!a) continue;
      const t = (a.textContent || "").trim();
      const isNumber = /^\d+$/.test(t);
      const disabled = li.classList.contains("disabled");
      // “botón de ventana” típico: no numérico y no disabled
      if (!isNumber && !disabled) return a;
    }
    return null;
  }

  async function clickAndWait(a, etiqueta) {
    const before = firstCell();
    a.click();

    // esperar hasta 6 s a que cambie la 1ª fila (confirmación de navegación)
    let ok = false;
    for (let t = 0; t < 12; t++) {
      await sleep(500);
      const after = firstCell();
      if (before && after && after !== before) { ok = true; break; }
    }
    console.log(ok ? `✅ Cambio (${etiqueta})` : `⚠️ Sin cambio (${etiqueta})`);
    await sleep(400);
    return ok;
  }

  console.log("▶️ Recorrido secuencial (con corte seguro en la última)…");

  let guardarrail = 0;
  const MAX_STEPS = 20000;
  let totalClicks = 0;
  let estancamientos = 0;

  while (guardarrail++ < MAX_STEPS) {
    const curr = getCurrentPage();
    const maxVis = getMaxVisibleNumber();
    if (curr == null) { console.log("❌ No pude leer la página actual"); break; }

    // 1) Intentar el siguiente número a la derecha
    let next = getNextNumberLinkToRight(curr);
    if (next) {
      console.log(`👉 Ir a página ${next.textContent.trim()} (desde ${curr})`);
      const ok = await clickAndWait(next, `página ${next.textContent.trim()}`);
      totalClicks++;
      if (!ok) {
        // si no cambió, contabilizamos estancamiento
        if (++estancamientos >= 2) { console.log("🛑 Estancado, corto."); break; }
      } else {
        estancamientos = 0;
      }
      continue;
    }

    // 2) Si no hay número a la derecha:
    //    - si curr == max visible y NO hay “»” a la derecha → fin real
    const rightNext = getRightNextWindowBtn();
    if (!rightNext) {
      if (maxVis != null && curr >= maxVis) {
        console.log(`✅ Fin: última página alcanzada (${curr}).`);
        break;
      }
      console.log("⚠️ No hay número siguiente ni botón » a la derecha; corto por seguridad.");
      break;
    }

    // 3) Avanzar ventana con “»” (a la derecha del activo), luego reintentar números
    console.log(`➡️ Avanzo ventana » (desde ${curr})`);
    const ok = await clickAndWait(rightNext, "ventana »");
    totalClicks++;
    if (!ok) {
      if (++estancamientos >= 2) { console.log("🛑 Estancado al avanzar ventana, corto."); break; }
    } else {
      estancamientos = 0;
    }
  }

  console.log(`🏁 Listo. Clicks realizados: ${totalClicks}`);
})();
