"""
Spa Time content — single source for seed-store.py and sync-content.py.

Sources (Downloads/spa-time specs etc):
  Spa_Time_Modelspecificaties.pdf   model specs and tier equipment
  Uitleg lijnen.docx                tier texts, "ideaal voor" and comparison table
"""

SPECS_NOTE = ('Comfort, Premium en Signature delen dezelfde basis van het gekozen model. '
              'Specificaties kunnen bij definitieve productie technisch worden verfijnd; de orderbevestiging is leidend.')

SHARED_SPECS = [
    ('Circulatie', '1 x 0,5 HP circulatiepomp'),
    ('Voeding', '220V / 50Hz of 380V / 50Hz'),
    ('Verwarming', '3 kW Balboa'),
]
CONSTRUCTION = [
    ('Waterbehandeling', 'UV-desinfectie met RVS behuizing'),
    ('Constructie', '8 mm Aristech acryl, RVS ondersteuningsframe en ABS bodemplaat'),
]


def specs(size, litres, weight, jets, massage, leds, headrests):
    return ([('Afmetingen', size), ('Waterinhoud', litres), ('Leeggewicht', weight), ('Aantal jets', jets),
             ('Massage', massage)] + SHARED_SPECS +
            [('Verlichting', leds), ('Hoofdsteunen', headrests)] + CONSTRUCTION)


TIERS = [
    ('comfort', {
        'name': 'Comfort', 'subtitle': 'Essentiële luxe', 'icon': 'diamond', 'featured': 'false',
        'short_description': 'Alles wat je nodig hebt voor optimaal ontspannen.',
        'description': "De Comfort-uitvoering biedt de complete Spa Time-ervaring zonder onnodige extra's. "
                       'Een comfortabele jacuzzi met hoogwaardige afwerking, krachtige massage en alle essentiële '
                       'functies voor jarenlang ontspannen.',
        'features': ['Balboa-besturing met TP500S-bediening', 'Kuipisolatie 25 mm', 'Bluetooth-audiosysteem',
                     'UV-waterdesinfectie', 'LED Spa Time-logo en hoekverlichting'],
        'ideal_for': 'Wie vooral zoekt naar kwaliteit en comfort voor een aantrekkelijke prijs.', 'ideal_icon': 'users',
    }),
    ('premium', {
        'name': 'Premium', 'subtitle': 'Extra comfort', 'icon': 'steam', 'featured': 'true',
        'short_description': 'Onze populairste keuze met extra massagekracht en luxe afwerking.',
        'description': 'De Premium-uitvoering tilt de ervaring naar een hoger niveau. Geniet van extra massagekracht, '
                       'het luxe Balboa SpaTouch-touchscreen, uitgebreide sfeerverlichting en verbeterde isolatie. '
                       'De beste balans tussen luxe, prestaties en prijs.',
        'features': ['Alles van Comfort', 'SpaTouch 4-touchscreen', 'Extra krachtige hydrotherapie',
                     'Extra dikke kuipisolatie (45 mm)', 'Bluetooth-audio met 6,5 inch speakers',
                     'LED-verlichting op alle vier de hoeken'],
        'ideal_for': 'Wie nét dat beetje extra luxe en comfort zoekt zonder direct voor de duurste uitvoering te gaan.',
        'ideal_icon': 'crown',
    }),
    ('signature', {
        'name': 'Signature', 'subtitle': 'Ultieme luxe', 'icon': 'star', 'featured': 'false',
        'short_description': 'De ultieme wellnesservaring met maximale isolatie en exclusieve afwerking.',
        'description': 'De Signature is onze meest complete uitvoering. Je krijgt alle luxe van Premium, aangevuld met '
                       'maximale isolatie, een extra geïsoleerde bodem en exclusieve afwerkingsdetails.',
        'features': ['Alles van Premium', 'Extra geïsoleerde bodemplaat', 'Extra 25 mm frame-isolatie',
                     'Volledige LED-strip rondom de omkasting'],
        'ideal_for': 'Wie alleen genoegen neemt met de meest complete Spa Time-uitvoering.', 'ideal_icon': 'diamond',
    }),
]

