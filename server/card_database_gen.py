import sqlite3

DB_NAME = "pokemon_cards.db"

# Connect to database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create table structure
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cards (
        ID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Type TEXT NOT NULL,
        A1Name INTEGER,
        A1Schaden INTEGER,
        A2Name INTEGER,
        A2Schaden INTEGER,
        A1Energie INTEGER,
        A2Energie INTEGER,
        Schwäche TEXT,
        Resistenz TEXT,
        RückzugsKosten INTEGER,
        Leben INTEGER,
        Seltenheit TEXT
    )
''')

# Insert 30 cards into the table
cards = [
    (1, "Bisasam", "Pflanze", "Rasierblatt", 20, "Solarstrahl", 80, 1, 3, "Feuer", "Wasser", 1, 60, "Common"),
    (2, "Bisaknosp", "Pflanze", "Tackle", 10, "Gigasauger", 40, 2, 3, "Feuer", "Wasser", 1, 80, "Uncommon"),
    (3, "Bisaflor", "Pflanze", "Rasierblatt", 40, "Solarstrahl", 100, 2, 4, "Feuer", "Wasser", 2, 120, "HoloRare"),
    (4, "Glumanda", "Feuer", "Glut", 30, "Flammenwurf", 60, 1, 2, "Wasser", "Pflanze", 1, 50, "Common"),
    (5, "Glutexo", "Feuer", "Flammenwurf", 40, "Feuersturm", 100, 2, 4, "Wasser", "Pflanze", 2, 90, "Uncommon"),
    (6, "Glurak", "Feuer", "Drachenwut", 60, "Hyperstrahl", 120, 3, 5, "Wasser", "Pflanze", 3, 140, "HoloRare"),
    (7, "Schiggy", "Wasser", "Aquaknarre", 20, "Hydropumpe", 70, 1, 3, "Pflanze", "Feuer", 1, 50, "Common"),
    (8, "Schillok", "Wasser", "Blubber", 20, "Hydropumpe", 90, 2, 4, "Pflanze", "Feuer", 1, 80, "Uncommon"),
    (9, "Turtok", "Wasser", "Aquaknarre", 40, "Hyperstrahl", 100, 2, 5, "Pflanze", "Feuer", 3, 130, "HoloRare"),
    (10, "Raupy", "Käfer", "Tackle", 10, "Käferbiss", 20, 1, 2, "Feuer", "Pflanze", 1, 40, "Common"),
    (11, "Safcon", "Käfer", "Härtner", "-", "-", "-", 1, "-", "Feuer", "Pflanze", 2, 50, "Common"),
    (12, "Smettbo", "Käfer", "Windstoß", 30, "Psychokinese", 50, 1, 3, "Feuer", "Boden", 1, 70, "Uncommon"),
    (13, "Hornliu", "Käfer", "Gifttackle", 10, "Giftstachel", 30, 1, 2, "Feuer", "Pflanze", 1, 40, "Common"),
    (14, "Kokuna", "Käfer", "Härtner", "-", "-", "-", 1, "-", "Feuer", "Pflanze", 2, 50, "Common"),
    (15, "Bibor", "Käfer", "Schlitzer", 30, "Käferbiss", 50, 2, 3, "Feuer", "Pflanze", 1, 80, "Uncommon"),
    (16, "Taubsi", "Normal", "Tackle", 10, "Windstoß", 20, 1, 2, "Elektro", "Boden", 1, 40, "Common"),
    (17, "Tauboga", "Normal", "Windstoß", 20, "Luftschnitt", 40, 2, 3, "Elektro", "Boden", 1, 70, "Uncommon"),
    (18, "Tauboss", "Normal", "Windstoß", 40, "Hyperstrahl", 100, 2, 4, "Elektro", "Boden", 2, 120, "Rare"),
    (19, "Rattfratz", "Normal", "Kratzer", 10, "Biss", 30, 1, 2, "Kampf", "Pflanze", 1, 30, "Common"),
    (20, "Rattikarl", "Normal", "Biss", 30, "Hyperzahn", 60, 2, 3, "Kampf", "Pflanze", 1, 60, "Uncommon"),
    (21, "Habitak", "Normal", "Schlitzer", 10, "Windstoß", 20, 1, 2, "Elektro", "Boden", 1, 40, "Common"),
    (22, "Ibitak", "Normal", "Luftschnitt", 40, "Hyperstrahl", 90, 2, 4, "Elektro", "Boden", 1, 80, "Uncommon"),
    (23, "Rettan", "Gift", "Gifttackle", 10, "Giftdruck", 30, 1, 2, "Psycho", "Pflanze", 1, 40, "Common"),
    (24, "Arbok", "Gift", "Giftdruck", 30, "Knirscher", 50, 2, 3, "Psycho", "Pflanze", 2, 80, "Uncommon"),
    (25, "Pikachu", "Elektro", "Donnerschock", 20, "Donnerblitz", 60, 1, 3, "Boden", "Pflanze", 1, 40, "Common"),
    (26, "Raichu", "Elektro", "Donnerblitz", 40, "Hyperstrahl", 90, 2, 4, "Boden", "Pflanze", 1, 80, "Rare"),
    (27, "Sandan", "Boden", "Lehmschelle", 20, "Schlitzer", 40, 1, 3, "Wasser", "Pflanze", 1, 50, "Common"),
    (28, "Sandamer", "Boden", "Schlitzer", 40, "Erdbeben", 100, 2, 4, "Wasser", "Pflanze", 2, 100, "Uncommon"),
    (29, "Nidoran♀", "Gift", "Gifttackle", 10, "Giftdruck", 20, 1, 2, "Psycho", "Pflanze", 1, 40, "Common"),
    (30, "Nidorina", "Gift", "Biss", 30, "Giftdruck", 50, 2, 3, "Psycho", "Pflanze", 1, 70, "Uncommon"),
    (31, "Nidoqueen", "Gift", "Schädelwumme", 60, "Erdbeben", 120, 3, 5, "Psycho", "Pflanze", 3, 120, "HoloRare"),
    (32, "Nidoran♂", "Gift", "Gifttackle", 10, "Giftdruck", 20, 1, 2, "Psycho", "Pflanze", 1, 40, "Common"),
    (33, "Nidorino", "Gift", "Schlitzer", 30, "Giftdruck", 50, 2, 3, "Psycho", "Pflanze", 1, 70, "Uncommon"),
    (34, "Nidoking", "Gift", "Schädelwumme", 60, "Hyperstrahl", 120, 3, 5, "Psycho", "Pflanze", 3, 120, "HoloRare"),
    (35, "Piepi", "Normal", "Mondschein", "-", "Kratzer", 20, 1, 2, "Kampf", "Pflanze", 1, 50, "Rare"),
    (36, "Pixi", "Normal", "Mondschein", "-", "Schlitzer", 40, 2, 3, "Kampf", "Pflanze", 1, 80, "Rare"),
    (37, "Vulpix", "Feuer", "Glut", 20, "Flammenwurf", 60, 1, 3, "Wasser", "Pflanze", 1, 40, "Common"),
    (38, "Vulnona", "Feuer", "Flammenwurf", 40, "Feuersturm", 100, 2, 4, "Wasser", "Pflanze", 1, 90, "HoloRare"),
    (39, "Pummeluff", "Normal", "Kulleraugen", "-", "Rasierblatt", 30, 1, 2, "Kampf", "Pflanze", 1, 60, "Common"),
    (40, "Knuddeluff", "Normal", "Bodyslam", 40, "Hyperstrahl", 90, 2, 4, "Kampf", "Pflanze", 2, 120, "Rare"),
    (41, "Zubat", "Gift", "Biss", 20, "Windstoß", 30, 1, 2, "Elektro", "Pflanze", 1, 40, "Common"),
    (42, "Golbat", "Gift", "Flügelschlag", 40, "Hyperstrahl", 70, 2, 4, "Elektro", "Pflanze", 1, 70, "Uncommon"),
    (43, "Myrapla", "Pflanze", "Rankenhieb", 10, "Gigasauger", 30, 1, 2, "Feuer", "Wasser", 1, 40, "Common"),
    (44, "Duflor", "Pflanze", "Gigasauger", 30, "Rasierblatt", 50, 2, 3, "Feuer", "Wasser", 1, 70, "Uncommon"),
    (45, "Giflor", "Pflanze", "Rasierblatt", 50, "Blizzard", 100, 2, 4, "Feuer", "Wasser", 2, 120, "Rare"),
    (46, "Paras", "Pflanze", "Kratzer", 10, "Gigasauger", 20, 1, 2, "Feuer", "Pflanze", 1, 40, "Common"),
    (47, "Parasek", "Pflanze", "Rankenhieb", 30, "Giftdruck", 40, 2, 3, "Feuer", "Pflanze", 1, 80, "Uncommon"),
    (48, "Bluzuk", "Käfer", "Käferbiss", 20, "Gifttackle", 30, 1, 2, "Feuer", "Pflanze", 1, 50, "Common"),
    (49, "Omot", "Käfer", "Windstoß", 30, "Psychokinese", 50, 2, 3, "Feuer", "Pflanze", 1, 80, "Rare"),
    (50, "Digda", "Boden", "Lehmschelle", 10, "Schlitzer", 20, 1, 2, "Wasser", "Pflanze", 1, 30, "Common"),
    (51, "Digdri", "Boden", "Schlitzer", 30, "Erdbeben", 70, 2, 3, "Wasser", "Pflanze", 1, 60, "Uncommon"),
    (52, "Mauzi", "Normal", "Kratzer", 10, "Biss", 20, 1, 2, "Kampf", "Pflanze", 1, 40, "Common"),
    (53, "Snobilikat", "Normal", "Biss", 30, "Hyperstrahl", 60, 2, 3, "Kampf", "Pflanze", 1, 70, "Uncommon"),
    (54, "Enton", "Wasser", "Blubber", 10, "Aquaknarre", 30, 1, 2, "Pflanze", "Feuer", 1, 50, "Common"),
    (55, "Entoron", "Wasser", "Aquaknarre", 40, "Hydropumpe", 80, 2, 3, "Pflanze", "Feuer", 2, 90, "Uncommon"),
    (56, "Menki", "Kampf", "Fußtritt", 10, "Bodyslam", 30, 1, 2, "Psycho", "Pflanze", 1, 40, "Common"),
    (57, "Rasaff", "Kampf", "Bodyslam", 30, "Hyperstrahl", 60, 2, 3, "Psycho", "Pflanze", 1, 80, "Uncommon"),
    (58, "Fukano", "Feuer", "Glut", 20, "Flammenwurf", 40, 1, 2, "Wasser", "Pflanze", 1, 50, "Common"),
    (59, "Arkani", "Feuer", "Flammenwurf", 50, "Feuersturm", 90, 2, 4, "Wasser", "Pflanze", 2, 110, "Rare"),
    (60, "Quapsel", "Wasser", "Blubber", 10, "Aquaknarre", 20, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (61, "Quaputzi", "Wasser", "Aquaknarre", 20, "Hydropumpe", 60, 2, 3, "Pflanze", "Feuer", 1, 70, "Uncommon"),
    (62, "Quappo", "Wasser", "Hydropumpe", 50, "Hyperstrahl", 100, 3, 5, "Pflanze", "Feuer", 2, 100, "Rare"),
    (63, "Abra", "Psycho", "Teleport", "-", "Psychokinese", 30, 1, 2, "Käfer", "Boden", 1, 40, "Common"),
    (64, "Kadabra", "Psycho", "Psychokinese", 40, "Genesung", "-", 2, 3, "Käfer", "Boden", 1, 70, "Uncommon"),
    (65, "Simsala", "Psycho", "Psychokinese", 60, "Metronom", 80, 3, 4, "Käfer", "Boden", 2, 100, "Rare"),
    (66, "Machollo", "Kampf", "Karatetritt", 10, "Bodyslam", 30, 1, 2, "Psycho", "Pflanze", 1, 50, "Common"),
    (67, "Maschock", "Kampf", "Bodyslam", 30, "Hyperstrahl", 60, 2, 3, "Psycho", "Pflanze", 1, 80, "Uncommon"),
    (68, "Machomei", "Kampf", "Hyperstrahl", 70, "Erdbeben", 120, 3, 5, "Psycho", "Pflanze", 3, 120, "HoloRare"),
    (69, "Knofensa", "Pflanze", "Rasierblatt", 20, "Rankenhieb", 30, 1, 2, "Feuer", "Wasser", 1, 40, "Common"),
    (70, "Ultrigaria", "Pflanze", "Rankenhieb", 30, "Rasierblatt", 50, 2, 3, "Feuer", "Wasser", 1, 70, "Uncommon"),
    (71, "Sarzenia", "Pflanze", "Rasierblatt", 50, "Blizzard", 90, 2, 4, "Feuer", "Wasser", 2, 110, "Rare"),
    (72, "Tentacha", "Wasser", "Aquaknarre", 20, "Giftdruck", 30, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (73, "Tentoxa", "Wasser", "Giftdruck", 40, "Hydropumpe", 80, 2, 3, "Pflanze", "Feuer", 2, 90, "Uncommon"),
    (74, "Kleinstein", "Gestein", "Schlammbombe", 10, "Steinhagel", 30, 1, 2, "Wasser", "Pflanze", 1, 40, "Common"),
    (75, "Georok", "Gestein", "Steinhagel", 30, "Erdbeben", 60, 2, 3, "Wasser", "Pflanze", 1, 60, "Uncommon"),
    (76, "Geowaz", "Gestein", "Erdbeben", 60, "Hyperstrahl", 120, 3, 5, "Wasser", "Pflanze", 3, 110, "Rare"),
    (77, "Ponita", "Feuer", "Glut", 30, "Flammenwurf", 60, 1, 2, "Wasser", "Pflanze", 1, 50, "Common"),
    (78, "Gallopa", "Feuer", "Flammenwurf", 50, "Feuersturm", 100, 2, 4, "Wasser", "Pflanze", 2, 90, "Uncommon"),
    (79, "Flegmon", "Wasser", "Blubber", 20, "Konfusion", 40, 1, 2, "Pflanze", "Feuer", 1, 60, "Common"),
    (80, "Lahmus", "Wasser", "Konfusion", 40, "Psychokinese", 70, 2, 3, "Pflanze", "Feuer", 2, 90, "Uncommon"),
    (81, "Magnetilo", "Elektro", "Donnerschock", 20, "Donnerblitz", 40, 1, 2, "Boden", "Pflanze", 1, 40, "Common"),
    (82, "Magneton", "Elektro", "Donnerblitz", 40, "Lichtkanone", 70, 2, 3, "Boden", "Pflanze", 2, 80, "HoloRare"),
    (83, "Porenta", "Normal", "Tackle", 20, "Windstoß", 30, 1, 2, "Kampf", "Pflanze", 1, 50, "Common"),
    (84, "Dodu", "Normal", "Tackle", 10, "Windstoß", 20, 1, 2, "Elektro", "Pflanze", 1, 40, "Common"),
    (85, "Dodri", "Normal", "Windstoß", 30, "Hyperstrahl", 70, 2, 4, "Elektro", "Pflanze", 1, 70, "Uncommon"),
    (86, "Jurob", "Wasser", "Blubber", 20, "Eisstrahl", 40, 1, 2, "Pflanze", "Feuer", 1, 50, "Common"),
    (87, "Jugong", "Wasser", "Eisstrahl", 40, "Blizzard", 80, 2, 3, "Pflanze", "Feuer", 2, 90, "Uncommon"),
    (88, "Sleima", "Gift", "Gifttackle", 10, "Schlammbombe", 30, 1, 2, "Psycho", "Pflanze", 1, 50, "Common"),
    (89, "Sleimok", "Gift", "Schlammbombe", 30, "Knirscher", 60, 2, 3, "Psycho", "Pflanze", 1, 80, "Uncommon"),
    (90, "Muschas", "Wasser", "Blubber", 20, "Eisstrahl", 40, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (91, "Austos", "Wasser", "Eisstrahl", 50, "Blizzard", 90, 2, 4, "Pflanze", "Feuer", 2, 90, "Uncommon"),
    (92, "Nebulak", "Geist", "Spukball", 20, "Konfusion", 30, 1, 2, "Psycho", "Boden", 1, 40, "Common"),
    (93, "Alpollo", "Geist", "Spukball", 40, "Knirscher", 60, 2, 3, "Psycho", "Boden", 1, 70, "Uncommon"),
    (94, "Gengar", "Geist", "Psychokinese", 60, "Spukball", 90, 3, 4, "Psycho", "Boden", 2, 100, "HoloRare"),
    (95, "Onix", "Gestein", "Steinhagel", 20, "Erdbeben", 40, 1, 2, "Wasser", "Pflanze", 1, 60, "Common"),
    (96, "Traumato", "Psycho", "Konfusion", 20, "Hypnose", 30, 1, 2, "Käfer", "Boden", 1, 50, "Common"),
    (97, "Hypno", "Psycho", "Psychokinese", 40, "Hypnose", 60, 2, 3, "Käfer", "Boden", 2, 80, "Uncommon"),
    (98, "Krabby", "Wasser", "Blubber", 20, "Schlitzer", 30, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (99, "Kingler", "Wasser", "Schlitzer", 40, "Hydropumpe", 80, 2, 3, "Pflanze", "Feuer", 2, 80, "Uncommon"),
    (100, "Voltobal", "Elektro", "Donnerschock", 20, "Schockwelle", 40, 1, 2, "Boden", "Pflanze", 1, 40, "Common"),
    (101, "Lektrobal", "Elektro", "Schockwelle", 40, "Donnerblitz", 70, 2, 3, "Boden", "Pflanze", 1, 70, "Uncommon"),
    (102, "Owei", "Pflanze", "Gigasauger", 30, "Psychokinese", 50, 1, 2, "Feuer", "Wasser", 1, 40, "Common"),
    (103, "Kokowei", "Pflanze", "Psychokinese", 40, "Blizzard", 90, 2, 4, "Feuer", "Wasser", 2, 90, "Uncommon"),
    (104, "Tragosso", "Boden", "Knochenkeule", 20, "Schädelwumme", 40, 1, 2, "Wasser", "Pflanze", 1, 50, "Common"),
    (105, "Knogga", "Boden", "Schädelwumme", 40, "Erdbeben", 70, 2, 3, "Wasser", "Pflanze", 2, 80, "Uncommon"),
    (106, "Kicklee", "Kampf", "Karatetritt", 30, "Megakick", 60, 1, 2, "Psycho", "Pflanze", 1, 60, "Rare"),
    (107, "Nockchan", "Kampf", "Haken", 30, "Feuerschlag", 60, 1, 2, "Psycho", "Pflanze", 1, 60, "HOloRare"),
    (108, "Schlurp", "Normal", "Bodyslam", 20, "Schlitzer", 40, 1, 2, "Kampf", "Pflanze", 1, 90, "Common"),
    (109, "Smogon", "Gift", "Schlammbombe", 20, "Knirscher", 40, 1, 2, "Psycho", "Pflanze", 1, 60, "Common"),
    (110, "Smogmog", "Gift", "Knirscher", 40, "Schlammbombe", 70, 2, 3, "Psycho", "Pflanze", 2, 80, "Uncommon"),
    (111, "Rihorn", "Boden", "Kratzer", 20, "Steinhagel", 30, 1, 2, "Wasser", "Pflanze", 1, 50, "Common"),
    (112, "Rizeros", "Boden", "Steinhagel", 40, "Erdbeben", 70, 2, 3, "Wasser", "Pflanze", 2, 90, "Uncommon"),
    (113, "Chaneira", "Normal", "Kulleraugen", "-", "Bodyslam", 30, 1, 2, "Kampf", "Pflanze", 2, 120, "Rare"),
    (114, "Tangela", "Pflanze", "Rasierblatt", 30, "Gigasauger", 50, 1, 2, "Feuer", "Wasser", 1, 60, "Common"),
    (115, "Kangama", "Normal", "Tackle", 20, "Hyperstrahl", 70, 2, 4, "Kampf", "Pflanze", 2, 90, "Rare"),
    (116, "Seeper", "Wasser", "Blubber", 20, "Aquaknarre", 30, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (117, "Seemon", "Wasser", "Aquaknarre", 30, "Hydropumpe", 60, 2, 3, "Pflanze", "Feuer", 1, 70, "Uncommon"),
    (118, "Goldini", "Wasser", "Schlitzer", 20, "Aquaknarre", 40, 1, 2, "Pflanze", "Feuer", 1, 50, "Common"),
    (119, "Golking", "Wasser", "Aquaknarre", 40, "Hydropumpe", 70, 2, 3, "Pflanze", "Feuer", 2, 80, "Uncommon"),
    (120, "Sterndu", "Wasser", "Blubber", 10, "Psychokinese", 30, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (121, "Starmie", "Wasser", "Psychokinese", 40, "Hydropumpe", 70, 2, 3, "Pflanze", "Feuer", 1, 80, "Uncommon"),
    (122, "Pantimos", "Psycho", "Konfusion", 20, "Psychokinese", 50, 1, 2, "Käfer", "Boden", 1, 60, "HoloRare"),
    (123, "Sichlor", "Käfer", "Käferbiss", 30, "Schlitzer", 50, 1, 3, "Feuer", "Pflanze", 1, 70, "HoloRare"),
    (124, "Rossana", "Psycho", "Eisstrahl", 30, "Psychokinese", 60, 1, 3, "Käfer", "Boden", 1, 80, "Uncommon"),
    (125, "Elektek", "Elektro", "Donnerschock", 30, "Donnerblitz", 60, 1, 3, "Boden", "Pflanze", 1, 70, "Uncommon"),
    (126, "Magmar", "Feuer", "Glut", 30, "Flammenwurf", 60, 1, 3, "Wasser", "Pflanze", 1, 70, "Uncommon"),
    (127, "Pinsir", "Käfer", "Schlitzer", 30, "Bodyslam", 50, 1, 3, "Feuer", "Pflanze", 1, 80, "Rare"),
    (128, "Tauros", "Normal", "Bodyslam", 40, "Hyperstrahl", 70, 2, 3, "Kampf", "Pflanze", 2, 90, "Rare"),
    (129, "Karpador", "Wasser", "Platscher", "-", "Tackle", 10, 1, 1, "Pflanze", "Feuer", 1, 30, "Common"),
    (130, "Garados", "Wasser", "Hydropumpe", 50, "Hyperstrahl", 100, 3, 5, "Pflanze", "Feuer", 3, 120, "HoloRare"),
    (131, "Lapras", "Wasser", "Eisstrahl", 40, "Blizzard", 80, 2, 4, "Pflanze", "Feuer", 2, 120, "HoloRare"),
    (132, "Ditto", "Normal", "Verwandlung", "-", "Tackle", 10, 1, 1, "Kampf", "Pflanze", 1, 50, "Uncommon"),
    (133, "Evoli", "Normal", "Tackle", 10, "Schlitzer", 20, 1, 2, "Kampf", "Pflanze", 1, 40, "Common"),
    (134, "Aquana", "Wasser", "Blubber", 30, "Aquaknarre", 50, 1, 3, "Pflanze", "Feuer", 1, 80, "HoloRare"),
    (135, "Blitza", "Elektro", "Donnerschock", 30, "Donnerblitz", 60, 1, 3, "Boden", "Pflanze", 1, 80, "HoloRare"),
    (136, "Flamara", "Feuer", "Glut", 30, "Flammenwurf", 60, 1, 3, "Wasser", "Pflanze", 1, 80, "HoloRare"),
    (137, "Porygon", "Normal", "Konvertierung", "-", "Tackle", 20, 1, 2, "Kampf", "Pflanze", 1, 60, "Uncommon"),
    (138, "Amonitas", "Wasser", "Blubber", 20, "Hydropumpe", 50, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (139, "Amoroso", "Wasser", "Hydropumpe", 40, "Hyperstrahl", 90, 2, 4, "Pflanze", "Feuer", 2, 80, "Uncommon"),
    (140, "Kabuto", "Wasser", "Schlitzer", 20, "Aquaknarre", 40, 1, 2, "Pflanze", "Feuer", 1, 40, "Common"),
    (141, "Kabutops", "Wasser", "Schlitzer", 40, "Hydropumpe", 80, 2, 4, "Pflanze", "Feuer", 2, 90, "HoloRare"),
    (142, "Aerodactyl", "Gestein", "Flügelschlag", 40, "Hyperstrahl", 100, 2, 4, "Wasser", "Pflanze", 2, 100, "HoloRare"),
    (143, "Relaxo", "Normal", "Bodyslam", 50, "Hyperstrahl", 120, 3, 5, "Kampf", "Pflanze", 4, 160, "HoloRare"),
    (144, "Arktos", "Eis", "Eisstrahl", 40, "Blizzard", 90, 2, 4, "Feuer", "Pflanze", 2, 100, "HoloRare"),
    (145, "Zapdos", "Elektro", "Donnerschock", 40, "Donnerblitz", 90, 2, 4, "Boden", "Pflanze", 2, 100, "HoloRare"),
    (146, "Lavados", "Feuer", "Glut", 40, "Feuersturm", 90, 2, 4, "Wasser", "Pflanze", 2, 100, "HoloRare"),
    (147, "Dratini", "Drache", "Drachenwut", 30, "Hyperstrahl", 60, 1, 3, "Eis", "Pflanze", 1, 40, "Common"),
    (148, "Dragonir", "Drache", "Hyperstrahl", 50, "Drachenwut", 80, 2, 4, "Eis", "Pflanze", 2, 80, "Uncommon"),
    (149, "Dragoran", "Drache", "Hyperstrahl", 70, "Drachenwut", 120, 3, 5, "Eis", "Pflanze", 3, 120, "HoloRare"),
    (150, "Mewtu", "Psycho", "Psychokinese", 70, "Genesung", "-", 3, 4, "Käfer", "Boden", 2, 130, "HoloRare")

]

# Insert cards into the table
cursor.executemany('''
    INSERT INTO Cards (ID, Name, Type, A1Name, A1Schaden, A2Name, A2Schaden, A1Energie, A2Energie, Schwäche, Resistenz, RückzugsKosten, Leben, Seltenheit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', cards)

# Commit changes / close the connection
conn.commit()
conn.close()

print(f"Database '{DB_NAME}' created")
