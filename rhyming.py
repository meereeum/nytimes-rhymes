from collections import defaultdict, Counter
import re
import string
import itertools
import random
import sys
import cPickle as pickle


def rhymable_sound(phons, accum=[], stresses='12'):
    """Returns string of rhymable word segment (starting with rightmost vowel phoneme with stress in stresses, if exists) - if no vowel sounds, returns original"""
    if len(phons) == 1 and not accum:
        return phons[0]
    if not phons:
        if stresses=='12':
            return rhymable_sound(accum, stresses='0')
        else:
            return ''.join(accum)
    if phons[-1][-1] in stresses: # vowel phoneme with given stress
        return ''.join(phons[-1:] + accum)
    else:
        return rhymable_sound(phons[:-1], accum = (phons[-1:] + accum), stresses=stresses)


def is_vowel(phoneme):
    """Returns True if phoneme is a vowel sounds, else False"""
    return phoneme[-1] in '012'


#def n_syllables(word):
    #"""Return number of syllables (based on # vowel sounds) in first pronounciation of word"""
    #return len(phon for phon in d_phonemes[word][0] if is_vowel(phon))


def n_pronounciations(word):
    """Returns number of specified pronouncations"""
    return len(d_phonemes[word])


def get_rhymes(word):
    """Given word, returns list of rhyming word strings (or empty list if DNE)"""
    try:
        return [ rhyme for pronunciation in d_phonemes[word]
                 for rhyme in d_rhymes[rhymable_sound(pronunciation)] if rhyme != word ]
    except(KeyError):
        return []


def top_phonemes(word):
    """Given word (str), returns list of phonemes in primary pronunciation of word"""
    word = word.upper()
    # return original (as single elem of list) if not in dictionary
    return d_phonemes.get(word, [[word]])[0]


def do_rhyme(word1, word2):
    """Given two word strings, returns True IFF words rhyme"""
    word1.upper()
    word2.upper()
    assert (word1 in get_rhymes(word2)) == (word2 in get_rhymes(word1))
    return word1 in get_rhymes(word2)


#def text2phons(text, sep=' '):
    #return r'{s}\b{s}'.format(s=sep).join( sep.join(top_phonemes(word)) for word in text.split() )


class Poem():
    def __init__(self, text, print_rhymable=False, print_rhymes=False,
                 stress_matters=True, print_individual=False, print_combined=True):
        self.print_individual = print_individual
        self.print_combined = print_combined
        self.l_words_only = text.translate(None,string.punctuation).upper().split()

        if stress_matters:
            self.l_rhymable = [ rhymable_sound(top_phonemes(word))
                                for word in self.l_words_only ]
        else:
            self.l_rhymable = [ ''.join(char for char in rhymable_sound(top_phonemes(word))
                                if char not in '012') for word in self.l_words_only ]

        self.potential_rhymes = [ k for k,v in Counter(self.l_rhymable).iteritems() if v>1 ]

        if print_rhymable:
            print '\nrhymables: {}\n'.format(l_rhymable)
        if print_rhymes:
            print '\nrhymes (?): {}\n'.format(potential_rhymes)

        self.rhyming_idxs = []
        self.combined_idxs = []
        if self.potential_rhymes:
            self.find_rhyming_idxs()
        if len(self.rhyming_idxs) > 1:
            self.combine_idxs()


    def __len__(self):
        return len(self.l_words_only)


    def __repr__(self):
        poems = []
        if self.print_individual:
            for rhyme in self.rhyming_idxs:
                for idxs in rhyme:
                    poem = self.partition([i+1 for i in idxs])
                    poems.append(poem)
        if self.print_combined:
            for rhyme in self.combined_idxs:
                for idxs in rhyme:
                    poem = self.partition([i+1 for i in idxs])
                    poems.append(poem)
        str_poem = '\n\n'
        for p in poems:
            str_poem += '\n'.join(' '.join(line) for line in p)
            str_poem += '\n\n'
        return str_poem


    def partition(self, idxs):
        """Slice word list by given list of indices and return as list of lists"""
        if not idxs:
            return [self.l_words_only]
        idxs.sort()
        if idxs[0] == 0:
            idxs = idxs[1:]
        if idxs[-1] == len(self):
            idxs = idxs[:-1]
        to_slice = zip([0]+idxs, idxs+[len(self)])
        return [ self.l_words_only[i:j] for (i,j) in to_slice ]


    def find_rhyming_idxs(self):
        for rhyme in self.potential_rhymes:
            idxd_rhymes = [ (i, self.l_words_only[i]) for i,rhymable
                            in enumerate(self.l_rhymable) if rhymable == rhyme ]
            # group rhymable words by word to prevent self-rhyming
            nonredundant_idxs = [ [word[0] for word in grouped]
                                for _,grouped in itertools.groupby(
                                        sorted(idxd_rhymes), key=lambda x: x[1]) ]
            if len(nonredundant_idxs) > 1:
                self.rhyming_idxs.append( [idxs for idxs in
                                           itertools.product(*nonredundant_idxs)] )


    def combine_idxs(self):
        combos = itertools.product(*self.rhyming_idxs)
        self.combined_idxs += [list(itertools.chain.from_iterable(c) for c in combos)]


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
        phonemes = d_phonemes[word][0]
        return len( [p for p in phonemes if is_vowel(p)] )
    except(IndexError, KeyError):
        # if word not in CMU dict, guess syllables based on # consecutive vowel groups
        # += 1 for trailing `y`
        return len( re.findall(r'[AEIOU]+', word) ) + (word[-1] == 'Y')


def choose_poem(lst):
    """Outputs poem with best syllables from list of potential poems"""
    def syllable_difference(a,b):
        return abs(n_syllables(a) - n_syllables(b))
    def metric(lines):
        # lower metric means fewer lines (overflow) & closer meter between lines
        return len(lines) + syllable_difference(lines[0], lines[1])

    if len(lst) == 1:
        best_idx = 0
    else:
        metrics = [ (i, metric(lines)) for i,lines in enumerate(lst) ]
        #metrics.sort(key=lambda x: x[1])
        #best = lst[metrics[0][0]]
        best_idx = min(metrics, key=lambda x: x[1])[0]

    return lst[best_idx]


def print_poem(lines):
    print
    print '\n'.join(' '.join(line) for line in lines)
    print


def populate_dicts(phonemes_in='./dict_phonemes.pickled',
                   rhymes_in='./dict_rhymes.pickled'):
    global d_phonemes
    global d_rhymes
    with open(phonemes_in, 'r') as f:
        d_phonemes = pickle.load(f)
    with open(rhymes_in, 'r') as f:
        d_rhymes = pickle.load(f)


TEXT = 'rihanna is going to a movie. tis the season to be groovy.'
# USAGE: $ cat scratch.txt | tr '\n' ' ' | sed -e's/^/"/' -e's/$/"/' | xargs python rhyming.py | gsed -re 's/([^^])$/\1!/' | say -v Vicki

if __name__ == "__main__":
    TEXT = sys.argv[1]
    PHONEME_DICT = './dict_phonemes.pickled'
    RHYMING_DICT = './dict_rhymes.pickled'
    populate_dicts(PHONEME_DICT, RHYMING_DICT)
    #import code; code.interact(local=locals())

    print Poem(TEXT)

    #for p in poems:
        #print_poem(p)
#
    #print '\nBEST!!!~~~~!!!!*****! ......'
    #print_poem( choose_poem(poems) )

    #poem = choose_poem(poems)
    #print_poem(poem[])

    #import code; code.interact(local=locals())
