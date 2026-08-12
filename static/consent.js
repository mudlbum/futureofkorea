/* Future of Korea — Consent Mode v2 + cookie banner. No dependencies, no CMP vendor.
 *
 * Order matters and is the whole point of this file: consent defaults must be
 * pushed to the dataLayer BEFORE gtag.js or the AdSense tag load, otherwise the
 * first pageview and the first ad request leave before consent is known. That is
 * the mistake that gets sites flagged under the EU user consent policy.
 *
 * Defaults are denied everywhere. Rather than trying to geolocate the reader —
 * which we cannot do reliably from a static page — we deny by default for
 * everyone and grant on explicit acceptance. Stricter than required outside the
 * EEA/UK, and strictly correct inside it.
 */
(function () {
  "use strict";

  var KEY = "fok-consent-v1";
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  function readStored() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); }
    catch (e) { return null; }
  }

  var stored = readStored();

  // 1. Defaults, before any Google tag loads.
  gtag("consent", "default", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "granted",
    security_storage: "granted",
    wait_for_update: 500
  });

  // 2. If this visitor already decided, replay it immediately.
  if (stored && stored.choice) {
    applyChoice(stored.choice, false);
  }

  function applyChoice(choice, persist) {
    var granted = choice === "all";
    gtag("consent", "update", {
      ad_storage: granted ? "granted" : "denied",
      ad_user_data: granted ? "granted" : "denied",
      ad_personalization: granted ? "granted" : "denied",
      analytics_storage: granted ? "granted" : "denied"
    });
    if (persist) {
      try {
        localStorage.setItem(KEY, JSON.stringify({ choice: choice, at: Date.now() }));
      } catch (e) { /* private mode — the choice simply won't persist */ }
    }
  }

  // 3. Banner, only when no decision is on record.
  if (stored && stored.choice) return;

  function build() {
    var wrap = document.createElement("div");
    wrap.className = "consent";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-label", "Cookie choices");
    wrap.setAttribute("aria-live", "polite");
    wrap.innerHTML =
      '<div class="consent-inner">' +
        '<p class="consent-copy">We use cookies to measure how the site is read, and — once ' +
        'advertising is enabled — to show ads. You can decline and everything still works. ' +
        'See our <a href="/cookie-policy/">cookie policy</a> and ' +
        '<a href="/privacy-policy/">privacy policy</a>.</p>' +
        '<div class="consent-actions">' +
          '<button type="button" class="btn btn-ghost" data-consent="essential">Essential only</button>' +
          '<button type="button" class="btn btn-primary" data-consent="all">Accept all</button>' +
        '</div>' +
      '</div>';

    wrap.addEventListener("click", function (e) {
      var b = e.target.closest("[data-consent]");
      if (!b) return;
      applyChoice(b.getAttribute("data-consent"), true);
      wrap.setAttribute("data-closing", "1");
      setTimeout(function () { wrap.remove(); }, 220);
    });

    document.body.appendChild(wrap);
    requestAnimationFrame(function () { wrap.setAttribute("data-in", "1"); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
