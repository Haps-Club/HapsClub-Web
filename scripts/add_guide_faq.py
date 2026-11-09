#!/usr/bin/env python3
"""Add a visible FAQ block + FAQPage JSON-LD to selected guides. Idempotent.

Every answer restates a fact already on that guide's page (no new claims), so when a
guide's facts change, edit the matching answer here and re-run. Run by sweep.py.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAQ = {
 "free-museum-days-los-angeles": [
  ("Which Los Angeles museums are free every day?",
   "Eight are free every day they are open: The Broad, the Getty Center, the Getty Villa, the Hammer, MOCA Grand Avenue, the California Science Center, Griffith Observatory and the Fowler at UCLA. Free admission is not always a free visit. The Getty charges $25 to park and the Hammer charges $9."),
  ("When is the Autry Museum free?",
   "On the first Wednesday of the month, not the second Tuesday. That is the most repeated error in LA free-museum listings."),
  ("When is LACMA free?",
   "LACMA is free to all on the second Tuesday of the month. It is also free to LA County residents on weekdays after 3pm with ID, and it is closed Wednesdays."),
  ("Do I need a reservation for the free Getty?",
   "Yes. Both Getty sites require a timed reservation, and turning up without one is the most common way a free Getty day fails."),
 ],
 "supper-clubs-los-angeles": [
  ("What is a supper club in Los Angeles?",
   "Usually a long table someone else has set, where the seating does the introductions. Haps Club runs its own at Hermanito in Santa Monica, LA Foodshop runs a monthly one in a different space each time, and Twentieth Street Garden drops backyard dinners on Hotplate a few times a year."),
  ("How do I eat dinner with strangers in LA?",
   "Three ways: a long-table dinner, a matched-dinner app, or a chef's counter. Timeleft seats you with five strangers every Wednesday and reveals the restaurant that afternoon. 222 groups you of about five off a personality questionnaire."),
  ("What is the hardest dinner reservation in LA?",
   "On this guide's list, Hayato downtown is the hardest reservation in the city."),
 ],
 "free-things-to-do-in-la-this-weekend": [
  ("What is free to do in Los Angeles every weekend?",
   "Griffith Observatory, The Broad, the Hammer, MOCA Grand and the Fowler are free every day they are open. So are the Venice Canals, the Santa Monica stairs, the Annenberg Community Beach House, the Venice Beach Recreation Center and the Strand. Smorgasburg LA is free to enter on Sundays, 10am to 4pm."),
  ("Is Griffith Observatory free?",
   "Admission is free any day. The planetarium show is ticketed and sold same day only."),
  ("What does free leave out?",
   "Mostly parking. Free admission does not cover parking, and the guide's 'What free leaves out' section has the details."),
 ],
 "venice": [
  ("What is the best way to spend a day in Venice, CA?",
   "Start at Gjusta bakery before ten, walk the Venice Canals, walk Abbot Kinney top to bottom, then book dinner. The canals are free and take about forty minutes, and the whole walking loop is about two miles."),
  ("Where should I park in Venice?",
   "Park once and walk. For the canals, park near Washington and Pacific. Abbot Kinney, the canals and the boardwalk are all within the same twenty-minute walk."),
  ("Do Venice restaurants take walk-ins?",
   "Gjelina takes walk-ins at the bar if you are willing to wait. The Tasting Kitchen and San Damián should be booked, and Felix is the hardest table on the street."),
 ],
 "santa-monica": [
  ("What is free to do in Santa Monica?",
   "The Santa Monica stairs at Adelaide Dr and 4th St, the courtyard, splash pad and beach courts at the Annenberg Community Beach House, the Wednesday farmers market on Arizona Avenue, and the Strand beach path."),
  ("Which Santa Monica farmers market is best?",
   "The Wednesday market on Arizona Avenue, 8am to 1pm. It has sixty-plus farms and a chefs' market, and has been running since 1981. The Saturday market is bigger and worse."),
  ("Does parking fill up at the Annenberg Beach House?",
   "Yes. On a weekend the lot fills by 11am, so bike or walk in if you can."),
 ],
}

def block(items):
    rows = "".join(f'<div class="faq-i"><h3>{html.escape(q)}</h3><p>{html.escape(a)}</p></div>' for q, a in items)
    return (f'<section class="faq" id="faq" data-haps-faq><div class="lbl">Quick answers</div>'
            f'<h2>Common questions</h2>{rows}</section>\n\n')

def apply(slug, items):
    path = os.path.join(ROOT, "guides", slug, "index.html")
    doc = open(path, encoding="utf-8").read()
    doc = re.sub(r'<section class="faq" id="faq" data-haps-faq>.*?</section>\n\n', "", doc, flags=re.S)
    marker = '<div class="morelinks">'
    assert doc.count(marker) == 1, slug
    doc = doc.replace(marker, block(items) + marker)
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', doc, re.S)
    data = json.loads(m.group(2))
    graph = [n for n in data["@graph"] if n.get("@type") != "FAQPage"]
    graph.append({"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]})
    data["@graph"] = graph
    doc = doc[:m.start(2)] + json.dumps(data, ensure_ascii=False) + doc[m.end(2):]
    open(path, "w", encoding="utf-8").write(doc)

if __name__ == "__main__":
    for slug, items in FAQ.items():
        apply(slug, items)
    print(f"faq: {len(FAQ)} guides")
