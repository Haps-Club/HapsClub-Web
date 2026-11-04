/* About page tip / contact form: sends through EmailJS.
   Config lives on the <form id="tipForm"> as data attributes (public client-side ids):
   data-emailjs-key, data-emailjs-service, data-emailjs-template, data-emailjs-src, data-emailjs-sri.
   The EmailJS library loads on first interaction, so it costs nothing on page load. */
(function () {
  var form = document.getElementById("tipForm");
  if (!form) return;
  var submit = document.getElementById("tipSubmit");
  var status = document.getElementById("tipStatus");
  var d = form.dataset;
  var loading = null;

  function load() {
    if (window.emailjs) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = d.emailjsSrc;
      if (d.emailjsSri) { s.integrity = d.emailjsSri; s.crossOrigin = "anonymous"; }
      s.onload = function () { window.emailjs.init({ publicKey: d.emailjsKey }); resolve(); };
      s.onerror = function () { loading = null; reject(new Error("emailjs failed to load")); };
      document.head.appendChild(s);
    });
    return loading;
  }

  function say(cls, msg) { status.className = "tip-status" + (cls ? " " + cls : ""); status.textContent = msg; }

  form.addEventListener("focusin", function () { load().catch(function () {}); }, { once: true });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    say("", "");
    var label = submit.textContent;
    submit.disabled = true;
    submit.textContent = "Sending…";
    load()
      .then(function () { return window.emailjs.sendForm(d.emailjsService, d.emailjsTemplate, form); })
      .then(function () { say("success", "Got it. Thanks for the tip. I'll read every word."); form.reset(); })
      .catch(function (err) {
        say("error", "Something went wrong. Try emailing michael@haps.club directly.");
        if (window.console) console.error("Tip form error:", err);
      })
      .then(function () { submit.disabled = false; submit.textContent = label; });
  });
})();
