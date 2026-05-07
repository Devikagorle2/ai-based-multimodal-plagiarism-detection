def count_vowels(text):
    vowels = 'aeiouAEIOU'
    return sum(1 for c in text if c in vowels)
