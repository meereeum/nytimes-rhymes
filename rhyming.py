from collections import defaultdict, Counter, namedtuple
import re
import string
import itertools
import random

def parse_words(file_in):
    """Parse CMUdict into dictionary of (string, list of lists) items
    Key: word
    Value: [ [phonemes for pronounciation 0], [phonemes for pronounciation 1], ... ]"""
    d_words = defaultdict(list)
    with open(file_in) as f:
        for line in f:
            if line[:3] != ';;;':
                split = line.strip().split()
                word, phonemes = (split[0], split[1:])
                if word[-1] == ')': # word is alternate pronounciation
                    word = word[:-3]
                d_words[word].append(phonemes)
    return d_words


def is_vowel(phoneme):
    """Returns True if phoneme is a vowel sounds, else False"""
    return phoneme[-1] in '012'


#def n_syllables(word):
    #"""Return number of syllables (based on # vowel sounds) in first pronounciation of word"""
    #return len(phon for phon in d_words[word][0] if is_vowel(phon))


def n_pronounciations(word):
    """Returns number of specified pronouncations"""
    return len(d_words[word])


def rhymable_sound(phons, accum=[], stresses='12'):
    """Returns string of rhymable word segment (starting with rightmost vowel phoneme with stress in stresses, if exists) - if no vowel sounds, returns original"""
    if not phons:
        if stresses=='12':
            return rhymable_sound(accum, stresses='0')
        else:
            return ''.join(accum)
    if phons[-1][-1] in stresses: # vowel phoneme with given stress
        return ''.join(phons[-1:] + accum)
    else:
        return rhymable_sound(phons[:-1], accum = (phons[-1:] + accum), stresses=stresses)


def find_all_rhymes():
    """Returns dictionary of { 'rhymable sound': ['word1', 'word2', ...] }"""
    d_rhymes = defaultdict(list)
    #iter_rhymes = {k: [rhymabe_sound(v) for v in vs] for k,vs in d_words.iteritems()}
    for k,vs in d_words.iteritems():
        for v in vs:
            d_rhymes[rhymable_sound(v)].append(k)
    return { k: v for k,v in d_rhymes.iteritems() if len(v) > 1 }


def get_rhymes(word):
    """Given word, returns list of rhyming word strings (or empty list)"""
    try:
        return [ rhyme for v in d_words[word] for rhyme in d_rhymes[rhymable_sound(v)] if rhyme != word ]
    except(KeyError):
        return []


def top_phonemes(word):
    """Given word (string), returns list of phonemes in first pronunciation of word"""
    word = word.upper()
    # return original (as single elem of list) if not in dictionary
    return d_words.get(word, [word])[0]


def do_rhyme(word1, word2):
    """Given two word strings, returns bool True IFF words rhyme"""
    word1.upper()
    word2.upper()
    assert (word1 in get_rhymes(word2)) == (word2 in get_rhymes(word1))
    return word1 in get_rhymes(word2)


def text2phons(text, sep=' '):
    return r'{s}\b{s}'.format(s=sep).join( sep.join(top_phonemes(word)) for word in text.split() )


def text2poems(text, printable=True):
    l_words_only = text.translate(None,string.punctuation).upper().split()
    l_rhymable = [ rhymable_sound(top_phonemes(word)) for word in l_words_only ]
    rhyme_text = ' '.join(l_rhymable)
    potential_rhymes = ( k for k,v in Counter(l_rhymable).iteritems() if v>1 )
    #real_rhymes = []
    Word = namedtuple('Word',['i','txt'])

    def partition(lst, idxs):
        idxs.sort()
        if idxs[0] == 0:
            idxs = idxs[1:]
        if idxs[-1] == len(lst):
            idxs = idxs[:-1]
        to_slice = zip([0]+idxs, idxs+[len(lst)])
        return [lst[i:j] for (i,j) in to_slice]

    poems = []

    for rhyme in potential_rhymes:
        idxd_rhymes = [ Word(i, l_words_only[i]) for i,rhymable
                        in enumerate(l_rhymable) if rhymable == rhyme ]
        nonredundant_idxs = [ random.choice([x.i for x in grouped]) for _,grouped
                              in itertools.groupby( sorted(idxd_rhymes), key=lambda(x): x.txt ) ]
        if len(nonredundant_idxs) > 1:
            poem = partition(l_words_only, [i+1 for i in nonredundant_idxs])
            poems.append(poem)

    # shorter length means fewer lines (i.e. less overflow to third line not incorporating rhyme)
    poems.sort(key=len)

    if printable:
        for poem in poems:# set(poems):
            print
            print '\n'.join(' '.join(line) for line in poem)
            print

    return poems


