class WordList(object):
    def __init__(self, short_name, description, easy=[], medium=[], hard=[],
                 impossible=[]):
        self.word_list = {
            'easy': easy,
            'medium': medium,
            'hard': hard,
            'impossible': impossible,
        }
        self.description = description
        self.short_name = short_name


WORDLISTS = {
    'space': WordList(
        short_name='Space',
        description='Space-related words',
        easy=[
            'Apollo',
            'The',
            'Moon',
            'The',
            'Sun',
            'Venus',
            'Pluto',
            'Mars',
            'Earth',
            'Mercury',
            'Jupiter',
            'Saturn',
            'Uranus',
            'Neptune',
            'Planet',
            'Space',
            'Star'
        ],
        medium=[
            'Alien',
            'Alpha',
            'Centauri',
            'Asteroid',
            'Astronaut',
            'Astronomy',
            'Big',
            'Bang',
            'Theory',
            'Black',
            'Hole',
            'Buzz',
            'Aldrin',
            'Ceres',
            'Comet',
            'Constellation',
            'Cosmonaut',
            'Crater',
            'Curiosity',
            'Rover',
            'Eclipse',
            "Elon's",
            'Red',
            'Tesla',
            'Roadster',
            'Event',
            'Horizon',
            'Galaxy',
            'Gas',
            'Giant',
            'Gravity',
            'Hubble',
            'Telescope',
            'International',
            'Space',
            'Station',
            'Laika',
            '(First',
            'dog',
            'in',
            'space)',
            'Lightyear',
            'Meteor',
            'Milky',
            'Way',
            'Mercury',
            'NASA',
            'Nebula',
            'Neil',
            'Armstrong',
            'Orbit',
            'Parsec',
            'Pulsar',
            'Quasar',
            'Red',
            'Dwarf',
            'Red',
            'Giant',
            'Red',
            'Shift',
            'Rocket',
            'Satellite',
            'Solar',
            'Flare',
            'Solar',
            'System',
            'Sputnik',
            'Supernova',
            'Telescope',
            'Titan',
            'Universe',
            'White',
            'Dwarf',
            'Wormhole',
            'Yellow',
            'Dwarf',
            'Vacuum'
        ]),
    'default': WordList(
        short_name='Default',
        description='Generic Words',
        easy=[
            'actor',
            'adult',
            'airplane',
            'alarm clock',
            'alive',
            'ankle',
            'apple',
            'astronaut',
            'awake',
            'baby',
            'backpack',
            'bald',
            'balloon',
            'banana',
            'bark',
            'baseball',
            'basketball',
            'bat',
            'bathroom',
            'beach',
            'beak',
            'bed',
            'bedtime',
            'below',
            'bench',
            'big',
            'bite',
            'black',
            'blanket',
            'blind',
            'blue jeans',
            'boat',
            'book',
            'bounce',
            'bowl',
            'boy',
            'bracelet',
            'brake',
            'branch',
            'broccoli',
            'broken',
            'broom',
            'brother',
            'bug',
            'bumblebee',
            'butterfly',
            'button',
            'buy',
            'calculator',
            'camera',
            'car',
            'chair',
            'cheek',
            'chocolate',
            'Christmas',
            'circle',
            'city',
            'clap',
            'classroom',
            'clean',
            'cold',
            'comb',
            'corn',
            'count',
            'cousin',
            'crack',
            'crib',
            'cube',
            'cup',
            'cupcake',
            'curl',
            'dad',
            'dance',
            'deep',
            'diamond',
            'dirt',
            'dog',
            'door',
            'dream',
            'drum',
            'duck',
            'egg',
            'elephant',
            'envelope',
            'exercise',
            'eye',
            'fact',
            'fall',
            'family',
            'farm',
            'feet',
            'fire',
            'first',
            'fish',
            'flashlight',
            'flower',
            'fly',
            'football',
            'forehead',
            'fork',
            'fountain',
            'frog',
            'frown',
            'frying pan',
            'full',
            'fur',
            'gift',
            'giraffe',
            'glasses',
            'grape',
            'gum',
            'gym',
            'hair',
            'half',
            'hamburger',
            'hand',
            'happy',
            'heavy',
            'helicopter',
            'help',
            'hit',
            'homework',
            'hook',
            'horse',
            'hotel',
            'house',
            'ice cream cone',
            'Internet',
            'iron',
            'jacket',
            'jail',
            'jar',
            'jellyfish',
            'juice',
            'king',
            'kite',
            'lamp',
            'leaf',
            'legs',
            'lightning',
            'lime',
            'line',
            'lion',
            'lizard',
            'long',
            'loud',
            'love',
            'low',
            'lunchbox',
            'lung',
            'mailbox',
            'mailman',
            'melt',
            'Mickey Mouse',
            'milk',
            'mitten',
            'moo',
            'moon',
            'mountains',
            'mouth',
            'music',
            'nail polish',
            'neighbor',
            'nest',
            'nice',
            'notebook',
            'old',
            'owl',
            'pantry',
            'party',
            'pencil',
            'person',
            'picture',
            'pig',
            'pillow',
            'play',
            'policeman',
            'popsicle',
            'purple',
            'purse',
            'quiet',
            'rainbow',
            'ranch',
            'refrigerator',
            'restaurant',
            'rhyme',
            'ride',
            'river',
            'road',
            'rock',
            'rocket',
            'roof',
            'room',
            'run',
            'school bus',
            'scientist',
            'sea',
            'seashell',
            'sea turtle',
            'share',
            'shark',
            'ship',
            'shoe',
            'shopping',
            'shower',
            'sink',
            'skateboard',
            'sleep',
            'smell',
            'smile',
            'snail',
            'snake',
            'soap',
            'sock',
            'socks',
            'square',
            'stamp',
            'stapler',
            'star',
            'stick',
            'stomach',
            'stream',
            'street',
            'study',
            'suitcase',
            'sun',
            'swimming pool',
            'swing',
            'table',
            'tail',
            'tent',
            'thunder',
            'tissue',
            'touchdown',
            'towel',
            'tractor',
            'train',
            'tree',
            'trip',
            'truck',
            'turtle',
            'TV',
            'umbrella',
            'vacation',
            'waitress',
            'watch',
            'wave',
            'wind',
            'wrinkle',
            'yellow',
            'yo-yo',
            'zero',
            'zigzag',
        ],
        medium=[
            'acne',
            'air',
            'astronaut',
            'attic',
            'baby-sitter',
            'bait',
            'ballpoint pen',
            'banister',
            'baseboards',
            'bass',
            'believe',
            'birthday',
            'bite',
            'blanket',
            'blossom',
            'bobsled',
            'boil',
            'bonnet',
            'brass',
            'brick',
            'bubble',
            'budget',
            'bump',
            'bunk bed',
            'button',
            'cage',
            'calorie',
            'camp',
            'campsite',
            'candlestick',
            'career',
            'caribou',
            'cartographer',
            'cartoon',
            'cell',
            'chauffeur',
            'church',
            'classroom',
            'cloud',
            'coupon',
            'crumb',
            'curb',
            'currency',
            'curtains',
            'date',
            'decide',
            'delay',
            'departure',
            'dirt',
            'dragonfly',
            'drums',
            'earache',
            'easel',
            'elf',
            'envious',
            'experiment',
            'face',
            'family reunion',
            'fine',
            'friend',
            'gasoline',
            'glue stick',
            'goblin',
            'gold',
            'gumball',
            'healthy',
            'heel',
            'hide-and-seek',
            'hike',
            'hip',
            'hoedown',
            'home movies',
            'hook',
            'hotel',
            'hug',
            'hurdle',
            'infant',
            'ironing board',
            'jog',
            'joyful',
            'judgmental',
            'knight',
            'lamp',
            'leak',
            'leotard',
            'linen',
            'lip',
            'log',
            'lunch tray',
            'magnet',
            'map',
            'mast',
            'matchstick',
            'mold',
            'mom',
            'mop',
            'motel',
            'mountain',
            'mountain biking',
            'nail',
            'net',
            'nitrogen',
            'oak tree',
            'observe',
            'operation',
            'order',
            'park',
            'pharmacy',
            'photograph',
            'ping pong',
            'plane',
            'pogo stick',
            'porch swing',
            'poster',
            'predator',
            'pride',
            'produce',
            'puppet',
            'quicksand',
            'quill',
            'race',
            'railroad',
            'rake',
            'rattle',
            'rebound',
            'recycle',
            'reign',
            'ribbon',
            'rind',
            'road trip',
            'robin',
            'rug',
            'rut',
            'safari',
            'sandpaper',
            'seesaw',
            'senior',
            'sense',
            'sentence',
            'shack',
            'shed',
            'sheet',
            'shrimp',
            'sideline',
            'silver',
            'silverware',
            'sin',
            'skull',
            'slam dunk',
            'slide',
            'smog',
            'smoke',
            'snack',
            'snowball',
            'sod',
            'soil',
            'son',
            'spaceship',
            'spouse',
            'spring',
            'spy',
            'squint',
            'stage',
            'stairs',
            'stapler',
            'state',
            'stationery',
            'steel',
            'stepmom',
            'stream',
            'stripe',
            'sun block',
            'sunshine',
            'swing',
            'tailor',
            'tank',
            'taxi',
            'teammate',
            'teenager',
            'think',
            'thread',
            'tiptoe',
            'toad',
            'toddler',
            'tool',
            'top hat',
            'trailer',
            'transport',
            'trash can',
            'tulip',
            'twig',
            'usher',
            'veil',
            'vent',
            'waist',
            'wallet',
            'waste',
            'waves',
            'weed',
            'wick',
            'Windex',
            'word',
            'writer',
            'x-ray',
            'yam',
        ],
        hard=[
            'abrasive',
            'actuary',
            'admit',
            'agenda',
            'airway',
            'altitude',
            'amateur',
            'application',
            'audacity',
            'ballpoint pen',
            'banana peel',
            'baron',
            'battle',
            'bay',
            'bedbug',
            'beehive',
            'bellhop',
            'blimp',
            'blur',
            'bonnet',
            'brand',
            'brass',
            'breakdance',
            'bucket',
            'campsite',
            'capitalism',
            'capybara',
            'chain',
            'chicken coop',
            'clay',
            'cloak',
            'coast',
            'confused',
            'crime',
            'crop',
            "crow's nest",
            'cuff',
            'cupola',
            'cure',
            'dawn',
            'degree',
            'demo',
            'deployed',
            'dimple',
            'diver',
            'divine',
            'dress shirt',
            'dust bunny',
            'ebony and ivory',
            'eternity',
            'example',
            'exhort',
            'fabric',
            'feudalism',
            'fizz',
            'flu',
            'flush',
            'forever',
            'fortnight',
            'fourth down',
            'freight train',
            'fringe',
            'full moon',
            'Galapagos tortoise',
            'game clock',
            'garden hose',
            'gem',
            'genetics',
            'glum',
            'gray hairs',
            'group',
            'gusto',
            'hardhearted',
            'hatch',
            'help',
            'highjack',
            'highway',
            'hole in one',
            'humidifier',
            'image',
            'immune',
            'incident',
            'insist',
            'intern',
            'irritated',
            'jade',
            'jazz',
            'jog',
            'jug',
            'jury',
            'kiosk',
            'ladder rung',
            'laundry basket',
            'lecture',
            'leisure',
            'livestock',
            'lollipop',
            'major league',
            'mascot',
            'mast',
            'maze',
            'midsummer',
            'modern',
            'moped',
            'motion',
            'multiplication',
            "Murphy's Law",
            'nanny',
            'nutrient',
            'oak tree',
            'observation',
            'organ',
            'outlet mall',
            'overhang',
            'password',
            'path',
            'payment',
            'perk',
            'person',
            'phonemics',
            'pinch',
            'pint',
            'plank',
            'plug',
            'pomp',
            'population',
            'porch swing',
            'position',
            'potassium',
            'premolar',
            'process',
            'program',
            'publisher',
            'purpose',
            'puzzle piece',
            'quality control',
            'quantum mechanics',
            'race',
            'radiation',
            'radiator',
            'range',
            'rendering',
            'research',
            'result',
            'rhetoric',
            'riddle',
            'romance',
            'runt',
            'rut',
            'safe',
            'sandbox',
            'sash',
            'scanner',
            'scar tissue',
            'scenery',
            'scoundrel',
            'scramble',
            'scuff mark',
            'scurvy',
            'scythe',
            'selection',
            'self',
            'sentence',
            'serve',
            'sheriff',
            'shipwreck',
            'shriek',
            'shrink ray',
            'sip',
            'sling',
            'smidgen',
            'snag',
            'snobbish',
            'snort',
            'snow shoe',
            'sod',
            'someone',
            'speakers',
            'speculate',
            'spoonful',
            'sports car',
            'standard',
            'standing ovation',
            'state fair',
            'station',
            'station wagon',
            'statistics',
            'step-daughter',
            'stipulate',
            'stockbroker',
            'structure',
            'suggestion',
            'sum',
            'sunglasses',
            'suspend',
            'sympathize',
            'tendency',
            'theorize',
            'thing',
            'thoughtless',
            'throb',
            'tine',
            'toboggan',
            'traffic jam',
            'train station',
            'tugboat',
            'tunic',
            'turnpike',
            'twitterpated',
            'underestimate',
            'urgent',
            'use',
            'voice',
            'wail',
            'waver',
            'way',
            'whole milk',
            'wish',
            'wreath',
            'zephyr',
        ]),
    'imdb_top_50_movies': WordList(
        short_name='Movies',
        description='IMDB top 50 movies',
        medium=[
            'The Shawshank Redemption',
            'The Godfather',
            'The Godfather: Part II',
            'The Dark Knight',
            '12 Angry Men',
            "Schindler's List",
            'Pulp Fiction',
            'The Good, the Bad and the Ugly',
            'The Lord of the Rings: The Return of the King',
            'Fight Club',
            'The Fellowship of the Ring',
            'The Empire Strikes Back',
            'Forrest Gump',
            'Inception',
            "One Flew Over the Cuckoo's Nest",
            'The Lord of the Rings: The Two Towers',
            'Goodfellas',
            'The Matrix',
            'Star Wars',
            'Seven Samurai',
            'City of God',
            'Se7en',
            'The Silence of the Lambs',
            'The Usual Suspects',
            "It's a Wonderful Life",
            'Life Is Beautiful',
            'Léon: The Professional',
            'Once Upon a Time in the West',
            'Interstellar',
            'Saving Private Ryan',
            'American History X',
            'Spirited Away',
            'Casablanca',
            'Raiders of the Lost Ark',
            'Psycho',
            'City Lights',
            'Rear Window',
            'The Intouchables',
            'Modern Times',
            'Terminator 2',
            'Whiplash',
            'The Green Mile',
            'The Pianist',
            'Memento',
            'The Departed',
            'Gladiator',
            'Apocalypse Now',
            'Back to the Future',
            'Sunset Blvd.',
            'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb',
            'The Prestige',
            'Alien',
            'The Lion King',
            'The Lives of Others',
            'The Great Dictator',
            'Inside Out',
            'Cinema Paradiso',
            'The Shining',
            'Paths of Glory',
            'Django Unchained',
            'The Dark Knight Rises',
            'WALL·E',
            'American Beauty',
            'Grave of the Fireflies',
            'Aliens',
            'Citizen Kane',
            'North by Northwest',
            'Princess Mononoke',
            'Vertigo',
            'Oldboy',
            'Das Boot',
            'Star Wars: Episode VI - Return of the Jedi',
            'Once Upon a Time in America',
            'Amélie',
            'Witness for the Prosecution',
            'Reservoir Dogs',
            'Braveheart',
            'Toy Story 3',
            'A Clockwork Orange',
            'Double Indemnity',
            'Taxi Driver',
            'Requiem for a Dream',
            'To Kill a Mockingbird',
            'Lawrence of Arabia',
            'Eternal Sunshine of the Spotless Mind',
            'Full Metal Jacket',
            'The Sting',
            'Amadeus',
            'Bicycle Thieves',
            "Singin' in the Rain",
            'Monty Python and the Holy Grail',
            'Snatch.',
            '2001: A Space Odyssey',
            'The Kid',
            'L.A. Confidential',
            'For a Few Dollars More',
            'Toy Story',
            'The Apartment',
            'Inglourious Basterds',
            'All About Eve',
            'The Treasure of the Sierra Madre',
            'Indiana Jones and the Last Crusade',
            'Metropolis',
            'Yojimbo',
            'The Third Man',
            'Batman Begins',
            'Scarface',
            'Some Like It Hot',
            'Unforgiven',
            '3 Idiots',
            'Up',
            'Raging Bull',
            'Downfall',
            'Mad Max: Fury Road',
            'Jagten',
            'Chinatown',
            'The Great Escape',
            'Die Hard',
            'Good Will Hunting',
            'Heat',
            'On the Waterfront',
            "Pan's Labyrinth",
            'Mr. Smith Goes to Washington',
            'The Bridge on the River Kwai',
            'My Neighbor Totoro',
            'Ran',
            'The Gold Rush',
            'Ikiru',
            'The Seventh Seal',
            'Blade Runner',
            'The Secret in Their Eyes',
            'Wild Strawberries',
            'The General',
            'Lock, Stock and Two Smoking Barrels',
            'The Elephant Man',
            'Casino',
            'The Wolf of Wall Street',
            "Howl's Moving Castle",
            'Warrior',
            'Gran Torino',
            'V for Vendetta',
            'The Big Lebowski',
            'Rebecca',
            'Judgment at Nuremberg',
            'A Beautiful Mind',
            'Cool Hand Luke',
            'The Deer Hunter',
            'How to Train Your Dragon',
            'Gone with the Wind',
            'Fargo',
            'Trainspotting',
            'It Happened One Night',
            'Dial M for Murder',
            'Into the Wild',
            'Gone Girl',
            'The Sixth Sense',
            'Rush',
            'Finding Nemo',
            'The Maltese Falcon',
            'Mary and Max',
            'No Country for Old Men',
            'The Thing',
            'Incendies',
            'Hotel Rwanda',
            'Kill Bill: Vol. 1',
            'Life of Brian',
            'Platoon',
            'The Wages of Fear',
            'Butch Cassidy and the Sundance Kid',
            'There Will Be Blood',
            'Network',
            'Touch of Evil',
            'The 400 Blows',
            'Stand by Me',
            '12 Years a Slave',
            'The Princess Bride',
            'Annie Hall',
            'Persona',
            'The Grand Budapest Hotel',
            'Amores Perros',
            'In the Name of the Father',
            'Million Dollar Baby',
            'Ben-Hur',
            'The Grapes of Wrath',
            "Hachi: A Dog's Tale",
            'Nausicaä of the Valley of the Wind',
            'Shutter Island',
            'Diabolique',
            'Sin City',
            'The Wizard of Oz',
            'Gandhi',
            'Stalker',
            'The Bourne Ultimatum',
            'The Best Years of Our Lives',
            'Donnie Darko',
            'Relatos salvajes',
            '8½',
            'Strangers on a Train',
            'Jurassic Park',
            'The Avengers',
            'Before Sunrise',
            'Twelve Monkeys',
            'The Terminator',
            'Infernal Affairs',
            'Jaws',
            'The Battle of Algiers',
            'Groundhog Day',
            'Memories of Murder',
            'Guardians of the Galaxy',
            'Monsters, Inc.',
            'Harry Potter and the Deathly Hallows: Part 2',
            'Throne of Blood',
            'The Truman Show',
            'Fanny and Alexander',
            'Barry Lyndon',
            'Rocky',
            'Dog Day Afternoon',
            'The Imitation Game',
            'Yip Man',
            "The King's Speech",
            'High Noon',
            'La Haine',
            'A Fistful of Dollars',
            'The Curse of the Black Pearl',
            'Notorious',
            'Castle in the Sky',
            'Prisoners',
            'The Help',
            "Who's Afraid of Virginia Woolf?",
            'Roman Holiday',
            'Spring, Summer, Fall, Winter... and Spring',
            'The Night of the Hunter',
            'Beauty and the Beast',
            'La Strada',
            'Papillon',
            'Days of Future Past',
            'Before Sunset',
            'Anatomy of a Murder',
            'The Hustler',
            'The Graduate',
            'The Big Sleep',
            'Underground',
            'Paris, Texas',
            'Akira'
        ]),
    'movie_characters': WordList(
        short_name='Movie Characters',
        description='Character names from Movies',
        medium=[
            'Forrest Gump',
            'Aragorn',
            'Legolas ',
            'Gimli',
            'Frodo',
            'Samwise Gamgee',
            'Sauron',
            'Captain Jack Sparrow',
            'Jack Skellington',
            'Oogie Boogie Man',
            'Ellen Ripley',
            'Han Solo',
            'Luke Skywalker',
            'Leia Organa',
            'Joker',
            'Batman',
            'Indiana Jones',
            'Hannibal Lector',
            'Gollum',
            'Gandalf ',
            'John McClane',
            'Norman Bates',
            'James Bond',
            'Vito Corleone',
            'Iron Man',
            'Maximus',
            'Tony Montana',
            'Freddy Krueger',
            'George Bailey',
            'Ebenezer Scrooge',
            'Neo',
            'Superman',
            'Dorothy Gale',
            'Obi-Wan Kenobi',
            'Wolverine',
            'Terminator',
            'Spider-Man',
            'Nurse Ratched',
            'Jason Bourne',
            'Buzz Lightyear',
            'Darth Vader',
            'Sheriff Woody',
            'Captain America',
            'Kevin McCallister',
            'Groot',
            'Dracula',
            'Boba Fett',
            'Optimus Prime',
            'Wednesday Addams',
            'Inigo Montoya',
            'Miracle Max',
            'Ethan Hunt',
            'Red (Shawshank Redemption)',
            'Bane',
            'Frank Drebin',
            'Captain Kirk',
            'Marge Gunderson',
            'Harry Potter',
            'Hans Landa',
            'E.T.',
            'Bilbo Baggins',
            'Dr. King Schultz',
            'Ace Ventura',
            'Sarah Conner',
            'Katniss Everdeen',
            'Jack Burton',
            'Rick Deckard',
            'Tommy DeVito',
            'Ferris Bueller',
            'Yoda',
            'Walter Sobchak',
            'Rocky Balboa',
            'Atticus Finch',
            'Jules Winnfield',
            'Peter Venkman',
            'Snake Plissken',
            'Doc Brown',
            'Marty Mcfly',
            'The Dude',
            'Snow White',
            'Cinderella',
            'Mickey Mouse',
            'Minnie Mouse',
            'Goofy',
            'Captain Hook',
            'Simba',
            'Donald Duck',
            'The Mad Hatter',
            'Chesire Cat',
            'Gepetto',
            'Pinocchio',
            'Aurora',
            'Matilda',
            'Bambi',
            'Quasimodo',
            'Hercules',
            'Hades',
            'Nemo ',
            'Tinker Belle',
            'Baloo',
            'Aladdin',
            'Pocahontas',
            'Peter Pan',
            'King Triton',
            'Mrs. Potts',
            'Ursela',
            'Mufasa',
            'Cogsworth',
            'Jiminy Cricket',
            'Mulan',
            'Repunzel',
            'Olaf',
            'Jafar',
            'Magic Carpet',
            'The Genie',
            'Lumiere',
            'Mr. Smee',
            'Queen of Hearts',
            'Kuzco',
            'Kronk',
            'Dopey',
            'Grumpy',
            'Fairy Godmother',
            'Maleficent',
            'Prince Phillip',
            'Mowgli',
            'Bagheera ',
            'Shere Khan',
            'Robin Hood',
            'Little John',
            'Winnie the Pooh',
            'Cruella De Vil',
            'Christopher Robin',
            'Tigger',
            'Mushu',
            'Dumbo',
            'Zeus',
            'Tarzan',
            'Pumbaa',
            'Ichabod',
            'Headless Horseman',
            'Predator',
            'BeetleJuice',
            'Edward Scissor Hands',
            'Conan the Barbarian',
            'Casper',
            'Dennis the Menace',
            'Django',
            'The Grinch',
            'Santa ',
            'Dredd',
            'Dudley Do-Right',
            'Chunk (Goonies)',
            'Mouth (Goonies)',
            'Sloth (Goonies)',
            'Data (Goonies)',
            'Mr. Incredible',
            'Jack and the Beanstalk',
            'John Wick',
            'King Kong',
            'Godzilla',
            'Jaws',
            'Mad Max',
            'Mary Poppins',
            'The Mask',
            'Harry Crumb',
            'Uncle Buck',
            'Sherlock Holmes',
            'Wonder Woman',
            'Rose (Titanic)',
            'Harley Quinn',
            'Shrek',
            'Princess Fiona',
            'Jessica Rabbit',
            'Galadriel',
            'Catwoman',
            'Wicked Witch of the West',
            'Elizabeth Swann',
            'Imperator Furiosa',
            'Marion Ravenwood',
            'Cleopatra',
            'Lara Croft',
            'Michael Myers',
            'Agent Smith',
            'Palpatine',
            'Anton Chigurh',
            'Alien (Xenomorph)',
            'Pennywise (IT)',
            'Jason Voorhees',
            'Darth Maul',
            'Davy Jones',
            'Thanos',
            'Buffalo Bill',
            'Professor Moriarty',
            'Khan',
            'Dr. Evil',
            'Jabba the Hutt',
            'Adolf Hitler',
            'PinHead',
            'Commodus',
            'Smaug',
            'PeeWee Herman',
            'Chucky',
            'Biff Tannen',
            'Shredder',
            '*One of the Ninja Turtles*',
            'Willy Wonka',
            'Lex Luthor ',
            'Dr. Otto Octavius',
            'The Kracken',
            'Sweeney Todd',
            'The White Witch',
            'Col. Nathan R. Jessep',
            'Zorro',
            'Daniel LaRusso',
            'John Rambo',
            'Elliot Ness',
            'Robocop',
            'Wyatt Earp',
            'Doc Holiday',
            'Spock',
            'William Wallace',
            'Chief Brody',
            'Martin Hooper',
            'Quint',
            'Oskar Schindler',
            'Clarice Starling',
            'Prince Humperdinck',
            'Falkor',
            'Gmork',
            'Rockbiter',
            'Atreyu',
            'Bastian Balthazar Bux',
            'Mike Wazowski',
            'Roger Rabbit'
        ]),
}