MODELS = [
    {'title': 'Ibiza', 'handle': 'ibiza', 'persons': 3, 'subtitle': '3-persoons jacuzzi',
     'tagline': 'Compact genieten zonder in te leveren op comfort.',
     'description': '<p>De Ibiza bewijst dat compact en luxe prima samengaan. Ideaal voor stellen of een kleinere tuin, zonder in te leveren op massagekracht.</p>',
     'prices': {'Comfort': 6500, 'Premium': 7500, 'Signature': 8700},
     'why_heading': 'Compact.\nKrachtig.\nVolledig uitgerust.',
     'why_text': 'De Ibiza bewijst dat compact en luxe prima samengaan. Ideaal voor stellen of een kleinere tuin, zonder in te leveren op massagekracht.',
     'highlights': ['Ruimte voor drie personen', '31 massagejets', '3 HP massagepomp', '22 LED-lampen rondom', 'Twee comfortabele hoofdsteunen'],
     'key_specs': [('users', '3', 'personen'), ('gear', '31', 'massagejets'), ('bolt', '1 × 3 HP', 'massagepomp'),
                   ('steam', '3 kW', 'Balboa-verwarming'), ('drop', '950 liter', 'waterinhoud')],
     'specs': specs('200 x 160 x 88 cm', '950 liter', '280 kg', '31', '1 x 3 HP massagepomp', '22 perimeter LED-lampen', '2 hoofdsteunen'),
     'size': (200, 160)},
    {'title': 'Bali', 'handle': 'bali', 'persons': 5, 'subtitle': '5-persoons jacuzzi',
     'tagline': 'Ruimte en krachtige massage voor de ultieme ontspanning.',
     'description': '<p>De Bali is onze allrounder: ruim genoeg voor het hele gezin, compact genoeg voor bijna elke tuin.</p>',
     'prices': {'Comfort': 6500, 'Premium': 7999, 'Signature': 9900},
     'why_heading': 'Ruimte voor vijf.\nKrachtige massage.\nNiet onnodig groot.',
     'why_text': 'De Bali biedt de perfecte balans tussen ruimte, comfort en krachtige massage. Vijf comfortabele zitplaatsen, een aantal met diepwerkende massagejets, zorgen ervoor dat iedereen zijn favoriete plek vindt.',
     'highlights': ['Ruimte voor vijf personen', '42 massagejets', 'Twee massagepompen van 2 HP', '25 LED-lampen rondom', 'Drie comfortabele hoofdsteunen'],
     'key_specs': [('users', '5', 'personen'), ('gear', '42', 'massagejets'), ('bolt', '2 × 2 HP', 'massagepompen'),
                   ('steam', '3 kW', 'Balboa-verwarming'), ('drop', '1.030 liter', 'waterinhoud')],
     'specs': specs('210 x 200 x 90 cm', '1.030 liter', '350 kg', '42', '2 x 2 HP massagepompen', '25 perimeter LED-lampen', '3 hoofdsteunen'),
     'size': (210, 200)},
    {'title': 'Marbella', 'handle': 'marbella', 'persons': 6, 'subtitle': '6-persoons jacuzzi',
     'tagline': 'Maximale ruimte en comfort voor het hele gezelschap.',
     'description': '<p>De Marbella combineert luxe, kracht en comfort. Het ideale model om het hele jaar door te genieten met familie en vrienden, in je eigen tuin.</p>',
     'prices': {'Comfort': 9900, 'Premium': 11400, 'Signature': 12900},
     'why_heading': 'Ruimte voor zes.\nMaximaal comfort.\nVoor het hele gezelschap.',
     'why_text': 'De Marbella combineert luxe, kracht en comfort. Met ruimte voor zes personen het ideale model om het hele jaar door te genieten met familie en vrienden.',
     'highlights': ['Ruimte voor zes personen', '42 massagejets', 'Twee massagepompen van 2 HP', '21 LED-lampen rondom', 'Drie comfortabele hoofdsteunen'],
     'key_specs': [('users', '6', 'personen'), ('gear', '42', 'massagejets'), ('bolt', '2 × 2 HP', 'massagepompen'),
                   ('steam', '3 kW', 'Balboa-verwarming'), ('drop', '1.030 liter', 'waterinhoud')],
     'specs': specs('200 x 200 x 90 cm', '1.030 liter', '350 kg', '42', '2 x 2 HP massagepompen', '21 perimeter LED-lampen', '3 hoofdsteunen'),
     'size': (200, 200)},
]