def n_syllables(text):
    """Given string or list of strings (i.e. words), returns int = number of syllables"""
    if isinstance(text, str):
        text = text.translate(None,string.punctuation).upper().split()
    if isinstance(text, list):
        return sum(syllablesInWord(w) for w in text)
    else:
        raise(TypeError)


def syllablesInWord(word):
    word = word.upper()
    try:
        phonemes = d_words[word][0]
        return len( [p for p in phonemes if is_vowel(p)] )
    except(IndexError, KeyError):
        # if word not in CMU dict, guess syllables based on # consecutive vowel groups
        # += 1 for trailing `y`
        return len( re.findall(r'[AEIOU]+', word) ) + (word[-1] == 'Y')


def choose_poem(lst, printable=True):
    """Outputs poem with best syllables from list of potential poems"""
    if len(lst) == 1:
        best = lst[0]
    else:
        def syllable_difference(a,b):
            return abs(n_syllables(a) - n_syllables(b))
        def metric(lines):
            return len(lines) + syllable_difference(lines[0], lines[1])
        metrics = [ (i, metric(lines)) for i,lines in enumerate(lst) ]
        metrics.sort(key=lambda x: x[1])
        best = lst[metrics[0][0]]

    if printable:
        print
        print '\n'.join(' '.join(line) for line in best)
        print

    return best


#def text2poem_regex(text, sep=' '):
    ##text = ('|').join(rhymable_sound(phons) for phons in d_words[word] for word in text.split())
    #l_words_only = text.translate(None,string.punctuation).upper().split()
    #rhyme_text = sep.join( rhymable_sound(top_phonemes(word)) for word in l_words_only )
#
    #print rhyme_text
    ## regexes for rhyming patterns
    ##pattern = re.compile(r'\b(?P<rhyme>\w+)\b.+\b(?P=rhyme)\b')
    #nongreedy = re.compile(r'(?P<pre>^.*?)\b(?P<rhyme>\w+)\b(?P<between>.+)\b(?P=rhyme)\b(?P<post>.*$)')
    #greedy = re.compile(r'(?P<pre>^.*)\b(?P<rhyme>\w+)\b(?P<between>.+)\b(?P=rhyme)\b(?P<post>.*$)')
    #patterns = (nongreedy, greedy)
#
    #matches = (re.search(pattern, rhyme_text) for pattern in patterns)
    #groups = ('pre', 'post', 'between')
#
    #poems = []
#
    #for match in matches:
        #d = match.groupdict()
        ## find indices separating rhyming parts
        #n_pre, n_post, n_between = ( len(d[k].split()) for k in groups )
        #rhyme_pair = tuple(l_words_only[i] for i in (n_pre, n_pre+n_between+1))
        #print "rhyming",rhyme_pair
        ## filter same-word rhymes
        #if rhyme_pair[0] == rhyme_pair[1]:
            #continue
#
        #idxs = ((0,n_pre+1), (n_pre+1, n_pre+n_between+2), (n_pre+n_between+2, n_pre+n_between+n_post+2))
        #lines = tuple( sep.join(l_words_only[i:j]) for (i,j) in idxs )
        #poems.append(lines)
#
    #for poem in set(poems):
        #print
        #print '\n'.join(poem)
        #print


def populate_dicts(filepath):
    global d_words
    global d_rhymes
    d_words = parse_words(filepath)
    d_rhymes = find_all_rhymes()


INFILE = './cmudict-0.7b'
TEXT = 'rihanna is going to a movie. tis the season to be groovy.'

if __name__ == "__main__":
    populate_dicts(INFILE)
    #import code; code.interact(local=locals())
    poems = text2poems(TEXT, printable=False)
    choose_poem(poems)
    #import code; code.interact(local=locals())
