// Ask Haps — front end for /ask/. Calls the Cloudflare Worker at /api/ask.
(function(){
  var ENDPOINT = "/api/ask";
  var f = document.getElementById("ask-form"), q = document.getElementById("ask-q"),
      btn = f.querySelector("button"), out = document.getElementById("ask-res");
  function esc(s){return String(s||"").replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function show(html){out.innerHTML = html;}
  function run(text){
    text = (text||"").trim(); if (text.length < 3) return;
    q.value = text; btn.disabled = true;
    show('<div class="ask-load">Looking around Los Angeles…</div>');
    try { history.replaceState(null, "", "?q=" + encodeURIComponent(text)); } catch(e){}
    if (window.gtag) gtag("event", "ask_haps", {search_term: text});
    fetch(ENDPOINT, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({q:text})})
      .then(function(r){ return r.json().catch(function(){ return {error:"Ask Haps is still warming up. Check back soon."}; }); })
      .then(function(d){
        if (d.error) { show('<div class="ask-ans"><div class="ask-dot">H</div><div>'+esc(d.error)+'</div></div>'); return; }
        var cards = (d.picks||[]).map(function(p){
          return '<a class="ask-card" href="'+esc(p.link)+'" target="_blank" rel="noopener"><h3>'+esc(p.title)+'</h3>'+
            '<div class="ask-meta">'+esc([p.when,p.where,p.price].filter(Boolean).join(" · "))+'</div>'+
            '<p>'+esc(p.tagline)+'</p></a>';
        }).join("");
        show('<div class="ask-ans"><div class="ask-dot">H</div><div>'+esc(d.answer)+'</div></div>'+(cards?'<div class="ask-grid">'+cards+'</div>':''));
      })
      .catch(function(){ show('<div class="ask-ans"><div class="ask-dot">H</div><div>Ask Haps is still warming up. Check back soon.</div></div>'); })
      .then(function(){ btn.disabled = false; });
  }
  f.addEventListener("submit", function(e){ e.preventDefault(); run(q.value); });
  document.querySelectorAll(".ask-chips button").forEach(function(b){ b.addEventListener("click", function(){ run(b.textContent); }); });
  var pre = new URLSearchParams(location.search).get("q"); if (pre) run(pre);
})();
