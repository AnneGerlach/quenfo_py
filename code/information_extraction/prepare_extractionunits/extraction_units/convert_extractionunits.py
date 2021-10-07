"""Script contains several functions used to preprocess the passed texts, objects, strings etc."""

# ## Imports
import spacy
import re

from information_extraction.models import TextToken
from information_extraction.prepare_resources import get_entities, get_no_entities, get_modifier
from information_extraction.prepare_resources.convert_entities import normalize_entities

# load nlp-model for sentence detection, pos tagger and lemmatizer
nlp = spacy.load("de_core_news_sm")

# load variables
known_entities = list()
no_entities = list()
modifier = list()

# ##Functions

# Split into Sentences
def split_into_sentences(content: str) -> list:
    """Get ExtractionUnits:
        +++ Step 1: Split Paragraph into Sentences. Take use of SentenceRecognizer from Spacy.+++

        Parameters:
        -----------
        content: str
            Receives the content of an ClassifyUnit-Object

        Returns:
        --------
        list
            list of sentences from the ClassifyUnit-Content"""

    extractionunits = list()
    # Construction from class and apply the SentenceRecognizer

    list_extractionunits = nlp(content)

    for eu in list_extractionunits.sents:
        # Paragraphs with list items will be separated as single sentences
        splitted = __split_list_items(str(eu))
        extractionunits.extend(splitted)

    # returns list with sentences from ClassifyUnit
    return extractionunits


# Split list items into single sentences
def __split_list_items(sentence: str) -> list:
    extractionunits = list()
    # split sentence at empty lines
    splitted_eu = __split_at_empty_line(sentence)
    # regex for match any existing list item in the sentence
    list_item_regex = re.compile(r"^[0-9][\.| ]?|^[\+|\-|\*]")
    for string in splitted_eu:
        # remove whitespaces, tabstops etc.
        string = string.strip()
        # compare regex with given sentence
        m = re.match(list_item_regex, string)
        if m:
            # if regex matches, the list item is removed from the sentence
            string = string[m.end():]
            string = string.strip()
        if len(string) > 0 & __contains_only_word_characters(string):
            extractionunits.append(string)

    # returns the sentence without any list items
    return extractionunits


# check if sentence contains word characters
def __contains_only_word_characters(string: str) -> bool:
    # regex for word character
    word_regex = re.compile(r"\w")
    if re.match(word_regex, string):
        return True
    return False


def __split_at_empty_line(content: str) -> list:
    return content.split("\n")


# correct sentence
def normalize_sentence(sentence: str) -> str:
    """Get ExtractionUnits:
            +++ Step 2: Correct specific elements of the sentence. +++

            Parameters:
            -----------
            sentence: str
                Receives a sentence as potential ExtractionUnit

            Returns:
            --------
            str
                given string with corrections """

    # 'und'/'oder' in uppercase change to be lowercase
    if sentence.__contains__("UND"):
        sentence = sentence.replace("UND", "und")
    if sentence.__contains__("ODER"):
        sentence = sentence.replace("ODER", "oder")

    # 'und/oder' in sentence change to be 'oder'
    regex = re.compile(r"^.*( und[\-|\/| ][\/| ]?[ ]?oder )")
    m = re.match(regex, sentence)
    if m:
        sentence = sentence.replace(m.group(1), " oder ")

    # 'oder/und' in sentence change to be 'und'
    regex = re.compile(r"^.*( oder[\-|\/| ][\/| ]?[ ]?und )")
    m = re.match(regex, sentence)
    if m:
        sentence = sentence.replace(m.group(1), " und ")

    # normalizes dot or comma if there is a space before them but none after them
    # adds a space after dot or comma
    regex = re.compile(r"^.*(\s[\.|\,])(\w+)")
    m = re.match(regex, sentence)
    if m:
        # exception: .NET (Microsoft-Framework)
        if m.group(2).lower() != "net":
            sentence = sentence.replace(m.group(1), m.group(1) + " ")

    # if there is a comma or semicolon without a space between two words,
    # a space is inserted after the comma or semicolon
    regex = re.compile(r"^.*[A-Za-z]+([\,|\;])[A-Za-z]+")
    m = re.match(regex, sentence)
    if m:
        sentence = sentence.replace(m.group(1), m.group(1) + " ")

    # checks the sentence for occurrences of / and * followed by two word characters and preceded by a space character
    # and normalizes them
    # e.g. Entwickler *in -> Entwickler/in
    regex = re.compile(r"^.*(\s[\/|\*])(\w\w)")
    m = re.match(regex, sentence)
    if m:
        if m.group(2) != "in":
            sentence = sentence.replace(m.group(1), " ")
        else:
            sentence = sentence.replace(m.group(1), "/")

    return sentence


