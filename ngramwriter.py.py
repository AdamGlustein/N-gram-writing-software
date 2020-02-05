import utilities

def parse_story(file_name):
    '''     
    (str) -> list
    Takes a text file and parses the file, breaking text into individual tokens for analysis
    Ex. "The cat went to the sto{re!" -> ["the", "cat", "went", "to", "the", sto", "re", "!"]
    '''
    parsing = [] 
    f = open(file_name, "r")  
    text = f.read().lower()
    N = len(text) 
    # generate token
    token = ""
    for x in range(N):
        if text[x] == " " and token != "": # token ends with space
            parsing.append(token)
            token = ""
        if text[x] == "\n" and token != "": # token ends with newline
            parsing.append(token)
            token = ""            
        elif (text[x] != " " and text[x] != "\n"): # not white space
            last_char, valid_punc, bad_character = 0, 0, 0
            for V in utilities.VALID_PUNCTUATION:
                if text[x] == V:
                    valid_punc = 1            
            for B in utilities.BAD_CHARS:
                if text[x] == B:
                    bad_character = 1
            if x == N-1:
                last_char = 1
            if valid_punc: 
                if token != "":                 
                    parsing.append(token)
                token = ""
                parsing.append(text[x])
            elif bad_character:
                if token != "":                 
                    parsing.append(token)
                token = "" 
            elif last_char: # last but not punc or bad
                token += text[x]
                parsing.append(token)
                token = ""
            else: # normal char
                token += text[x]
              
    return parsing
    
def get_prob_from_count(counts): 
    '''     
    (list) -> list
    Takes a list of counts and returns the associated list of probabilities 
    Ex. [40, 60, 50, 30, 20] -> [0.2, 0.3, 0.25, 0.15, 0.1]
    '''    
    pmf = []
    csum = 0
    for i in counts: # getting total
        csum += i
    for i in range(len(counts)):
        pmf.append(counts[i]/csum)
    return pmf
    
def build_ngram_counts(words, n):
    '''     
    (list, int) -> dict
    Takes a list of tokens and returns a dictionary of N-grams created using those tokens
    Ex. ["the", "man", "ate"], 2 -> {("the", "man"): [["ate"], [1]]}
    '''     
    ngrams = {}
    for i in range(len(words)-n):
        key, counts, newwords = [], [], []
        temp = [newwords, counts]
        for x in range(n):
            key.append(words[i+x])
        key = tuple(key)
        if key in ngrams:
            continue
        else: # key not in ngram, need to create it 
            ngrams[key] = temp
            counts.append(1)
            newwords.append(words[i+n]) # add the next token after ngram           
            for k in range(i+1, len(words)-n): # check remainder of dictionary for more occurences 
                new = [] # create new key
                for l in range(n):
                    new.append(words[k+l])
                    
                if key == tuple(new): # repeat key, thus add to existing list
                    existing = False
                    for m in range(len(newwords)):
                        if words[k+n] == newwords[m]: # repeat word 
                            counts[m] += 1
                            existing = True
                    if existing:
                        continue
                    else: # word needs to be added to key
                        counts.append(1)
                        newwords.append(words[k+n])                        
    return ngrams
    
def prune_ngram_counts(counts, prune_len):
    '''     
    (dict, int) -> dict
    Takes a dictionary of n-grams and prunes it, keeping only the k most frequent words where k is the second parameter
    Ex. {("i", "will"): [["go", "leave"], [2,1]]}, 1 -> {("i", "will"): [["go"], [2]]}
    '''      
    pruned_ngrams = {}
    for key in counts: # looping through every tupled key
        words, countsl = counts[key][0], counts[key][1]
        for i in range(len(countsl)): # dual bubble sort algorithm
            for j in range(len(countsl)-i-1):
                if countsl[j] < countsl[j+1]: # reversing bubble sort list
                    countsl[j], countsl[j+1] = countsl[j+1], countsl[j] 
                    words[j], words[j+1] = words[j+1], words[j]
        endList = [prune_len, len(countsl)]
        N = min(endList) 
        boundary = countsl[N-1]  # boundary for each key is final element before cut
        words2, counts2 = [], [] 
        tlist = [words2, counts2]        
        for x in range(len(words)):
            if countsl[x] >= boundary: # within pruning boundary
                counts2.append(countsl[x])
                words2.append(words[x])              
        pruned_ngrams[key] = tlist
    return pruned_ngrams
 
