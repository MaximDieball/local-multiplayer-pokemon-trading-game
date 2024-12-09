import sqlite3

# Define database and table creation
DB_NAME = "pokemon_cards.db"

# Connect to the SQLite database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create the table structure
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cards (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Type TEXT NOT NULL,
        A1Schaden INTEGER,
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

# Insert 30 real Gen 1 Pokémon cards into the table with German names and attacks
cards = [
    ("Pikachu", "Electric", 10, 30, 1, 3, "Fighting", None, 1, 50, "Common"),  # Attack names not available for Pikachu
    ("Glumanda", "Fire", 10, 30, 1, 2, "Water", None, 1, 50, "Common"),
    ("Bisasam", "Grass", 10, 20, 1, 2, "Fire", None, 1, 60, "Common"),
    ("Schiggy", "Water", 10, 20, 1, 2, "Electric", None, 1, 50, "Common"),
    ("Taubsi", "Normal", 10, None, 1, None, "Electric", "Fighting", 1, 40, "Common"),
    ("Pummeluff", "Normal", 10, None, 1, None, "Fighting", "Ghost", 1, 60, "Common"),
    ("Mauzi", "Normal", 20, None, 2, None, "Fighting", None, 1, 50, "Common"),
    ("Machollo", "Fighting", 20, None, 1, None, "Psychic", None, 2, 70, "Common"),
    ("Kleinstein", "Fighting", 10, 20, 1, 2, "Grass", None, 1, 50, "Common"),
    ("Enton", "Water", 10, 30, 1, 2, "Electric", None, 1, 50, "Common"),
    ("Magnetilo", "Electric", 10, None, 1, None, "Fighting", "Electric", 1, 40, "Common"),
    ("Nebulak", "Ghost", None, None, None, None, "Dark", "Normal", 0, 30, "Common"),
    ("Evoli", "Normal", 10, 30, 1, 3, "Fighting", None, 1, 50, "Common"),
    ("Dratini", "Dragon", 10, None, 1, None, "Ice", None, 1, 40, "Common"),
    ("Rattfratz", "Normal", 20, None, 1, None, "Fighting", None, 0, 30, "Common"),
    ("Fukano", "Fire", 20, 40, 2, 3, "Water", None, 1, 70, "Uncommon"),
    ("Abra", "Psychic", 10, None, 1, None, "Dark", None, 0, 30, "Common"),
    ("Kadabra", "Psychic", 30, 50, 2, 3, "Dark", None, 1, 60, "Uncommon"),
    ("Gengar", "Ghost", 40, 60, 3, 4, "Psychic", "Fighting", 0, 80, "Rare"),
    ("Onix", "Rock", 10, 40, 1, 4, "Grass", None, 3, 90, "Uncommon"),
    ("Lapras", "Water", 20, 40, 2, 3, "Electric", None, 2, 80, "Rare"),
    ("Relaxo", "Normal", 30, 60, 4, 5, "Fighting", None, 4, 120, "Rare"),
    ("Mewtu", "Psychic", 40, 80, 3, 5, "Dark", None, 3, 100, "Rare"),
    ("Mew", "Psychic", 30, 60, 3, 4, "Dark", None, 0, 70, "Rare"),
    ("Glurak", "Fire", 50, 100, 4, 5, "Water", None, 3, 120, "Rare"),
    ("Turtok", "Water", 50, 100, 4, 5, "Electric", None, 3, 120, "Rare"),
    ("Bisaflor", "Grass", 50, 90, 4, 5, "Fire", None, 3, 120, "Rare"),
    ("Simsala", "Psychic", 40, 70, 3, 4, "Dark", None, 2, 80, "Rare"),
    ("Arktos", "Ice", 40, 80, 3, 5, "Rock", None, 2, 100, "Rare"),
    ("Zapdos", "Electric", 40, 80, 3, 5, "Rock", "Fighting", 2, 100, "Rare")
]

# Insert cards into the table
cursor.executemany('''
    INSERT INTO Cards (Name, Type, A1Schaden, A2Schaden, A1Energie, A2Energie, Schwäche, Resistenz, RückzugsKosten, Leben, Seltenheit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', cards)

# Commit changes and close the connection
conn.commit()
conn.close()

print(f"Database '{DB_NAME}' created and populated with 30 Gen 1 Pokémon cards (German names).")