def get_token(sentence: str) -> list:
    tokens = list()

    pre_token =nlp(sentence)
    for token in pre_token:
        tokens.append(token.text)

    return tokens


# get POS-tag for each token of given sentence
def get_pos_tags(sentence: str) -> list:
    """Get ExtractionUnits:
                +++ Step 3: Get lexical data from tokens. +++

                Parameters:
                -----------
                sentence: str
                        Receives sentence as potential ExtractionUnit.

                Returns:
                --------
                list
                    list of POS-tags for each token"""
    pos_tags = list()

    pre_pos_tags = nlp(sentence)
    for token in pre_pos_tags:
        pos_tags.append(token.pos_)

    return pos_tags


# get lemma for each token of given sentence
def get_lemmata(sentence: str) -> list:
    """Get ExtractionUnits:
                    +++ Step 3: Get lexical data from tokens. +++

                    Parameters:
                    -----------
                    sentence: str
                        Receives sentence as potential ExtractionUnit.

                    Returns:
                    --------
                    list
                        list of lemma for each token"""
    lemmata = list()

    pre_lemmata = nlp(sentence)
    for token in pre_lemmata:
        lemmata.append(token.lemma_)

    return lemmata


def annotate_token(token: list, ie_mode: str) -> 'list[TextToken]':
    """Get ExtractionUnits:
                    +++ Step 4: Annotate tokens by comparing them with list of extraction errors,
                    modifiers and known extractions. +++

                    Parameters:
                    -----------
                        token: list of Token
                            Receives list with tokens from ExtractionUnit
                        ie_mode: str
                            Receives a string with the current extraction mode: competences or tools"""

    global known_entities, no_entities, modifier

    known_entities = get_entities(ie_mode)
    no_entities = get_no_entities(ie_mode)
    modifier = get_modifier()

    if known_entities:
        token = annotate_entities(token)
    if no_entities:
        token = annotate_negatives(token)
    if ie_mode != 'TOOLS' and modifier:
        token = annotate_modifier(token)

    return token


def annotate_entities(token: list) -> 'list[TextToken]':
    annotate_list = list()

    for i in range(len(token)):
        lemma = normalize_entities(token[i].lemma)
        # Anmerkung: Programm braucht für diesen Teil 4 Minuten länger bei query_limit = 500
        matched_entities = [known_entity for known_entity in known_entities if hash(known_entity.start_lemma) == hash(lemma)]
        for known_entity in matched_entities:
            if known_entity.is_single_word:
                token[i].set_ie_token(True)
                continue
            matches = False
            for j in range(len(known_entity.lemma_array)):
                if len(token) <= i + j:
                    matches = False
                    break
                matches = known_entity.lemma_array[j].__eq__(normalize_entities(token[i + j].lemma))
                if not matches:
                    break
            if matches:
                token[i].set_ie_token(True)
                token[i].tokensToCompleteInformationEntity = len(known_entity.lemma_array) - 1
            annotate_list.append(token[i])

    return annotate_list


def annotate_negatives(token: list) -> 'list[TextToken]':
    annotate_list = list()

    for i in range(len(token)):
        lemma = normalize_entities(token[i].lemma)
        if no_entities.__contains__(lemma):
            token[i].set_no_token(True)
        annotate_list.append(token[i])

    return annotate_list


def annotate_modifier(token: list) -> 'list[TextToken]':
    annotate_list = list()

    for i in range(len(token)):
        lemma = normalize_entities(token[i].lemma)
        matched_modifier = [m for m in modifier if hash(m.start_lemma) == hash(lemma)]
        for mod in matched_modifier:
            if mod.is_single_word:
                token[i].set_modifier_token(True)
                continue
            matches = False
            for j in range(len(mod.lemma_array)):
                if len(token) <= i + j:
                    matches = False
                    break
                matches = mod.lemma_array[j].__eq__(normalize_entities(token[i + j].lemma))
                if not matches:
                    break
            if matches:
                token[i].set_modifier_token(True)
                token[i].tokensToCompleteModifier = len(mod.lemma_array) - 1
        annotate_list.append(token[i])

    return annotate_list
