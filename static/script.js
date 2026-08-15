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

  // ── Scroll reveal ───────────────────────────────────────────────────────
  // Adds .reveal to content blocks, then .in when they enter the viewport.
  // Purely transform/opacity, so it never shifts layout. Anything already on
  // screen at load is revealed immediately — no blank first paint, and no
  // dependence on JS for content to be readable (the CSS default is visible
  // until this script opts an element in).
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
      "IntersectionObserver" in window) {
    var targets = document.querySelectorAll(
      ".card, .section-card, .prose > h2, .prose > h3, .prose > p, .prose > ul, " +
      ".prose > ol, .prose > table, .prose > blockquote, .prose > figure, " +
      ".callout, .faq details, .sources, .resources, .related");

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });

    targets.forEach(function (el, i) {
      var r = el.getBoundingClientRect();
      if (r.top < innerHeight * 0.95) { el.classList.add("reveal", "in"); return; }
      el.classList.add("reveal");
      el.style.transitionDelay = ((i % 4) * 45) + "ms";
      io.observe(el);
    });
  }

  // ── Count-up on the key-takeaway figures ────────────────────────────────
  // Animates the number inside <strong> once, when the takeaways scroll into
  // view. Falls back silently to the static text if anything is unparseable,
  // and never rewrites the digits themselves — only the display during flight.
  (function () {
    var box = document.querySelector(".takeaways");
    if (!box || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;

    var nums = [].slice.call(box.querySelectorAll("strong")).map(function (el) {
      var m = /^([^\d\-]*)(-?[\d,]+(?:\.\d+)?)(.*)$/.exec(el.textContent.trim());
      if (!m) return null;
      var target = parseFloat(m[2].replace(/,/g, ""));
      if (!isFinite(target)) return null;
      var decimals = (m[2].split(".")[1] || "").length;
      var grouped = m[2].indexOf(",") > -1;
      return { el: el, pre: m[1], post: m[3], target: target, decimals: decimals,
               grouped: grouped, original: el.textContent };
    }).filter(Boolean);
    if (!nums.length) return;

    function fmt(v, n) {
      var s = v.toFixed(n.decimals);
      if (n.grouped) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return n.pre + s + n.post;
    }

    var io = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      io.disconnect();
      var start = null, dur = 900;
      requestAnimationFrame(function step(ts) {
        if (start === null) start = ts;
        var t = Math.min((ts - start) / dur, 1);
        var e = 1 - Math.pow(1 - t, 3);
        nums.forEach(function (n) { n.el.textContent = fmt(n.target * e, n); });
        if (t < 1) requestAnimationFrame(step);
        else nums.forEach(function (n) { n.el.textContent = n.original; });
      });
    }, { threshold: 0.35 });
    io.observe(box);
  })();


  // ── Theme toggle ────────────────────────────────────────────────────────
  // Cycles light → dark → system. "System" means no attribute at all, so the
  // prefers-color-scheme media query in the stylesheet takes over again.
  //
  // The attribute is applied by a tiny inline script in <head> before first
  // paint; this file only handles the click. Doing it here alone would cause a
  // visible flash of the wrong theme on every page load.
  (function () {
    var KEY = "fok-theme";
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    var root = document.documentElement;

    function label() {
      var t = root.getAttribute("data-theme");
      var next = t === "light" ? "dark" : (t === "dark" ? "system" : "light");
      btn.setAttribute("title", "Theme: " + (t || "system") + " — switch to " + next);
      btn.setAttribute("aria-label", "Colour theme: " + (t || "follows your system") +
                       ". Activate to switch to " + next + ".");
    }

    btn.addEventListener("click", function () {
      var t = root.getAttribute("data-theme");
      var next = t === "light" ? "dark" : (t === "dark" ? null : "light");
      try {
        if (next) { root.setAttribute("data-theme", next); localStorage.setItem(KEY, next); }
        else { root.removeAttribute("data-theme"); localStorage.removeItem(KEY); }
      } catch (e) {
        if (next) root.setAttribute("data-theme", next); else root.removeAttribute("data-theme");
      }
      label();
    });

    label();
  })();

})();
