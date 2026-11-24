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

FAQ.update({
 "christmas-lights-los-angeles": [
  ("What are the best Christmas lights in Los Angeles?",
   "For a ticketed walk, Enchanted: Forest of Light at Descanso Gardens, about a mile under the oaks, Nov 22, 2026 to Jan 9, 2027. For free, Christmas Tree Lane in Altadena and Candy Cane Lane in Woodland Hills, plus the Marina del Rey Holiday Boat Parade on Saturday, Dec 12, 2026."),
  ("What are the best free Christmas lights in LA?",
   "Christmas Tree Lane in Altadena (lighting ceremony Sat Dec 5, 2026 at 6pm), Candy Cane Lane in Woodland Hills (lights 6-10pm from the first Saturday in December), the Marina del Rey Holiday Boat Parade (Sat Dec 12, 6-8pm) and The Grove's nightly snowfall at 6pm and 8pm."),
  ("How much is LA Zoo Lights?",
   "Tickets start at $19 and parking is free. It runs select nights from Nov 20, 2026 to Jan 10, 2027, and is dark on several nights including Dec 24, 25 and 31."),
  ("Is Christmas Tree Lane in Altadena happening after the Eaton fire?",
   "Yes. None of its cedars were lost, and the lighting ceremony is Saturday, Dec 5, 2026 at 6pm at Santa Rosa Ave and Mariposa St, with a free Winterfest craft fair from 3pm."),
  ("Is Holiday Road at King Gillette Ranch on this year?",
   "No. Holiday Road is taking 2026 off for projected El Niño weather and plans to return in 2027. The Naples Island boat parade in Long Beach is also cancelled this year."),
 ],
 "holiday-things-to-do-los-angeles": [
  ("Where can I ice skate outdoors in Los Angeles?",
   "Downtown at the Holiday Ice Rink in Pershing Square, daily Nov 12, 2026 to Jan 3, 2027, $23.32 with skates. On the Westside at Frost on 5th in Santa Monica, the old Ice at Santa Monica, $22 with skates."),
  ("Is the LA County Holiday Celebration still on Christmas Eve?",
   "Not in person. This year it is on Sunday, Dec 20, 2026 at the Dorothy Chandler Pavilion, with free shows at 11am and 3pm. Reservations open at 10am on Dec 8, 9 and 10. It still airs on PBS SoCal on Christmas Eve at 3pm."),
  ("Where can I see The Nutcracker in LA?",
   "Los Angeles Ballet plays Royce Hall Dec 11-13 and the Dolby Theatre Dec 18-27 with a live orchestra, including a 2pm Christmas Eve matinee. American Contemporary Ballet's Nutcracker Suite runs Nov 28 to Dec 24 downtown."),
  ("When is the Messiah Sing-Along at Disney Hall?",
   "The LA Master Chorale's Great Messiah Sing-Along is Sunday, Dec 20, 2026 at 7pm at Walt Disney Concert Hall. The LA Phil's lighter Holiday Sing-Along is Saturday, Dec 19 at 11:30am and 2:30pm."),
  ("What is open in LA on Christmas Eve?",
   "The Pershing Square rink is open noon to 10pm from Dec 21 through Jan 3. LA Ballet has a 2pm Nutcracker matinee at the Dolby on Dec 24, and A Noise Within's A Christmas Carol closes that day at 2pm."),
 ],
 "new-years-eve-los-angeles": [
  ("What free New Year's Eve events are there in Los Angeles?",
   "NYELA at Gloria Molina Grand Park downtown, 8pm to 1am on Dec 31, 2026, free with no ticket. On the Westside, the Marina del Rey Fireworks and Glow Party at Burton Chace Park, 7pm to midnight, free with an RSVP."),
  ("Where can I watch fireworks in LA on New Year's Eve?",
   "Marina del Rey's free fireworks launch from the south jetty at 11:59pm and are visible across most of the marina. In Long Beach, the Queen Mary puts on fifteen minutes of midnight fireworks over the harbor."),
  ("When is the Rose Parade 2027?",
   "Friday, Jan 1, 2027, from 8am to about 10am on a 5.5-mile route in Pasadena, mostly along Colorado Boulevard. Watching from the curb is free; overnight street parking opens at noon on Dec 31."),
  ("Is LA Metro free on New Year's Eve?",
   "Not announced yet for this year. Last year Metro ran free fares and kept several rail lines running all night, so check metro.net in the last week of December."),
  ("Is there a New Year's Eve concert in Los Angeles?",
   "The LA Phil presents A Yacht Rock NYE with Christopher Cross at Walt Disney Concert Hall on Dec 31, 2026 from 7pm. Tickets start at $101 and the first 350 guests get champagne."),
 ],
 "date-ideas-los-angeles": [
  ("What is a good first date in Los Angeles?",
   "Something short, cheap and easy to extend: the Hammer Museum in Westwood is free, needs no reservation and takes about an hour, and Westwood has plenty of places to keep talking afterwards."),
  ("What are free date ideas in LA?",
   "Griffith Observatory at night (free, open until 10pm Tuesday to Sunday), The Broad and the Hammer (both free), the free self-guided tour of Walt Disney Concert Hall, and the Getty, which is free with a timed reservation."),
  ("What are romantic things to do in LA at night?",
   "Griffith Observatory's lawn over the city lights, the Getty on a Saturday when it stays open until 9pm, a sunset trail ride at Sunset Ranch Hollywood, or a jazz set at Sam First or Catalina Jazz Club."),
  ("What are good rainy day date ideas in Los Angeles?",
   "A double feature on film at the New Beverly, Vidiots in Eagle Rock, bowling at Highland Park Bowl, the Academy Museum after 4:30pm for $18, or The Last Bookstore, open until 11pm Wednesday to Saturday."),
  ("Where can you see comedy on a date in LA?",
   "Largo at the Coronet on La Cienega: most shows are $40, no phones, doors at 7pm and the show at 8pm."),
 ],
 "meet-people-los-angeles": [
  ("How do you make friends in Los Angeles as an adult?",
   "Pick one thing that happens every week and keep going back. LA is spread out, so chance meetings are rare; repetition is what turns faces into names. A free weekly run club, a six-week class or a monthly volunteer shift all work."),
  ("What are the best run clubs in LA?",
   "Koreatown Run Club (Mondays 7pm and Thursdays 8pm, no sign-up), Silver Lake Track Club (Tuesdays 7pm around the reservoir, free) and, on the Westside, the Los Angeles Running Club's Monday evening run from Playa Vista."),
  ("Can I join a sports league in LA by myself?",
   "Yes. Volo Sports lets you sign up as a free agent and places you on a team, with leagues in Santa Monica, Venice, Mar Vista, Culver City, WeHo and more, at $95 to $165 a season."),
  ("How do I have dinner with strangers in LA?",
   "Haps Club hosts long-table dinners, with seats going to newsletter readers first. Timeleft matches four to six strangers for dinner on Wednesdays and Fridays at 7pm, at $19.99 a ticket plus your own meal."),
  ("Where can I meet people in LA without an app?",
   "Volunteer with Big Sunday, Heal the Bay or TreePeople, take a beginner improv class at the Groundlings, go to the Saturday swing dance in Pasadena (lesson included, no partner needed), or join a book club at Skylight Books."),
 ],
})

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
