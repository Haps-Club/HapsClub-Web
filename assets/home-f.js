/* haps.club homepage interactions (Design F). Content is server-rendered by
   scripts/build_home.py; this file only adds filters, motion and the signup. */
(function () {
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

  // Filters: category + neighborhood
  var cat = 'All', area = 'all';
  var rows = $$('.row'), cchips = $$('.chip[data-f]'), achips = $$('.chip[data-area]');
  var LIMIT = 14, expanded = false, more = $('#more');
  if (more) more.onclick = function () { expanded = true; apply(); };
  function apply() {
    var shown = 0, filtered = cat !== 'All' || area !== 'all';
    rows.forEach(function (r) {
      var ok = (cat === 'All' || r.dataset.c.split(' ').indexOf(cat.split(' ')[0]) > -1 ||
                (cat === 'Date night' && r.dataset.c.indexOf('Date night') > -1)) &&
               (area === 'all' || r.dataset.a === area);
      if (ok) shown++;
      var cut = ok && !filtered && !expanded && shown > LIMIT;
      r.classList.toggle('hide', !ok || cut); if (ok && !cut) r.classList.add('in');
    });
    if (more) more.hidden = filtered || expanded || shown <= LIMIT;
    var em = $('#empty'); if (em) em.hidden = shown > 0;
    cchips.forEach(function (c) { var on = c.dataset.f === cat; c.classList.toggle('on', on); c.setAttribute('aria-pressed', on); });
    achips.forEach(function (c) { var on = c.dataset.area === area; c.classList.toggle('on', on); c.setAttribute('aria-pressed', on); });
  }
  cchips.forEach(function (c) { c.onclick = function () { cat = c.dataset.f; apply(); }; });
  achips.forEach(function (c) { c.onclick = function () { area = c.dataset.area; apply(); }; });
  $$('[data-go]').forEach(function (a) { a.addEventListener('click', function () { cat = a.dataset.go; area = 'all'; apply(); }); });

  apply();

  // Header shadow
  var hdr = $('#top');
  addEventListener('scroll', function () { hdr.classList.toggle('scrolled', scrollY > 10); }, { passive: true });

  // Reveal on scroll (section heads wipe, items fade up with stagger)
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: .12 });
    $$('.head').forEach(function (h) { io.observe(h); });
    $$('.rv').forEach(function (el) {
      var sib = [].filter.call(el.parentElement.children, function (x) { return x.classList.contains('rv'); });
      el.style.transitionDelay = (sib.indexOf(el) % 6) * 70 + 'ms'; io.observe(el);
    });
  } else { $$('.head,.rv').forEach(function (el) { el.classList.add('in'); }); }

  // Count-up
  $$('[data-count]').forEach(function (el) {
    var end = +el.dataset.count; if (reduce || !('IntersectionObserver' in window)) return;
    el.textContent = '0';
    var o = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return; o.disconnect();
      var t0 = performance.now();
      (function f(t) { var p = Math.min(1, (t - t0) / 1200); el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(f); })(t0);
    }, { threshold: .6 }); o.observe(el);
  });

  // Rotating "On the list now"
  var rot = $('#rot'), items = window.HAPS_ROT || [], i = 0;
  var col = { food: '--food-ink', music: '--music', culture: '--culture', out: '--out-ink' };
  function nb(t) { var k = t.lastIndexOf(' '); return k > 0 ? t.slice(0, k) + ' ' + t.slice(k + 1) : t; }
  function show(k) { rot.textContent = nb(items[k][0]); rot.style.color = 'var(' + (col[items[k][1]] || '--signal') + ')'; }
  if (rot && items.length) {
    show(0);
    if (!reduce && items.length > 1) setInterval(function () {
      rot.classList.add('out');
      setTimeout(function () { i = (i + 1) % items.length; show(i); rot.classList.remove('out'); rot.classList.add('pre'); void rot.offsetWidth; rot.classList.remove('pre'); }, 330);
    }, 2600);
  }

  // Headline: unclip after entrance so glyph edges are never cut
  setTimeout(function () { var m = $('.mega'); if (m) m.classList.add('done'); }, reduce ? 0 : 1300);

  // MailerLite signup without leaving the page
  var form = $('#joinform'), note = $('#joinnote');
  if (form) form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var btn = form.querySelector('button'); btn.disabled = true; btn.textContent = 'Sending…';
    fetch(form.action, { method: 'POST', body: new FormData(form), mode: 'no-cors' })
      .then(function () {
        form.classList.add('done'); btn.textContent = 'You’re in. Check your inbox.';
        if (note) note.textContent = 'One last step: tap the confirm link we just emailed you.';
        if (window.gtag) gtag('event', 'sign_up', { method: 'homepage' });
      })
      .catch(function () { btn.disabled = false; btn.textContent = 'Try again'; });
  });
})();
