/* Shared MailerLite signup for every interior page. Forms post to the
   MailerLite embedded form (double opt-in) without leaving the page. */
(function () {
  var forms = document.querySelectorAll('form[action*="mailerlite.com"]');
  [].forEach.call(forms, function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = form.querySelector('button');
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
      fetch(form.action, { method: 'POST', body: new FormData(form), mode: 'no-cors' })
        .then(function () {
          form.classList.add('done');
          if (btn) btn.textContent = 'You’re in. Check your inbox to confirm.';
          if (window.gtag) gtag('event', 'sign_up', { method: location.pathname });
        })
        .catch(function () { if (btn) { btn.disabled = false; btn.textContent = 'Try again'; } });
    });
  });
})();
