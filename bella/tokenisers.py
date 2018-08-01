'''
Functions that tokenise text and returns the list of tokens all of which are
Strings.

Functions:

1. :py:func:`bella.tokenisers.whitespace` -- tokenises on whitespace.
2. :py:func:`bella.tokenisers.ark_twokenize` -- A Twitter tokeniser from
   `CMU Ark <https://github.com/brendano/ark-tweet-nlp>`_
3. :py:func:`bella.tokenisers.stanford` -- Stanford tokeniser from
   `CoreNLP <https://nlp.stanford.edu/software/tokenizer.html>`_
4. :py:func:`bella.tokenisers.moses` -- Tokeniser used in the
   `moses toolkit <https://github.com/moses-smt>`_
'''
from typing import List

from mosestokenizer import MosesTokenizer
import twokenize

from bella import stanford_tools


def whitespace(text: str) -> List[str]:
    '''
    Tokenises on whitespace.

    :param text: A string to be tokenised.
    :returns: A list of tokens where each token is a String.
    '''

    if isinstance(text, str):
        return text.split()
    raise ValueError(f'The paramter must be of type str not {type(text)}')


def ark_twokenize(text: str) -> List[str]:
    '''
    A Twitter tokeniser from
    `CMU Ark <https://github.com/brendano/ark-tweet-nlp>`_

    This is a wrapper of
    `this <https://github.com/Sentimentron/ark-twokenize-py>`_

    :param text: A string to be tokenised.
    :returns: A list of tokens where each token is a String.
    '''

    if isinstance(text, str):
        return twokenize.tokenizeRawTweetText(text)
    raise ValueError(f'The paramter must be of type str not {type(text)}')


def stanford(text: str) -> List[str]:
    '''
    Stanford tokeniser from
    `CoreNLP <https://nlp.stanford.edu/software/tokenizer.html>`_

    Requires CoreNLP server to be running.

    :param text: A string to be tokenised.
    :returns: A list of tokens where each token is a String.
    '''
    if isinstance(text, str):
        return stanford_tools.tokenise(text)
    raise ValueError(f'The paramter must be of type str not {type(text)}')


def moses(text: str) -> List[str]:
    '''
    Tokeniser used in the `moses toolkit <https://github.com/moses-smt>`_

    This is a wrapper of `this <https://pypi.org/project/mosestokenizer/>`_

    :param text: A string to be tokenised.
    :returns: A list of tokens where each token is a String.
    '''
    if isinstance(text, str):
        with MosesTokenizer('en') as tokeniser:
            return tokeniser(text)
    raise ValueError(f'The paramter must be of type str not {type(text)}')
