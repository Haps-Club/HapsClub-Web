/* Footer + pop-up signup for every page that uses the shared chrome.
   Both post to the MailerLite embedded form (double opt-in) without leaving
   the page. The pop-up stays away for 7 days once closed. */
(function () {
  var DAY = 864e5, KEY = 'haps_pop_until';

  function remember(days) {
    try { localStorage.setItem(KEY, String(Date.now() + days * DAY)); } catch (e) {}
  }
  function snoozed() {
    try { return Number(localStorage.getItem(KEY) || 0) > Date.now(); } catch (e) { return false; }
  }

  function wire(form, onDone) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = form.querySelector('button');
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
      fetch(form.action, { method: 'POST', body: new FormData(form), mode: 'no-cors' })
        .then(function () {
          form.classList.add('done');
          if (btn) btn.textContent = 'Check your inbox to confirm';
          if (window.gtag) gtag('event', 'sign_up', { method: form.className + ' ' + location.pathname });
          if (onDone) onDone();
        })
        .catch(function () { if (btn) { btn.disabled = false; btn.textContent = 'Try again'; } });
    });
  }

  var foot = document.querySelector('form.fsub-form');
  if (foot) wire(foot, function () { remember(365); });

  // No pop-up on the signup pages themselves.
  if (/^\/(subscribe|confirm)(\/|\.html)?$/.test(location.pathname)) return;
  if (snoozed()) return;

  var pop, shown = false, last;
  function build() {
    pop = document.createElement('div');
    pop.className = 'pop';
    pop.setAttribute('role', 'dialog');
    pop.setAttribute('aria-label', 'Join the Tuesday edit');
    pop.innerHTML =
      '<button type="button" class="pop-x" aria-label="Close">&times;</button>' +
      '<div class="pop-lab">Los Angeles &middot; every Tuesday</div>' +
      '<h3>The best of LA, in one email.</h3>' +
      '<p>Food, music, shows and the weekend hike. Picked by hand.</p>' +
      '<form class="pop-form" action="' + (foot ? foot.action : '') + '" method="post">' +
      '<input type="email" name="fields[email]" placeholder="you@email.com" required autocomplete="email" inputmode="email" aria-label="Email address">' +
      '<input type="hidden" name="ml-submit" value="1"><input type="hidden" name="anticsrf" value="true">' +
      '<button type="submit">Join</button></form>' +
      '<p class="pop-note">Free. Leave any time.</p>';
    document.body.appendChild(pop);
    pop.querySelector('.pop-x').addEventListener('click', close);
    wire(pop.querySelector('form'), function () {
      remember(365);
      setTimeout(function () { if (pop) pop.classList.remove('on'); }, 2500);
    });
  }
  function close() {
    remember(7);
    if (pop) pop.classList.remove('on');
    if (last && last.focus) last.focus();
  }
  function show() {
    if (shown || snoozed()) return;
    shown = true;
    last = document.activeElement;
    if (!pop) build();
    requestAnimationFrame(function () { pop.classList.add('on'); });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && pop && pop.classList.contains('on')) close();
  });

  // Not on arrival: after 25 seconds, or when a desktop mouse heads for the tab bar.
  setTimeout(show, 25000);
  document.addEventListener('mouseout', function (e) {
    if (!e.relatedTarget && e.clientY <= 0 && !(window.matchMedia && matchMedia('(pointer:coarse)').matches)) show();
  });
})();
