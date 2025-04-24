import csv
import argparse
import spacy
from itertools import product


def extract_triples_with_nlp(text):
    """
    Extract RDF triples from text using NLP to identify subjects (nouns),
    predicates (verbs), and objects (nouns).
    """
    # Load English language model
    nlp = spacy.load("en_core_web_sm")

    # Process the text
    doc = nlp(text)

    # Use a set to store unique triples
    unique_triples = set()

    # Process each sentence separately
    for sent in doc.sents:
        subjects = []
        predicates = []
        objects = []

        # Identify nouns and verbs
        for token in sent:
            # Find nouns (subjects and objects)
            if token.pos_ in ["NOUN", "PROPN"]:
                # Check if it's likely a subject or object based on dependency
                if token.dep_ in ["nsubj", "nsubjpass"]:
                    subjects.append(token.text)
                elif token.dep_ in ["dobj", "pobj", "attr"]:
                    objects.append(token.text)
                else:
                    # If dependency doesn't clearly indicate role, add to both for consideration
                    subjects.append(token.text)
                    objects.append(token.text)

            # Find verbs (predicates)
            elif token.pos_ == "VERB":
                predicates.append(token.text)

        # If we have found potential subjects, predicates, and objects
        if subjects and predicates and objects:
            # Create triples from all combinations of subjects, predicates, and objects
            for subj, pred, obj in product(subjects, predicates, objects):
                # Avoid self-referential triples
                if subj != obj:
                    # Add to set of unique triples
                    unique_triples.add((subj, pred, obj))

    # Convert set back to list for further processing
    return list(unique_triples)


def write_triples_to_csv(triples, output_file):
    """Write extracted triples to a CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['Subject', 'Predicate', 'Object'])
        # Write data
        for triple in triples:
            writer.writerow(triple)

    print(f"Extracted {len(triples)} unique triples to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Extract RDF triples from text using NLP and output to CSV')
    parser.add_argument('input_file', help='Path to the input .txt file containing text')
    parser.add_argument('output_file', help='Path to the output .csv file')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of triples to extract')
    args = parser.parse_args()

    try:
        # Check if spaCy is installed and the model is available
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Installing required spaCy model...")
                import subprocess
                subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
        except ImportError:
            print("spaCy is required. Installing...")
            import subprocess
            subprocess.check_call(["pip", "install", "spacy"])
            subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])

        # Read text file
        with open(args.input_file, 'r', encoding='utf-8') as file:
            text = file.read()

        # Extract unique triples using NLP
        triples = extract_triples_with_nlp(text)

        if not triples:
            print("No triples found in the input file.")
            return

        # Limit the number of triples if specified
        if args.limit and len(triples) > args.limit:
            triples = triples[:args.limit]
            print(f"Limited output to {args.limit} triples.")

        # Write to CSV
        write_triples_to_csv(triples, args.output_file)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()