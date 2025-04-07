import csv
import argparse
import os


def get_inverse_verb(verb):
    """
    Generates the inverse form of a verb (e.g., "design" -> "designed by")

    Args:
        verb (str): The verb to invert

    Returns:
        str: The inverted verb phrase
    """
    # Dictionary for irregular verbs
    irregular_verbs = {
        "am": "is for",
        "is": "is for",
        "are": "are for",
        "was": "was for",
        "were": "were for",
        "have": "belongs to",
        "has": "belongs to",
        "had": "belonged to",
        "do": "done by",
        "does": "done by",
        "did": "done by",
        "go": "visited by",
        "goes": "visited by",
        "went": "visited by",
        "make": "made by",
        "makes": "made by",
        "made": "made by",
        "see": "seen by",
        "sees": "seen by",
        "saw": "seen by",
        "write": "written by",
        "writes": "written by",
        "wrote": "written by",
        "create": "created by",
        "creates": "created by",
        "design": "designed by",
        "designs": "designed by",
        "build": "built by",
        "builds": "built by",
        "develop": "developed by",
        "develops": "developed by",
        "implement": "implemented by",
        "implements": "implemented by",
        "manage": "managed by",
        "manages": "managed by"
    }

    # Check if it's in our irregular verbs dictionary
    verb_lower = verb.lower()
    if verb_lower in irregular_verbs:
        return irregular_verbs[verb_lower]

    # Regular verb transformations

    # Handle common verb endings
    if verb_lower.endswith('e'):
        return verb_lower + 'd by'
    elif verb_lower.endswith('y'):
        return verb_lower[:-1] + 'ied by'
    elif any(verb_lower.endswith(c + 't') for c in 'bcdfghjklmnpqrstvwxz'):
        # Verbs ending in a consonant + t (except when preceded by a vowel)
        return verb_lower + 'ted by'
    elif len(verb_lower) >= 3:
        # Check for consonant-vowel-consonant pattern
        last_three = verb_lower[-3:]
        if (last_three[0] not in 'aeiou' and
                last_three[1] in 'aeiou' and
                last_three[2] not in 'aeiouy'):
            return verb_lower + verb_lower[-1] + 'ed by'
        else:
            # Default case
            return verb_lower + 'ed by'
    else:
        # Default case for very short verbs
        return verb_lower + 'ed by'


def invert_triples(input_csv, output_csv):
    """
    Read RDF triples from a CSV file, invert them by swapping subject and object,
    and transform the predicate using verb inversion logic.

    Args:
        input_csv (str): Path to the input CSV file containing RDF triples
        output_csv (str): Path to save the inverted triples
    """
    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Error: Input file '{input_csv}' not found.")
        return

    try:
        # Determine if the input CSV has headers
        with open(input_csv, 'r', newline='', encoding='utf-8') as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            has_header = csv.Sniffer().has_header(sample)

            reader = csv.reader(csvfile)
            header = next(reader) if has_header else None

            # Determine column indices for subject, predicate, object
            if has_header:
                # Try to find columns by name
                subj_idx = header.index('Subject') if 'Subject' in header else 0
                pred_idx = header.index('Predicate') if 'Predicate' in header else 1
                obj_idx = header.index('Object') if 'Object' in header else 2
            else:
                # Default column positions
                subj_idx, pred_idx, obj_idx = 0, 1, 2

            # Read all triples
            triples = []
            for row in reader:
                if len(row) >= 3:  # Ensure row has enough columns
                    triples.append((row[subj_idx], row[pred_idx], row[obj_idx]))

        # Invert the triples
        inverted_triples = []
        for subj, pred, obj in triples:
            inverted_pred = get_inverse_verb(pred)
            inverted_triples.append((obj, inverted_pred, subj))  # Swap subject and object

        # Write inverted triples to output file
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            if has_header:
                writer.writerow(['Subject', 'Predicate', 'Object'])

            # Write inverted triples
            for triple in inverted_triples:
                writer.writerow(triple)

        print(f"Successfully inverted {len(inverted_triples)} triples and saved to {output_csv}")

    except Exception as e:
        print(f"Error processing CSV file: {e}")


def main():
    parser = argparse.ArgumentParser(description='Invert RDF triples from CSV and transform predicates')
    parser.add_argument('input_csv', help='Path to input CSV file containing RDF triples')
    parser.add_argument('output_csv', help='Path to output CSV file for inverted triples')
    args = parser.parse_args()

    invert_triples(args.input_csv, args.output_csv)


if __name__ == "__main__":
    main()