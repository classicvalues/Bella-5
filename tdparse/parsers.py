'''
Functions that parse the annotated data that is being used in this project. The
annotated dataset are the following:

1. `Li Dong <http://goo.gl/5Enpu7>`_ which links to :py:func:`tdparse.parsers.dong`
2. Semeval parser
'''
import json
import os
import re
import xml.etree.ElementTree as ET

from tdparse.data_types import Target, TargetCollection

def dong(file_path):
    '''
    Given file path to the
    `Li Dong <https://github.com/bluemonk482/tdparse/tree/master/data/lidong>`_
    sentiment data it will parse the data and return it as a list of dictionaries.

    :param file_path: File Path to the annotated data
    :type file_path: String
    :returns: A TargetCollection containing Target instances.
    :rtype: TargetCollection
    '''

    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError('This file does not exist {}'.format(file_path))

    sentiment_range = [-1, 0, 1]

    sentiment_data = TargetCollection()
    with open(file_path, 'r') as dong_file:
        sent_dict = {}
        for index, line in enumerate(dong_file):
            divisible = index + 1
            line = line.strip()
            if divisible % 3 == 1:
                sent_dict['text'] = line
            elif divisible % 3 == 2:
                sent_dict['target'] = line
            elif divisible % 3 == 0:
                sentiment = int(line)
                if sentiment not in sentiment_range:
                    raise ValueError('The sentiment has to be one of the '\
                                     'following values {} not {}'\
                                     .format(sentiment_range, sentiment))
                sent_dict['sentiment'] = int(line)
                text = sent_dict['text'].lower()
                target = sent_dict['target'].lower()
                offsets = [match.span() for match in re.finditer(target, text)]
                if len(target.split()) > 1:
                    joined_target = ''.join(target.split())
                    offsets.extend([match.span()
                                    for match in re.finditer(joined_target, text)])
                sent_dict['spans'] = offsets
                sent_dict['target_id'] = str(len(sentiment_data))
                sent_target = Target(**sent_dict)
                sentiment_data.add(sent_target)
                sent_dict = {}
            else:
                raise Exception('Problem')
    return sentiment_data

def semeval(file_path):
    '''
    :param file_path: File path to the semeval data
    :type file_path: String
    :returns: A TargetCollection containing Target instances.
    :rtype: TargetCollection
    '''

    # Converts the sentiment tags from Strings to ints
    sentiment_mapper = {'conflict' : -2, 'negative' : -1,
                        'neutral' : 0, 'positive' : 1}
    def extract_aspect_terms(aspect_terms, sentence_id):
        '''
        :param aspect_terms: An aspectTerms element within the xml tree
        :param sentence_id: Id of the sentence that the aspects came from.
        :type aspect_terms: xml.etree.ElementTree.Element
        :type sentence_id: String
        :returns: A list of dictioanries containg id, span, sentiment and \
        target
        :rtype: list
        '''

        aspect_terms_data = []
        for index, aspect_term in enumerate(aspect_terms):
            aspect_term = aspect_term.attrib
            aspect_term_data = {}
            sentiment = sentiment_mapper[aspect_term['polarity']]
            aspect_id = '{}{}'.format(sentence_id, index)
            aspect_term_data['target_id'] = aspect_id
            aspect_term_data['target'] = aspect_term['term']
            aspect_term_data['sentiment'] = sentiment
            aspect_term_data['spans'] = [(aspect_term['from'],
                                          aspect_term['to'])]
            aspect_terms_data.append(aspect_term_data)
        return aspect_terms_data
    def add_text(aspect_data, text):
        '''
        :param aspect_data: A list of dicts containing `span`, `target` and \
        `sentiment` keys.
        :param text: The text of the sentence that is associated to all of the \
        aspects in the aspect_data list
        :type aspect_data: list
        :type text: String
        :returns: The list of dicts in the aspect_data parameter but with a \
        `text` key with the value that the text parameter contains
        :rtype: list
        '''

        for data in aspect_data:
            data['text'] = text
        return aspect_data

    tree = ET.parse(file_path)
    sentences = tree.getroot()
    all_aspect_term_data = TargetCollection()
    if sentences.tag != 'sentences':
        raise ValueError('The root of all semeval xml files should '\
                         'be sentences and not {}'\
                         .format(sentences.tag))
    for sentence in sentences:
        aspect_term_data = None
        text_index = None
        sentence_id = sentence.attrib['id']
        for index, data in enumerate(sentence):
            if data.tag == 'text':
                text_index = index
            elif data.tag == 'aspectTerms':
                aspect_term_data = extract_aspect_terms(data, sentence_id)
        if aspect_term_data is None:
            continue
        if text_index is None:
            raise ValueError('A semeval sentence should always have text '\
                             'semeval file {} sentence id {}'\
                             .format(file_path, sentence.attrib['id']))
        sentence_text = sentence[text_index].text
        aspect_term_data = add_text(aspect_term_data, sentence_text)
        for aspect in aspect_term_data:
            sent_target = Target(**aspect)
            all_aspect_term_data.add(sent_target)
    return all_aspect_term_data