def probify_ngram_counts(counts):
    '''     
    (dict) -> dict
    Takes a dictionary of n-grams and converts all counts to probabilities 
    Ex. {("i", "will"): [["go", "leave"], [2,3]]} -> {("i", "will"): [["go", "leave"], [0.4, 0.6]]}
    '''      
    for key in counts: 
        firstlist = counts[key][1]
        newlist = get_prob_from_count(firstlist) # probifies each keys counts list
        counts[key][1] = newlist
    return counts
    
def build_ngram_model(words, n):
    '''     
    (list, int) -> dict
    Takes a list of words and creates an n-gram model to predict future words 
    '''      
    model = prune_ngram_counts(build_ngram_counts(words, n), 15) # cutting to only the 15 most frequent characters 
    for key in model:
        wordlist = model[key][0]
        countslist = model[key][1]  
        N = len(countslist)
        for i in range(N): # dual reverse bubble sort 
            for j in range(N-i-1):
                if countslist[j] < countslist[j+1]:
                    wordlist[j], wordlist[j+1] = wordlist[j+1], wordlist[j] 
                    countslist[j], countslist[j+1] = countslist[j+1], countslist[j]                     
    model = probify_ngram_counts(model)
    return model
    
def gen_bot_list(ngram_model, seed, num_tokens=0):
    '''     
    (dict, tuple, int) -> list
    Generates n tokens of text based on an n-gram model and a seed tuple
    Ex. {("I", "will"): [["Go"], [1]]}, ("I", "will"), 3 --> ["I", "will", "Go"]
    '''       
    botlist = []
    for token in seed:
        botlist.append(token)
    N = len(seed)
    if N > num_tokens: # length of seed > number of tokens required 
        return list(seed[0:num_tokens])
    
    for x in range(len(seed)-1, num_tokens-1):
        if ((botlist[x-1], botlist[x]) not in ngram_model): # the n-gram is not present in the model
            break
        if len(ngram_model[(botlist[x-1], botlist[x])][0]) == 0: # the n-gram is present but is empty 
            break
        else: # n-gram has some token
            ngram = (botlist[x-1], botlist[x])
            botlist.append(utilities.gen_next_token(ngram, ngram_model))
    return botlist
    
def gen_bot_text(token_list, bad_author):
    '''     
    (list, bool) -> str
    Returns a string of tokens which is formatted according to the skill of the author (bad or good)
    Ex. ["the", "fox", "jumped", "."], False --> "The fox jumped."
    '''         
    bot_text = ""
    N = len(token_list)
    if bad_author:
        for token in token_list: # just adding each token separated by a space
            bot_text += token
            bot_text += " "
    else:
        for x in range(N):
            token = token_list[x]
            first, final, beforeVP, newSent, cap = 0,0,0,0,0 # all weird things to check
            if x == 0: 
                first = True
            if x == (N - 1):
                final = True
            if x != (N-1) and (token_list[x+1] in utilities.VALID_PUNCTUATION):
                beforeVP = True
            if x != 0 and (token_list[x-1] in utilities.END_OF_SENTENCE_PUNCTUATION):
                newSent = True
            if token.capitalize() in utilities.ALWAYS_CAPITALIZE:
                cap = True
            # special cases
            if (first and final) or (final and (cap or newSent)):
                bot_text += token.capitalize()
            elif final or beforeVP:
                bot_text += token 
            elif first or cap or newSent:
                bot_text += token.capitalize() 
                if not beforeVP:
                    bot_text += " " 
            else: # normal case
                bot_text += token + " "
            
    return bot_text
        

