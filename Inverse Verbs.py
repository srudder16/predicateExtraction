import csv
from spellchecker import SpellChecker


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


def check_spelling(verbs):
    """
    Check and correct spelling of verbs

    Args:
        verbs (list): List of verbs to check

    Returns:
        dict: Dictionary mapping original verbs to corrected ones
    """
    spell = SpellChecker()
    corrections = {}

    for verb in verbs:
        if not verb:
            continue

        # Check if the verb is misspelled
        misspelled = spell.unknown([verb.lower()])
        if misspelled:
            # Get the most likely correction
            correction = spell.correction(verb.lower())
            if correction and correction != verb.lower():
                corrections[verb] = correction

    return corrections


def process_verbs_from_csv(input_csv_path, output_csv_path=None, check_spelling_flag=True):
    """
    Read verbs from a CSV file, generate their inverse forms, and optionally write to a new CSV

    Args:
        input_csv_path (str): Path to the input CSV file containing verbs
        output_csv_path (str, optional): Path to save the output CSV. If None,
                                         results are only returned but not saved.
        check_spelling_flag (bool): If True, check and correct spelling of verbs

    Returns:
        dict: Dictionary mapping each verb to its inverse form
    """
    verbs = []
    try:
        # Try to read the CSV file - first check if it has headers
        with open(input_csv_path, 'r', newline='') as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            has_header = csv.Sniffer().has_header(sample)

            reader = csv.reader(csvfile)
            if has_header:
                next(reader)  # Skip header if present

            for row in reader:
                if row:  # Ensure row is not empty
                    verbs.append(row[0].strip())  # Assume the verb is in the first column

    except FileNotFoundError:
        print(f"Error: File '{input_csv_path}' not found.")
        return {}
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return {}

    # Dictionary to track original and corrected verbs
    corrections = {}
    applied_corrections = False

    # Perform spell checking if enabled
    if check_spelling_flag:
        try:
            corrections = check_spelling(verbs)
            if corrections:
                print("\nPossible spelling errors detected:")
                print("{:<15} {:<15}".format("Original", "Correction"))
                print("-" * 30)
                for orig, corr in corrections.items():
                    print("{:<15} {:<15}".format(orig, corr))

                # Ask user if they want to apply corrections
                choice = input("\nApply these corrections? (y/n): ")
                if choice.lower() == 'y':
                    # Apply corrections to the verbs list
                    verbs = [corrections.get(v, v) for v in verbs]
                    applied_corrections = True
                    print("Corrections applied.")
                else:
                    # If user chooses not to apply corrections, clear the corrections dictionary
                    corrections = {}
        except ImportError:
            print("Spellchecker library not found. Install using: pip install pyspellchecker")
            print("Continuing without spell checking...")

    # Generate inverse for each verb
    results = {}
    original_to_corrected = {}

    for i, verb in enumerate(verbs):
        if not verb:  # Skip empty strings
            continue

        # Keep track of original and possibly corrected verbs
        original_verb = list(corrections.keys())[
            list(corrections.values()).index(verb)] if verb in corrections.values() else verb
        original_to_corrected[original_verb] = verb

        results[verb] = get_inverse_verb(verb)

    # Write results to output CSV if specified
    if output_csv_path:
        try:
            with open(output_csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Add spellcheck columns if corrections were made
                if applied_corrections and corrections:
                    writer.writerow(['Original', 'Corrected', 'Inverse'])

                    # For each original verb, write the corrected version and its inverse
                    for original, corrected in original_to_corrected.items():
                        if original != corrected:  # This is a corrected verb
                            writer.writerow([original, corrected, results[corrected]])
                        else:  # This verb had no correction
                            writer.writerow([original, '', results[original]])
                else:
                    writer.writerow(['Verb', 'Inverse'])  # Write header
                    for verb, inverse in results.items():
                        writer.writerow([verb, inverse])

            print(f"Results saved to {output_csv_path}")
        except Exception as e:
            print(f"Error writing to output file: {e}")

    # Print results in a table-like format
    if results:
        print("\nInverse Verbs:")

        # Print with spellcheck info if corrections were applied
        if applied_corrections and corrections:
            print("{:<12} {:<12} {:<15}".format("Original", "Corrected", "Inverse"))
            print("-" * 40)
            for original, corrected in original_to_corrected.items():
                if original != corrected:  # This is a corrected verb
                    print("{:<12} {:<12} {:<15}".format(original, corrected, results[corrected]))
                else:  # This verb had no correction
                    print("{:<12} {:<12} {:<15}".format(original, "", results[original]))
        else:
            print("{:<12} {:<15}".format("Verb", "Inverse"))
            print("-" * 27)
            for verb, inverse in results.items():
                print("{:<12} {:<15}".format(verb, inverse))
    else:
        print("No verbs found in the input file.")

    return results


def save_spelling_corrections(corrections, output_path):
    """
    Save spelling corrections to a separate CSV file

    Args:
        corrections (dict): Dictionary of original words and their corrections
        output_path (str): Path to save the corrections CSV
    """
    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Original', 'Correction'])
            for original, correction in corrections.items():
                writer.writerow([original, correction])
        print(f"Spelling corrections saved to {output_path}")
    except Exception as e:
        print(f"Error saving spelling corrections: {e}")


if __name__ == "__main__":
    # Example usage
    input_file = "extracted_verbs.csv"  # CSV file with verbs in the first column
    output_file = "inverse_verbs.csv"  # Output file to save results
    corrections_file = "spelling_corrections.csv"  # File to save spelling corrections

    # Process verbs and generate inverses
    inverse_verbs = process_verbs_from_csv(input_file, output_file, check_spelling_flag=True)

    # You can also use the function without saving to a file
    # inverse_verbs = process_verbs_from_csv(input_file)