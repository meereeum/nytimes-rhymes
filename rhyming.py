import itertools
import string
import cPickle as pickle

class rhymingDict():
    def __init__(self, phonemes_in = './words/dict_phonemes.pickled')#, rhymes_in='./words/dict_rhymes.pickled')
        with open(phonemes_in, 'r') as f:
            self.d_phonemes = pickle.load(f)
        #with open(rhymes_in, 'r') as f:
            #self.d_rhymes = pickle.load(f)

        # add support for digits
        nums =  '0123456789'
        num_txt = ['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE']
        num_phons = [[self.topPhonemes(n)] for n in num_txt]
        self.d_phonemes.update(itertools.izip(nums,num_phons))


    def n_pronounciations(self, word):
        """Returns number of specified pronouncations"""
        return len(self.d_phonemes[word])


    def getRhymes(self, word):
        """Given word, returns list of rhyming word strings (or empty list if DNE)"""
        try:
            return [ rhyme for pronunciation in self.d_phonemes[word]
                    for rhyme in self.d_rhymes[self.rhymableSound(pronunciation)]
                     if rhyme != word ]
        except(KeyError):
            return []


    def topPhonemes(self, word):
        """Given word (str), returns list of phonemes in primary pronunciation of word"""
        # if word is number ending in 1-9, find phonemes for final number
        if all([char in (str(n) for n in xrange(1,10)) for char in word]):
            word = word[-1]
        word = word.upper()
        # return original (as single elem of list) if not in dictionary
        return self.d_phonemes.get(word, [[word]])[0]


    def doRhyme(self, word1, word2):
        """Given two word strings, returns True IFF words rhyme"""
        word1.upper()
        word2.upper()
        assert (word1 in self.getRhymes(word2)) == (word2 in self.getRhymes(word1))
        return word1 in self.getRhymes(word2)


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
            return len( [p for p in phonemes if self.isVowel(p)] )
        except(IndexError, KeyError):
            # if word not in CMU dict, guess syllables based on # consecutive vowel groups
            # += 1 for trailing `y`
            return len( re.findall(r'[AEIOU]+', word) ) + (word[-1] == 'Y')


    #def text2phons(text, sep=' '):
        #return r'{s}\b{s}'.format(s=sep).join( sep.join(topPhonemes(word)) for word in text.split() )


    def rhymableSound(self, phons, accum=[], stresses='12'):
        """Returns string of rhymable word segment (starting with rightmost vowel phoneme with stress in stresses, if exists) - if no vowel sounds, returns original"""
        if len(phons) == 1 and not accum:
            return phons[0]
        if not phons:
            if stresses=='12':
                return self.rhymableSound(accum, stresses='0')
            else:
                return ''.join(accum)
        if phons[-1][-1] in stresses: # vowel phoneme with given stress
            return ''.join(phons[-1:] + accum)
        else:
            return self.rhymableSound(phons[:-1], accum = (phons[-1:] + accum), stresses=stresses)


    def isVowel(self, phoneme):
        """Returns True if phoneme is a vowel sounds, else False"""
        return (phoneme[-1] in '012') and (phoneme[0] not in '0123456789')