def write_story(file_name, text, title, student_name, author, year):
    '''     
    (str, str, atr, str, str, int) -> None
    Writes a file formatted as to the specifications given in the file, using the information given
    '''        
    f = open(file_name, "w+") # formatting title page 
    for lines in range(10):
        f.write("\n")
    f.write(title + ": " + str(year) + ", UNLEASHED")
    f.write("\n")
    f.write(student_name + ", inspired by " + author)
    f.write("\n")
    f.write("Copyright year published (" + str(year) + "), publisher: EngSci press")
    f.write("\n")
    for lines in range(17):
        f.write("\n")   
    
    line, word = "", "" # textual part of story
    charcount, pglines = 0,0
    chnum, pgnum = 1,1
    pgcount = 12
    N = len(text)
    for index in range(N): 
        word += text[index] 
        if word == "of " and pgnum == 12 and pglines == 22 and charcount > 30 and (text[index+1] == "o" or text[index+1] == "O") and text[index+3] == "-": 
            # dealing with that one pesky test case, because modern problems require modern solutions
            word = word[0:len(word)-1]
            line += word
            f.write(line[0:len(line)] + "\n")
            charcount = 0
            pglines += 1
            word = ""
            line = ""
        if pgcount == 12: # adding chapter numbers
            f.write("CHAPTER " + str(chnum))
            f.write("\n")
            f.write("\n")
            pglines = 2
            pgcount = 0
            chnum += 1 
        if pglines == 28: # adding page numbers
            f.write("\n")
            f.write(str(pgnum))
            f.write("\n")
            pgnum += 1
            pgcount += 1
            pglines = 0
        if text[index] == "\n" or text[index] == " " : # adding each word
            charcount += len(word)
            if charcount <= 91: # no new line needed
                line += word
                word = ""
            else: # new line protocol            
                f.write(line[0:len(line)-1])
                f.write("\n") 
                pglines += 1
                line = ""
                index -= len(word) 
                charcount = 0
    # END SEQUENCE
    line += word
    f.write(line[0:len(line)] + "\n") # last line
    pglines += 1
    while pglines < 28: # fill empty space to 30
        f.write("\n")
        pglines += 1
    f.write("\n" + str(pgnum))
    
    
if __name__ == "__main__":
    words1 = ["the", "child", "will", "go", "out", "to", "play",",", "and", "the", "child", "can", "not", "be", "sad", "anymore", "."]   
    ngram_counts = {}
    ngram_counts['i', 'love'] = [['js', 'py3', 'c'], [20, 20, 10]]
    ngram_counts[('u', 'r')] = [['cool', 'nice', 'lit', 'kind'], [7, 8, 5, 5]]
    ngram_counts[('toronto', 'is')] = [['six', 'drake', 'a', 'b'], [2, 3, 5, 4]]  
    pruned = prune_ngram_counts(ngram_counts, 2)
    
    words = ["the", "child", "will", "the", "child", "can", "the", "child", "will", "the", "child", "may","go", "home", "."]    
    ngram_model = build_ngram_counts(words, 2)
    token_list = ['this', 'is', 'a', 'string', 'of', 'text', '.', 'which', 'needs', 'to', 'be', 'created', '.']    
    
    token_list = parse_story("308.txt")    
    text = " ".join(parse_story("308.txt"))
    write_story('test_gen_bot_text.txt', text, "Three Men in a Boat", "Jerome K. Jerome", "Jerome K. Jerome", 1889)
    f = open("analysis.txt", "w+")
    f.write(text)
    print(build_ngram_model(words, 2))
    write_story('text1.txt', text, "Three Men in a Boat", "Jerome K. Jerome", "Jerome K. Jerome", 1889)
    
    
