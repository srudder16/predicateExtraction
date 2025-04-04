import spacy
import csv

# Load English language model
nlp = spacy.load("en_core_web_sm")

# Load your text file
with open("ISO-15288_Section3_Final copy.txt", "r", encoding="windows-1252") as file:
    text = file.read()

# Process the text
doc = nlp(text)

# Extract singular common nouns (filtering out plural nouns)
nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN" and token.tag_ != "NNS"]

# Extract base-form verbs
verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

# Remove duplicates
unique_nouns = sorted(set(nouns))
unique_verbs = sorted(set(verbs))

# -------------------------------
# ✨ 1. Write to CSV
# -------------------------------
with open("extracted_words.csv", "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Nouns", "Verbs"])

    # Write rows — zip fills to the shorter of the two
    for noun, verb in zip(unique_nouns, unique_verbs):
        writer.writerow([noun, verb])

    # Handle unmatched lengths
    if len(unique_nouns) > len(unique_verbs):
        for noun in unique_nouns[len(unique_verbs):]:
            writer.writerow([noun, ""])
    elif len(unique_verbs) > len(unique_nouns):
        for verb in unique_verbs[len(unique_nouns):]:
            writer.writerow(["", verb])

print("✅ CSV file saved as 'extracted_words.csv'")

# -------------------------------
# ✨ 2. Write to TTL (Turtle)
# -------------------------------
with open("extracted_words.ttl", "w", encoding="utf-8") as ttlfile:
    ttlfile.write('@prefix : <http://example.org/ontology#> .\n')
    ttlfile.write('@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n')

    # Declare classes
    ttlfile.write(':Noun rdf:type rdf:Class .\n')
    ttlfile.write(':Verb rdf:type rdf:Class .\n\n')

    # Write individuals
    for noun in unique_nouns:
        safe_noun = noun.replace(" ", "_")
        ttlfile.write(f':{safe_noun} rdf:type :Noun .\n')

    ttlfile.write('\n')



print("✅ Turtle file saved as 'extracted_words.ttl'")