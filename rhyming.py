from collections import defaultdict, Counter
import re
import string
import itertools
import sys
import cPickle as pickle
import numpy as np


class rhymingDict():
    def __init__(self, phonemes_in='./words/dict_phonemes.pickled'):#, rhymes_in='./words/dict_rhymes.pickled')
        with open(phonemes_in, 'r') as f:
            self.d_phonemes = pickle.load(f)

        # add support for digits
        nums =  '0123456789'
        num_txt = ['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE']
        num_phons = [[self.top_phonemes(n)] for n in num_txt]
        self.d_phonemes.update(itertools.izip(nums,num_phons))

        #with open(rhymes_in, 'r') as f:
            #self.d_rhymes = pickle.load(f)


    def n_pronounciations(self, word):
        """Returns number of specified pronouncations"""
        return len(self.d_phonemes[word])


    def get_rhymes(self, word):
        """Given word, returns list of rhyming word strings (or empty list if DNE)"""
        try:
            return [ rhyme for pronunciation in self.d_phonemes[word]
                    for rhyme in self.d_rhymes[self.rhymable_sound(pronunciation)] if rhyme != word ]
        except(KeyError):
            return []


    def top_phonemes(self, word):
        """Given word (str), returns list of phonemes in primary pronunciation of word"""
        # if word is number ending in 1-9, find phonemes for final number
        if all([char in (str(n) for n in xrange(1,10)) for char in word]):
            word = word[-1]
        word = word.upper()
        # return original (as single elem of list) if not in dictionary
        return self.d_phonemes.get(word, [[word]])[0]


    def do_rhyme(self, word1, word2):
        """Given two word strings, returns True IFF words rhyme"""
        word1.upper()
        word2.upper()
        assert (word1 in self.get_rhymes(word2)) == (word2 in self.get_rhymes(word1))
        return word1 in self.get_rhymes(word2)


    def n_syllables(self, text):
        """Given string or list of strings (i.e. words), returns int = number of syllables"""
        if isinstance(text, str):
            text = text.translate(None,string.punctuation).upper().split()
        if isinstance(text, list):
            return sum(self.syllablesInWord(w) for w in text)
        else:
            raise(TypeError)


    def syllablesInWord(self, word):
        word = word.upper()
        try:
            phonemes = self.d_phonemes[word][0]
            return len( [p for p in phonemes if self.is_vowel(p)] )
        except(IndexError, KeyError):
            # if word not in CMU dict, guess syllables based on # consecutive vowel groups
            # += 1 for trailing `y`
            return len( re.findall(r'[AEIOU]+', word) ) + (word[-1] == 'Y')


    #def text2phons(text, sep=' '):
        #return r'{s}\b{s}'.format(s=sep).join( sep.join(top_phonemes(word)) for word in text.split() )


    def rhymable_sound(self, phons, accum=[], stresses='12'):
        """Returns string of rhymable word segment (starting with rightmost vowel phoneme with stress in stresses, if exists) - if no vowel sounds, returns original"""
        if len(phons) == 1 and not accum:
            return phons[0]
        if not phons:
            if stresses=='12':
                return self.rhymable_sound(accum, stresses='0')
            else:
                return ''.join(accum)
        if phons[-1][-1] in stresses: # vowel phoneme with given stress
            return ''.join(phons[-1:] + accum)
        else:
            return self.rhymable_sound(phons[:-1], accum = (phons[-1:] + accum), stresses=stresses)


    def is_vowel(self, phoneme):
        """Returns True if phoneme is a vowel sounds, else False"""
        return (phoneme[-1] in '012') and (phoneme[0] not in '0123456789')




class Poem():
    def __init__(self, text, d_phonemes, stress_matters=True, ignore_plural=True,
                 print_rhymable=False, print_rhymes=False, print_individual=False, print_combined=True):
        self.d_phonemes = d_phonemes
        self.print_individual = print_individual
        self.print_combined = print_combined

        self.l_words = text.split()
        self.l_words_only = text.translate(None,string.punctuation).upper().split()

        # process rhymable text according to options
        if stress_matters:
            self.l_rhymable = [ d_phonemes.rhymable_sound(d.top_phonemes(word))
                                for word in self.l_words_only ]
        else:
            self.l_rhymable = [ ''.join(char for char in d_phonemes.rhymable_sound(d.top_phonemes(word))
                                if char not in '012') for word in self.l_words_only ]
        if ignore_plural:
            self.l_rhymable = [ word[:-1] if word[-1] in 'ZS' else word for word in self.l_rhymable ]

        print self.l_rhymable


        # find rhymes
        self.potential_rhymes = [ k for k,v in Counter(self.l_rhymable).iteritems() if v>1 ]

        if print_rhymable:
            print '\nrhymables: {}\n'.format(self.l_rhymable)
        if print_rhymes:
            print '\nrhymes (?): {}\n'.format(self.potential_rhymes)

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
        # if one rhyme only, print single rhyme regardless of optional bool
        if not self.combined_idxs:
            self.print_individual = True
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
            return [self.l_words]
        idxs.sort()
        if idxs[0] == 0:
            idxs = idxs[1:]
        if idxs[-1] == len(self):
            idxs = idxs[:-1]
        to_slice = zip([0]+idxs, idxs+[len(self)])
        return [ self.l_words[i:j] for (i,j) in to_slice ]


    def find_rhyming_idxs(self):
        """Identify indices corresponding to true rhymes (non-self) among
        potential rhymes"""
        for rhyme in self.potential_rhymes:
            idxd_rhymes = [ (i, self.l_words_only[i]) for i,rhymable
                            in enumerate(self.l_rhymable) if rhymable == rhyme ]
            # group rhymable words by word to prevent self-rhyming
            nonredundant_idxs = [ [word[0] for word in grouped]
                                for _,grouped in itertools.groupby(
                                        sorted(idxd_rhymes), key=lambda x: x[1]) ]
            if len(nonredundant_idxs) > 1:
                # list of lists
                self.rhyming_idxs.append( [idxs for idxs in
                                           itertools.product(*nonredundant_idxs)] )


    def combine_idxs(self):
        """"""
        combos = itertools.product(*self.rhyming_idxs)
        self.combined_idxs += [list(itertools.chain.from_iterable(c) for c in combos)]


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



TEXT = 'rihanna is going to a movie. tis the season to be groovy.'
# USAGE: $ cat scratch.txt | tr '\n' ' ' | sed -e's/^/"/' -e's/$/"/' | xargs python rhyming.py | gsed -re 's/([^^])$/\1!/' | say -v Vicki

if __name__ == "__main__":
    TEXT = sys.argv[1]
    PHONEME_DICT = './words/dict_phonemes.pickled'
    RHYMING_DICT = './words/dict_rhymes.pickled'
    #import code; code.interact(local=locals())

    d = rhymingDict(PHONEME_DICT)#, RHYMING_DICT)

    print Poem(TEXT, d_phonemes=d, print_rhymable=True, print_rhymes=True)


    #print '\nBEST!!!~~~~!!!!*****! ......'
    #print_poem( choose_poem(poems) )
