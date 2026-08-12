/* Future of Korea — minimal progressive enhancement. No dependencies, ~1KB. */
(function () {
  "use strict";

  // Close the mobile nav after choosing a link.
  var t = document.getElementById("navtoggle");
  if (t) {
    document.querySelectorAll(".site-nav a").forEach(function (a) {
      a.addEventListener("click", function () { t.checked = false; });
    });
  }

  // Reading-progress bar on articles.
  var art = document.querySelector(".article .prose");
  if (art && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var bar = document.createElement("div");
    bar.setAttribute("role", "presentation");
    bar.style.cssText =
      "position:fixed;top:0;left:0;height:2px;width:0;z-index:60;background:var(--accent);" +
      "transition:width .1s linear;will-change:width";
    document.body.appendChild(bar);
    var tick = false;
    addEventListener("scroll", function () {
      if (tick) return;
      tick = true;
      requestAnimationFrame(function () {
        var r = art.getBoundingClientRect();
        var total = r.height - innerHeight;
        var done = Math.min(Math.max(-r.top, 0), Math.max(total, 1));
        bar.style.width = (total > 0 ? (done / total) * 100 : 0) + "%";
        tick = false;
      });
    }, { passive: true });
  }

  // Open the FAQ item a visitor deep-linked to.
  if (location.hash) {
    var el = document.querySelector(location.hash);
    if (el) { var d = el.closest("details"); if (d) d.open = true; }
  }

  // External links: make the new-tab behaviour safe and announced.
  document.querySelectorAll('.prose a[href^="http"]').forEach(function (a) {
    if (a.hostname && a.hostname !== location.hostname) {
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener nofollow");
    }
  });
})();
