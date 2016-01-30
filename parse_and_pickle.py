from collections import defaultdict
import cPickle as pickle
from rhyming import rhymableSound


def parseWords(file_in):
    """Parse CMUdict into dictionary of (string, list of lists) items
    Key: word
    Value: [ [phonemes for pronounciation 0], [phonemes for pronounciation 1], ... ]"""
    d_phonemes = defaultdict(list)
    with open(file_in) as f:
        for line in f:
            if line[:3] != ';;;':
                split = line.strip().split()
                word, phonemes = (split[0], split[1:])
                if word[-1] == ')': # word is alternate pronounciation
                    word = word[:-3]
                d_phonemes[word].append(phonemes)
    return d_phonemes


def findAllRhymes(indict):
    """Given dictionary of phonemes, returns dictionary of
    { 'rhymable sound': ['word1', 'word2', ...] }"""
    d_rhymes = defaultdict(list)
    for k,vs in indict.iteritems():
        for v in vs:
            d_rhymes[rhymableSound(v)].append(k)
    return { k: v for k,v in d_rhymes.iteritems() if len(v) > 1 }


if __name__ == "__main__":
    INFILE = './words/cmudict-0.7b'
    OUTFILES = ('./words/dict_phonemes.pickled', './words/dict_rhymes.pickled')

    d_phonemes = parseWords(INFILE)
    d_rhymes = findAllRhymes(d_phonemes)

    for file_out, d in zip(OUTFILES, (d_phonemes, d_rhymes)):
        with open(file_out, 'w') as f:
            pickle.dump(d, f, pickle.HIGHEST_PROTOCOL)
