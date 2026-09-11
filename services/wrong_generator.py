import random
import re
from services import llm

STOPWORDS = {
    "what", "when", "where", "who", "why", "how", "the", "is", "was",
    "are", "were", "did", "does", "do", "a", "an", "of", "in", "on",
    "at", "to", "for", "with", "and", "or", "it", "its", "this", "that",
    "tell", "me", "about", "can", "you", "please", "give", "explain",
    "many", "much", "some", "any", "there", "was", "were", "been",
}

UNRELATED_FACTS = [
    {"title": "The first pizza margherita was baked in 1889",
     "snippet": "Created in Naples for Queen Margherita of Savoy, the iconic pizza used tomato, mozzarella, and basil to represent the Italian flag."},
    {"title": "Honey never spoils",
     "snippet": "Archaeologists have found 3,000-year-old honey in Egyptian tombs that was still perfectly edible."},
    {"title": "Bananas are berries, but strawberries aren't",
     "snippet": "Botanically, bananas qualify as berries while strawberries are aggregate accessory fruits."},
    {"title": "The sandwich is named after the Earl of Sandwich",
     "snippet": "In 1762, John Montagu asked for meat between two slices of bread so he could keep playing cards."},
    {"title": "Instant noodles were invented in 1958",
     "snippet": "Momofuku Ando created them after seeing people queue for food in post-war Japan."},
    {"title": "Chocolate was once used as currency",
     "snippet": "The Aztecs used cacao beans as money — a rabbit cost about 10 beans."},
    {"title": "Carrots were originally purple",
     "snippet": "Orange carrots were bred by Dutch farmers in the 17th century to honor the House of Orange."},
    {"title": "Pineapples take two years to grow",
     "snippet": "Each pineapple plant produces only one fruit, and it takes 18-24 months to mature."},
    {"title": "Basketball was invented in 1891",
     "snippet": "James Naismith invented the game using a soccer ball and two peach baskets nailed to a gymnasium wall."},
    {"title": "The Olympic Games were banned for 1,500 years",
     "snippet": "Emperor Theodosius I abolished the ancient Olympics in 393 AD. They didn't return until 1896."},
    {"title": "The first marathon was run in 490 BC",
     "snippet": "A Greek messenger ran 26 miles from Marathon to Athens to announce a military victory, then collapsed."},
    {"title": "Tennis was invented by French monks",
     "snippet": "Medieval monks played a handball game called 'jeu de paume' that evolved into modern tennis."},
    {"title": "Modern golf was invented in Scotland",
     "snippet": "The first written rules of golf were drafted in Edinburgh in 1744."},
    {"title": "Sumo wrestling is over 2,000 years old",
     "snippet": "The sport is mentioned in Japanese texts from the 3rd century AD and was originally a religious ritual."},
    {"title": "Figure skating is the oldest Winter Olympic sport",
     "snippet": "It appeared in the 1908 Summer Olympics before the Winter Games even existed."},
    {"title": "Beethoven composed his 9th Symphony while deaf",
     "snippet": "By the time of its 1824 premiere, Beethoven could not hear the thunderous applause that followed."},
    {"title": "The shortest song ever recorded is 1.316 seconds long",
     "snippet": "Napalm Death's 'You Suffer' holds the record for the shortest commercially released song."},
    {"title": "Mozart wrote his first symphony at age 8",
     "snippet": "He composed Symphony No. 1 in E-flat major in 1764 during a family tour of London."},
    {"title": "The Beatles never learned to read music",
     "snippet": "None of the four Beatles could read musical notation. They composed entirely by ear."},
    {"title": "The guitar has six strings — but that's modern",
     "snippet": "Earlier guitars had four, five, or even ten strings depending on the era and region."},
    {"title": "The piano has over 12,000 parts",
     "snippet": "A grand piano contains about 12,000 individual components, and about 10,000 of them are moving."},
    {"title": "A hummingbird's heart beats 1,200 times per minute",
     "snippet": "During flight, hummingbirds have the highest metabolism of any animal."},
    {"title": "Octopuses have three hearts",
     "snippet": "Two pump blood to the gills and one to the rest of the body. The main heart stops when they swim."},
    {"title": "Cows have best friends",
     "snippet": "Studies show cows experience less stress when housed with their preferred companions."},
    {"title": "Wombat poop is cube-shaped",
     "snippet": "Wombats produce cube-shaped droppings to mark territory without rolling off rocks."},
    {"title": "Butterflies taste with their feet",
     "snippet": "Receptors on their feet let them taste leaves before laying eggs on them."},
    {"title": "Snails can sleep for up to 3 years",
     "snippet": "During dry seasons, some snails seal themselves in their shells and enter a dormant state."},
    {"title": "Elephants are the only animals that can't jump",
     "snippet": "Their weight and bone structure make it impossible for all four feet to leave the ground at once."},
    {"title": "A group of flamingos is called a flamboyance",
     "snippet": "Other collective nouns include a 'parliament' of owls and a 'murder' of crows."},
    {"title": "Sea otters hold hands while sleeping",
     "snippet": "They link paws to avoid drifting apart in the water."},
    {"title": "Sloths can hold their breath longer than dolphins",
     "snippet": "Sloths can slow their heart rate and hold their breath for up to 40 minutes."},
    {"title": "There are more stars than grains of sand on Earth",
     "snippet": "The observable universe contains roughly 200 sextillion stars."},
    {"title": "A day on Venus is longer than a year on Venus",
     "snippet": "Venus takes 243 Earth days to rotate once but only 225 to orbit the Sun."},
    {"title": "Neil Armstrong's spacesuit was hand-sewn",
     "snippet": "The Apollo 11 suit was assembled by seamstresses at ILC Dover using 21 layers of fabric."},
    {"title": "A teaspoon of neutron star weighs a billion tons",
     "snippet": "Neutron stars are so dense that a single teaspoon of their material would weigh more than Mount Everest."},
    {"title": "The Milky Way is 100,000 light-years across",
     "snippet": "It contains over 100 billion stars and takes 250 million years to complete one rotation."},
    {"title": "Saturn would float in water",
     "snippet": "Its density is lower than water — it would bob on the surface of a big enough ocean."},
    {"title": "Space smells like seared steak",
     "snippet": "Astronauts report that the vacuum of space leaves a metallic, smoky smell on their suits."},
    {"title": "Cleopatra lived closer to the moon landing than the building of the pyramids",
     "snippet": "The Great Pyramid was built around 2560 BC. Cleopatra ruled 51-30 BC. The moon landing was 1969."},
    {"title": "Oxford University is older than the Aztec Empire",
     "snippet": "Teaching at Oxford began around 1096. Tenochtitlan was founded in 1325."},
    {"title": "Napoleon was average height for his time",
     "snippet": "He stood about 5'6\" — the 'short Napoleon' myth came from British propaganda."},
    {"title": "Vikings never wore horned helmets",
     "snippet": "The horned helmet is a 19th-century opera costume invention."},
    {"title": "The Hundred Years' War lasted 116 years",
     "snippet": "It ran from 1337 to 1453 — 116 years, not 100."},
    {"title": "The shortest war in history lasted 38 minutes",
     "snippet": "The Anglo-Zanzibar War of 1896 ended in under 40 minutes."},
    {"title": "The Titanic had four smokestacks but only three worked",
     "snippet": "The fourth was added purely for visual symmetry."},
    {"title": "Nintendo was founded in 1889",
     "snippet": "It started as a playing card company before pivoting to video games almost a century later."},
    {"title": "The Mona Lisa has no eyebrows",
     "snippet": "Renaissance fashion favored shaved eyebrows. Da Vinci painted the portrait between 1503 and 1519."},
    {"title": "Van Gogh sold only one painting in his lifetime",
     "snippet": "'The Red Vineyard' sold in 1890 for 400 francs."},
    {"title": "The Scream has been stolen twice",
     "snippet": "Thieves took Edvard Munch's painting from a Norwegian museum in 1994 and again in 2004."},
    {"title": "Michelangelo's David was carved from a rejected block",
     "snippet": "The marble had been discarded by two other sculptors before Michelangelo took it on."},
    {"title": "The first computer bug was a literal moth",
     "snippet": "In 1947, engineers at Harvard found a moth trapped in a relay of the Mark II computer."},
    {"title": "Apollo 11's computer ran at 0.043 MHz",
     "snippet": "Your phone has roughly 100,000 times more processing power than the guidance computer that landed on the moon."},
    {"title": "The first webcam watched a coffee pot",
     "snippet": "Researchers at Cambridge set up a camera in 1991 to check if the coffee pot was empty without leaving their desks."},
    {"title": "Email predates the World Wide Web by 20 years",
     "snippet": "The first email was sent in 1971. The Web was invented in 1989."},
    {"title": "The first domain ever registered was symbolics.com",
     "snippet": "Registered on March 15, 1985, it's still active today."},
    {"title": "QWERTY was designed to slow typists down",
     "snippet": "The layout was created in the 1870s to prevent mechanical typewriter jams."},
    {"title": "The first text message said 'Merry Christmas'",
     "snippet": "Sent on December 3, 1992, by Neil Papworth in the UK."},
    {"title": "Lightning strikes Earth about 100 times per second",
     "snippet": "Approximately 8 million lightning strikes occur globally every day."},
    {"title": "An average cumulus cloud weighs over a million pounds",
     "snippet": "It holds thousands of tons of water droplets but stays aloft because of low density."},
    {"title": "Snowflakes always have six sides",
     "snippet": "The molecular structure of ice forces water to crystallize in hexagonal patterns."},
    {"title": "Rainbows are actually full circles",
     "snippet": "From the ground we only see half — from an airplane you can see the whole circle."},
    {"title": "The word 'set' has 430 definitions",
     "snippet": "The Oxford English Dictionary lists 430 distinct meanings — more than any other English word."},
    {"title": "'I am' is the shortest complete sentence",
     "snippet": "It has a subject and a verb and expresses a complete thought."},
    {"title": "'Uncopyrightable' is the longest English word with no repeated letters",
     "snippet": "15 letters, all unique."},
    {"title": "'Dreamt' is the only common English word ending in 'mt'",
     "snippet": "All other 'mt' words are rare or archaic."},
    {"title": "Scotland's national animal is the unicorn",
     "snippet": "The unicorn has been a symbol of Scotland since the 12th century."},
    {"title": "Sharks are older than trees",
     "snippet": "Sharks have existed for about 450 million years. Trees appeared around 350 million years ago."},
    {"title": "A day on Jupiter is only 9.9 hours",
     "snippet": "Jupiter spins faster than any other planet in our solar system."},
    {"title": "The Eiffel Tower can grow 15 cm taller in summer",
     "snippet": "Thermal expansion causes the iron to expand in hot weather."},
    {"title": "Your body contains enough carbon to make 9,000 pencils",
     "snippet": "Carbon makes up about 18% of human body mass."},
    {"title": "Bubble wrap was invented as wallpaper",
     "snippet": "It flopped as wallpaper in 1957 and was rebranded as packaging."},
    {"title": "The wedding ring is worn on the fourth finger because of an old myth",
     "snippet": "Ancient Romans believed a vein ran directly from that finger to the heart."},
    {"title": "Your stomach gets a new lining every three days",
     "snippet": "Otherwise the acid would digest your own stomach."},
    {"title": "A cloud can weigh more than an airplane",
     "snippet": "A cumulus cloud can weigh about 1.1 million pounds."},
    {"title": "The longest hiccuping spasm lasted 68 years",
     "snippet": "Charles Osborne hiccuped from 1922 to 1990 — about 430 million times."},
]

def _subject_words(query):
    words = re.findall(r"[a-zA-Z]{3,}", query.lower())
    return set(w for w in words if w not in STOPWORDS)

def _filter_unrelated(query, pool):
    subject = _subject_words(query)
    safe = []
    for fact in pool:
        text = (fact["title"] + " " + fact["snippet"]).lower()
        if any(sw in text for sw in subject):
            continue
        safe.append(fact)
    if len(safe) < 5:
        return pool
    return safe

def generate(query, n=5):
    llm_answers = llm.generate(query, n)
    if llm_answers:
        subject = _subject_words(query)
        clean = []
        for a in llm_answers:
            text = (a["title"] + " " + a["snippet"]).lower()
            if any(sw in text for sw in subject):
                continue
            clean.append(a)
        if len(clean) >= 3:
            return clean[:n], "llm"
    pool = _filter_unrelated(query, UNRELATED_FACTS)
    random.shuffle(pool)
    return [{"title": f["title"], "snippet": f["snippet"]} for f in pool[:n]], "unrelated"