def election(folder_path, include_dnr=False, include_additional=False):
    '''
    Data can be downloaded from 
    `FigShare <https://figshare.com/articles/EACL_2017_-_Multi-target_\
    UK_election_Twitter_sentiment_corpus/4479563/1>`_

    :param folder_path: Path to the folder containing the data after it has \
    been unziped and all folders within it have been unziped.
    :type folder_path: String
    :returns: A TargetCollection containing Target instances.
    :rtype: TargetCollection
    '''

    def get_file_data(folder_dir):
        '''
        :param folder_dir: File path to a folder containing JSON data files \
        where the file names is the datas ID
        :type folder_dir: String
        :returns: A dictionary of IDs as keys and JSON data as values
        :rtype: dict
        '''

        data = {}
        for file_name in os.listdir(folder_dir):
            file_path = os.path.join(folder_dir, file_name)
            tweet_id = file_name.rstrip('.json').lstrip('5')
            with open(file_path, 'r') as file_data:
                data[tweet_id] = json.load(file_data)
        return data

    def parse_tweet(tweet_data, anno_data, tweet_id):

        def get_offsets(entity, tweet_text, target):
            offset_shifts = [0, -1, 1]
            from_offset = entity['offset']
            for offset_shift in offset_shifts:
                from_offset_shift = from_offset + offset_shift
                to_offset = from_offset_shift + len(target)
                offsets = [(from_offset_shift, to_offset)]
                offset_text = tweet_text[from_offset_shift : to_offset].lower()
                if offset_text == target.lower():
                    return offsets
            raise ValueError('Offset {} does not match target text {}. Full '\
                             'text {}\nid {}'\
                             .format(from_offset, target, tweet_text, tweet_id))

        def fuzzy_target_match(tweet_text, target):
            low_target = target.lower()
            target_searches = [low_target, '[^\w]' + low_target,
                               '[^\w]' + low_target + '[^\w]',
                               low_target + '[^\w]', 
                               low_target.replace(' ', ''),
                               low_target.replace(" '", '')]
            for target_search in target_searches:
                target_matches = list(re.finditer(target_search, 
                                                  tweet_text.lower()))
                if len(target_matches) == 1:
                    return target_matches
            if tweet_id in set(['81211671026352128', '78689580104290305',
                                '81209490499960832']):
                return None
            if tweet_id == '75270720671973376' and target == 'kippers':
                return None
            if tweet_id == '65855178264686592' and target == 'tax':
                return None
            print(tweet_data)
            print(anno_data)
            raise ValueError('Cannot find the exact additional '\
                             'entity {} within the tweet {}'\
                             .format(target, tweet_text))



        target_instances = []
        tweet_id = str(tweet_id)
        tweet_text = tweet_data['content']
        target_ids = []
        # Parse all of the entities that have been detected automatically
        for entity in tweet_data['entities']:
            data_dict = {}
            target = entity['entity']
            target_ids.append(entity['id'])
            entity_id = str(entity['id'])
            data_dict['spans'] = get_offsets(entity, tweet_text, target)
            data_dict['target'] = entity['entity']
            data_dict['target_id'] = tweet_id + '#' + entity_id
            data_dict['sentence_id'] = tweet_id
            data_dict['sentiment'] = anno_data['items'][entity_id]
            if data_dict['sentiment'] == 'doesnotapply' and not include_dnr:
                continue
            data_dict['text'] = tweet_text
            target_instances.append(Target(**data_dict))
        # Parse all of the entities that have been selected by the user
        if include_additional:
            additional_data = anno_data['additional_items']
            if isinstance(additional_data, dict):
                for target, sentiment in additional_data.items():
                    target_matches = fuzzy_target_match(tweet_text, target)
                    if target_matches is None:
                        continue
                    target_id = max(target_ids) + 1
                    target_ids.append(target_id)
                    data_dict['spans'] = [target_matches[0].span()]
                    data_dict['target'] = target
                    data_dict['sentiment'] = sentiment
                    data_dict['text'] = tweet_text
                    data_dict['sentence_id'] = tweet_id
                    data_dict['target_id'] = tweet_id + '#' + str(target_id)
                    target_instances.append(Target(**data_dict))

        return target_instances

    def get_data(id_file, tweets_data, annos_data):
        targets = []
        with open(id_file, 'r') as id_data:
            for tweet_id in id_data:
                tweet_id = tweet_id.strip()
                tweet_data = tweets_data[tweet_id]
                anno_data = annos_data[tweet_id]
                targets.extend(parse_tweet(tweet_data, anno_data, tweet_id))
        return TargetCollection(targets)

    folder_path = os.path.abspath(folder_path)
    tweets_data = get_file_data(os.path.join(folder_path, 'tweets'))
    annotations_data = get_file_data(os.path.join(folder_path, 'annotations'))

    train_ids_file = os.path.join(folder_path, 'train_id.txt')
    train_data = get_data(train_ids_file, tweets_data, annotations_data)
    test_ids_file = os.path.join(folder_path, 'test_id.txt')
    test_data = get_data(test_ids_file, tweets_data, annotations_data)

    return train_data, test_data