/* Graphique automatique sous chaque tableau marqué data-graphique (reporting et états).
 *   data-graphique="barres" | "courbes" | "barres-h"
 *   data-colonnes="1,2,3"   colonnes chiffrées à tracer (0 = première colonne, celle des libellés)
 *   data-sens="lignes"      chaque ligne du tableau devient une série (tableau éléments × mois)
 *   data-max="12"           nombre de lignes tracées au plus (les plus fortes ; le reste est « Autres »)
 * Les chiffres sont relus dans le tableau affiché : le graphique montre exactement ce que dit le tableau.
 */
(function () {
  const tables = document.querySelectorAll("table[data-graphique]");
  if (!tables.length) return;
  // Ordre fixe des couleurs (palette contrôlée pour les daltonismes) ; le logiciel s'affiche sur fond clair
  const COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"];
  const AUTRES = "#8a8984";
  const fmt = v => (v ?? 0).toLocaleString("fr-FR", { maximumFractionDigits: 0 });

  function nombre(cellule) {
    if (!cellule) return null;
    const t = cellule.textContent.replace(/[\s  %]/g, "").replace("−", "-").replace(",", ".");
    if (t === "") return 0;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }
  const texte = c => (c ? c.textContent.replace(/\s+/g, " ").trim() : "");

  function lignesDuCorps(table) {
    return [...table.tBodies].flatMap(b => [...b.rows]).filter(r => !r.querySelector("[colspan]") && r.cells.length > 1);
  }

  function series(table) {
    const entete = table.tHead ? table.tHead.rows[table.tHead.rows.length - 1].cells : [];
    const lignes = lignesDuCorps(table);
    const max = Number(table.dataset.max || 15);
    if (table.dataset.sens === "lignes") {
      // Colonnes = périodes (toutes les colonnes chiffrées sauf la dernière, le total)
      const cols = [...entete].map((_, i) => i).filter(i => i > 0 && i < entete.length - 1);
      const tri = lignes.map(r => ({ nom: texte(r.cells[0]), valeurs: cols.map(i => nombre(r.cells[i]) || 0),
                                     total: Math.abs(nombre(r.cells[r.cells.length - 1]) || 0) }))
                        .sort((a, b) => b.total - a.total);
      const gardees = tri.slice(0, Math.min(max, 7));
      const reste = tri.slice(gardees.length);
      if (reste.length) gardees.push({ nom: `Autres (${reste.length})`, valeurs: cols.map((_, j) => reste.reduce((s, x) => s + x.valeurs[j], 0)), autres: true });
      return { etiquettes: cols.map(i => texte(entete[i])), jeux: gardees.map(g => ({ nom: g.nom, valeurs: g.valeurs, autres: g.autres })) };
    }
    // Colonnes : numéros, intitulés (« Total produits ») ou « auto » (colonnes de montants, 3 au plus)
    const decalage = lignes.length ? lignes[0].cells.length - entete.length : 0;   // en-tête sur deux lignes
    const intitules = [...entete].map(texte);
    const demande = (table.dataset.colonnes || "1").split(",").map(x => x.trim());
    const cols = (demande[0] === "auto"
      ? [...entete].map((c, i) => c.dataset.type === "montant" ? i : -1).filter(i => i >= 0).slice(0, 3)
      : demande.map(x => /^\d+$/.test(x) ? Number(x) - decalage : intitules.indexOf(x)).filter(i => i >= 0))
      .map(i => i + decalage);
    let retenues = lignes;
    if (lignes.length > max) {                                  // les plus fortes sur la première série
      retenues = [...lignes].sort((a, b) => Math.abs(nombre(b.cells[cols[0]]) || 0) - Math.abs(nombre(a.cells[cols[0]]) || 0)).slice(0, max);
      retenues.sort((a, b) => lignes.indexOf(a) - lignes.indexOf(b));
    }
    return { etiquettes: retenues.map(r => texte(r.cells[0])),
             jeux: cols.map(i => ({ nom: texte(entete[i - decalage]), valeurs: retenues.map(r => nombre(r.cells[i])) })),
             tronque: lignes.length > max ? `Les ${max} plus fortes lignes sur ${lignes.length}.` : "" };
  }

  function dessiner(table, n) {
    const s = series(table);
    if (!s.etiquettes.length || !s.jeux.length) return;
    const forme = table.dataset.graphique;
    const bloc = document.createElement("div");
    bloc.className = "card p-3 mb-3 graphique-sous-tableau";
    const titre = table.dataset.titreGraphique || "Graphique du tableau ci-dessus";
    bloc.innerHTML = `<div class="small fw-semibold mb-2">${titre}</div><div style="position:relative;height:${forme === "barres-h" ? Math.max(220, 26 * s.etiquettes.length) : 280}px"><canvas aria-label="${titre}" role="img"></canvas></div>` +
      (s.tronque ? `<div class="small text-muted mt-1">${s.tronque}</div>` : "");
    const ancre = table.closest(".card, .table-responsive") || table;
    ancre.after(bloc);
    const courbes = forme === "courbes";
    new Chart(bloc.querySelector("canvas"), {
      type: courbes ? "line" : "bar",
      data: { labels: s.etiquettes, datasets: s.jeux.map((j, i) => {
        const c = j.autres ? AUTRES : COULEURS[i % COULEURS.length];
        return { label: j.nom, data: j.valeurs, borderColor: c, backgroundColor: courbes ? c : c,
                 borderWidth: courbes ? 2 : 0, borderRadius: courbes ? 0 : 4, pointRadius: courbes ? 3 : 0,
                 pointHoverRadius: 5, tension: 0.25, maxBarThickness: 36 };
      }) },
      options: {
        maintainAspectRatio: false, indexAxis: forme === "barres-h" ? "y" : "x",
        interaction: { mode: "index", intersect: false },
        plugins: { legend: { display: s.jeux.length > 1, position: "bottom" },
                   tooltip: { callbacks: { label: c => `${c.dataset.label} : ${fmt(c.parsed[forme === "barres-h" ? "x" : "y"])}` } } },
        scales: { [forme === "barres-h" ? "x" : "y"]: { ticks: { callback: fmt }, grid: { color: "#eee" } },
                  [forme === "barres-h" ? "y" : "x"]: { grid: { display: false },
                    ticks: { callback(v) { const l = String(this.getLabelForValue(v)); return l.length > 26 ? l.slice(0, 25) + "…" : l; } } } }
      }
    });
  }

  if (typeof Chart === "undefined") {                         // Chart.js n'est chargé que s'il y a un graphique
    const s = document.createElement("script");
    s.src = document.currentScript.dataset.chart;
    s.onload = () => tables.forEach(dessiner);
    document.head.appendChild(s);
  } else {
    tables.forEach(dessiner);
  }
})();
