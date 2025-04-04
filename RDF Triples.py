import spacy
import re
from typing import List, Tuple, Dict, Optional


class RDFTripleExtractor:
    """
    Extracts RDF triples (subject-predicate-object) from text documents
    based on noun and verb relationships.
    """

    def __init__(self, model: str = "en_core_web_lg"):
        """
        Initialize the extractor with a spaCy model.

        Args:
            model: The spaCy model to use (default: en_core_web_lg for best results)
        """
        self.nlp = spacy.load(model)

    def preprocess_text(self, text: str) -> str:
        """
        Clean and prepare text for processing.

        Args:
            text: Raw text input

        Returns:
            Preprocessed text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Replace common abbreviations
        abbreviations = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'s": " is",
            "'m": " am",
            "'ll": " will"
        }

        for abbr, expanded in abbreviations.items():
            text = text.replace(abbr, expanded)

        return text

    def extract_triples(self, text: str) -> List[Dict[str, str]]:
        """
        Extract RDF triples from the given text.

        Args:
            text: Input text to process

        Returns:
            List of dictionaries, each containing subject, predicate, and object
        """
        text = self.preprocess_text(text)
        doc = self.nlp(text)
        triples = []

        # Process each sentence separately
        for sent in doc.sents:
            sentence_triples = self._extract_triples_from_sentence(sent)
            triples.extend(sentence_triples)

        return triples

    def _extract_triples_from_sentence(self, sent) -> List[Dict[str, str]]:
        """
        Extract triples from a single sentence.

        Args:
            sent: spaCy sentence span

        Returns:
            List of triples from the sentence
        """
        triples = []

        # Find the root verb of the sentence
        root = None
        for token in sent:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                root = token
                break

        if not root:
            return []

        # Extract subject
        subject = self._find_subject(root)
        if not subject:
            return []

        # Extract direct objects
        direct_objects = self._find_objects(root)

        # Create triples for each object
        for obj in direct_objects:
            if obj:
                triple = {
                    "subject": self._get_span_text(subject),
                    "predicate": root.lemma_,
                    "object": self._get_span_text(obj)
                }
                triples.append(triple)

        # Handle additional clause-level relationships
        for token in sent:
            # Find clauses that might contain additional triples
            if token.dep_ in ["ccomp", "xcomp", "advcl"] and token.pos_ == "VERB":
                clause_subject = self._find_subject(token) or subject
                clause_objects = self._find_objects(token)

                for obj in clause_objects:
                    if obj and clause_subject:
                        triple = {
                            "subject": self._get_span_text(clause_subject),
                            "predicate": token.lemma_,
                            "object": self._get_span_text(obj)
                        }
                        triples.append(triple)

        return triples

    def _find_subject(self, verb) -> Optional[spacy.tokens.Span]:
        """Find the subject related to a verb"""
        for child in verb.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                return self._expand_noun_phrase(child)
        return None

    def _find_objects(self, verb) -> List[spacy.tokens.Span]:
        """Find objects related to a verb"""
        objects = []

        for child in verb.children:
            if child.dep_ in ["dobj", "attr", "pobj"]:
                obj = self._expand_noun_phrase(child)
                if obj:
                    objects.append(obj)

            # Handle preposition + object
            elif child.dep_ == "prep":
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        # Include the preposition in the predicate
                        prep_obj = self._expand_noun_phrase(grandchild)
                        if prep_obj:
                            objects.append(prep_obj)

        return objects

    def _expand_noun_phrase(self, token) -> Optional[spacy.tokens.Span]:
        """Expand a noun to include its modifiers and form a complete noun phrase"""
        if not token or token.pos_ not in ["NOUN", "PROPN", "PRON"]:
            return None

        # Find the start and end indices of the expanded noun phrase
        start_idx = token.i
        end_idx = token.i + 1

        # Find the head of the noun phrase
        head = token
        while head.head.pos_ in ["NOUN", "PROPN"] and head.dep_ in ["compound", "amod"]:
            head = head.head
            end_idx = head.i + 1

        # Find all words that modify the noun
        for t in token.doc:
            if t.head == head or t.head == token:
                if t.dep_ in ["det", "amod", "compound", "nummod", "quantmod"] and t.i < start_idx:
                    start_idx = t.i
                elif t.dep_ in ["amod", "compound"] and t.i >= end_idx:
                    end_idx = t.i + 1

        return token.doc[start_idx:end_idx]

    def _get_span_text(self, span) -> str:
        """Get the text of a span with proper formatting"""
        if not span:
            return ""
        return span.text.strip()

    def to_rdf_format(self, triples: List[Dict[str, str]], format: str = "turtle") -> str:
        """
        Convert extracted triples to RDF format string.

        Args:
            triples: List of triples (dicts with subject, predicate, object)
            format: Output format ("turtle", "n-triples", or "xml")

        Returns:
            String representation in the requested RDF format
        """
        if not triples:
            return ""

        if format == "turtle":
            return self._to_turtle(triples)
        elif format == "n-triples":
            return self._to_n_triples(triples)
        elif format == "xml":
            return self._to_rdf_xml(triples)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_turtle(self, triples: List[Dict[str, str]]) -> str:
        """Convert triples to Turtle format"""
        output = "@prefix ex: <http://example.org/> .\n\n"

        # Group by subject
        subjects = {}
        for triple in triples:
            subj = triple["subject"]
            if subj not in subjects:
                subjects[subj] = []
            subjects[subj].append((triple["predicate"], triple["object"]))

        # Generate turtle representation
        for subject, predicates in subjects.items():
            # Create safe IDs for URIs
            subject_id = self._safe_uri(subject)
            output += f"ex:{subject_id}\n"

            for i, (predicate, obj) in enumerate(predicates):
                predicate_id = self._safe_uri(predicate)

                # Check if object looks like a literal or should be a URI
                if re.match(r'^[0-9]+$', obj) or obj.lower() in ["true", "false"]:
                    # Numeric or boolean
                    output += f"    ex:{predicate_id} {obj}"
                elif any(char in obj for char in ',."\'(){}[]'):
                    # Likely a literal
                    output += f'    ex:{predicate_id} "{obj}"'
                else:
                    # Likely a reference to another entity
                    obj_id = self._safe_uri(obj)
                    output += f"    ex:{predicate_id} ex:{obj_id}"

                if i < len(predicates) - 1:
                    output += " ;\n"
                else:
                    output += " .\n\n"

        return output

    def _to_n_triples(self, triples: List[Dict[str, str]]) -> str:
        """Convert triples to N-Triples format"""
        output = ""

        for triple in triples:
            subject_id = self._safe_uri(triple["subject"])
            predicate_id = self._safe_uri(triple["predicate"])
            obj = triple["object"]

            if any(char in obj for char in ',."\'(){}[]') or re.match(r'^[0-9]+$', obj):
                # Likely a literal
                output += f'<http://example.org/{subject_id}> <http://example.org/{predicate_id}> "{obj}" .\n'
            else:
                # Likely a reference
                obj_id = self._safe_uri(obj)
                output += f'<http://example.org/{subject_id}> <http://example.org/{predicate_id}> <http://example.org/{obj_id}> .\n'

        return output

    def _to_rdf_xml(self, triples: List[Dict[str, str]]) -> str:
        """Convert triples to RDF/XML format"""
        output = '<?xml version="1.0" encoding="UTF-8"?>\n'
        output += '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n'
        output += '         xmlns:ex="http://example.org/">\n\n'

        # Group by subject
        subjects = {}
        for triple in triples:
            subj = triple["subject"]
            if subj not in subjects:
                subjects[subj] = []
            subjects[subj].append((triple["predicate"], triple["object"]))

        # Generate RDF/XML
        for subject, predicates in subjects.items():
            subject_id = self._safe_uri(subject)
            output += f'  <rdf:Description rdf:about="http://example.org/{subject_id}">\n'

            for predicate, obj in predicates:
                predicate_id = self._safe_uri(predicate)

                if any(char in obj for char in ',."\'(){}[]') or re.match(r'^[0-9]+$', obj):
                    # Likely a literal
                    output += f'    <ex:{predicate_id}>{obj}</ex:{predicate_id}>\n'
                else:
                    # Likely a reference
                    obj_id = self._safe_uri(obj)
                    output += f'    <ex:{predicate_id} rdf:resource="http://example.org/{obj_id}"/>\n'

            output += '  </rdf:Description>\n\n'

        output += '</rdf:RDF>'
        return output

    def _safe_uri(self, text: str) -> str:
        """Convert text to a safe URI part"""
        # Remove special characters and replace spaces with underscores
        safe = re.sub(r'[^a-zA-Z0-9 ]', '', text)
        safe = safe.replace(' ', '_').lower()
        return safe


# Example usage
def example():
    # Initialize the extractor
    extractor = RDFTripleExtractor()

    # Sample text
    with open("ISO-15288_Section3_Final copy.txt", "r", encoding="utf-8") as file:
        text = file.read()
    # Save to files
    with open("output_turtle.ttl", "w", encoding="utf-8") as f:
        f.write(turtle)

    with open("output_ntriples.nt", "w", encoding="utf-8") as f:
        f.write(n_triples)

    with open("output_rdf.xml", "w", encoding="utf-8") as f:
        f.write(rdf_xml)

    # Extract triples
    triples = extractor.extract_triples(text)

    # Print the extracted triples
    print("Extracted Triples:")
    for t in triples:
        print(f"Subject: {t['subject']}")
        print(f"Predicate: {t['predicate']}")
        print(f"Object: {t['object']}")
        print()

    # Convert to RDF formats
    turtle = extractor.to_rdf_format(triples, "turtle")
    n_triples = extractor.to_rdf_format(triples, "n-triples")
    rdf_xml = extractor.to_rdf_format(triples, "xml")

    # Print Turtle format
    print("Turtle Format:")
    print(turtle)


if __name__ == "__main__":
    example()