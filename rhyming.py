from collections import defaultdict

def parse_words(file_in):
    """Parse CMUdict into dictionary of (string, list of lists) items
    Key: word
    Value: [ [syllables for pronounciation 0], [syllables for pronounciation 1], ... ]"""
    d_words = defaultdict(list)
    with open(file_in) as f:
        for line in f:
            if line[:3] != ';;;':
                split = line.strip().split()
                word, sylls = (split[0], split[1:])
                if word[-1] == ')': # word is alternate pronounciation
                    word = word[:-3]
                d_words[word].append(sylls)
    return d_words


def is_vowel(syll):
    """Returns True if syllable is a vowel sounds, else False"""
    return syll[-1] in '012'


def n_syllables(word):
    """Return number of syllables (based on # vowel sounds) in first pronounciation of word"""
    return len(syll for sylls in d_words[word][0] if is_vowel(syll))


def n_pronounciations(word):
    """Returns number of specified pronouncations"""
    return len(d_words[word])


def rhymable_sound(sylls, accum=''):
    """Returns string of rhymable word segment (starting with rightmost vowel sound with stress>0, if exists)"""
    if not sylls:
        return ''.join(accum)
    if sylls[-1][-1] in '12': # stressed vowel
        return ''.join(sylls[-1] + accum)
    else:
        return rhymable_sound(sylls[:-1], sylls[-1] + accum)


def find_rhymes():
    d_rhymes = defaultdict(list)
    #iter_rhymes = {k: [rhymabe_sound(v) for v in vs] for k,vs in d_words.iteritems()}
    for k,vs in d_words.iteritems():
        for v in vs:
            d_rhymes[rhymable_sound(v)].append(k)
    return {k: v for k,v in d_rhymes if len(v) > 1} # { 'rhymable sound': ['word1', 'word2', ...] }


INFILE = './cmudict-0.7b'

if __name__ == "__main__":
    global d_words
    d_words = parse_words(INFILE)
    d_rhymes = find_rhymes()
    import code; code.interact(local=locals())
