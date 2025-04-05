import spacy
import csv

# Load English language model
nlp = spacy.load("en_core_web_sm")

# Load your text file
with open("LML specification 1.4.txt", "r", encoding="latin-1") as file:
    text = file.read()

# Process the text
doc = nlp(text)

# Extract singular common nouns (filtering out plural nouns and multi-word expressions)
nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN" and token.tag_ != "NNS" and " " not in token.lemma_]

# Extract base-form verbs (filtering out multi-word expressions)
verbs = [token.lemma_ for token in doc if token.pos_ == "VERB" and " " not in token.lemma_]

# Remove duplicates
unique_nouns = sorted(set(nouns))
unique_verbs = sorted(set(verbs))

# -------------------------------
# ✨ 1. Write to CSV
# -------------------------------
with open("nouns.csv", "w", newline='', encoding="utf-8") as noun_file:
    writer = csv.writer(noun_file)
    writer.writerow(["Noun"])
    for noun in unique_nouns:
        writer.writerow([noun])

# -------------------------------
# ✨ Write verbs to verbs.csv
# -------------------------------
with open("verbs.csv", "w", newline='', encoding="utf-8") as verb_file:
    writer = csv.writer(verb_file)
    writer.writerow(["Verb"])
    for verb in unique_verbs:
        writer.writerow([verb])

print("✅ CSV files saved: 'nouns.csv' and 'verbs.csv'")


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