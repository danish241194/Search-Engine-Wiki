import sys
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords 

STOPWORDS = set(stopwords.words('english')) 
URL_STOP_WORDS = set(["http", "https", "www", "ftp", "com", "net", "org", "archives", "pdf", "html", "png", "txt", "redirect"])

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
class Query:
    def __init__(self,query):
        self.query = query
    def Tokenize(self):
        self.query = self.query.split()
    def lower(self):
        self.query = self.query.lower()
    def stop_word_removal(self):
        self.query = [x for x in self.query if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
    def Stemming(self):
        Pstemmer = SnowballStemmer("english")
        self.query = [Pstemmer.stem(titl) for titl in self.query]
    def process(self):
        self.lower()
        self.Tokenize()
        self.stop_word_removal()
        self.Stemming()
    def value(self):
        return self.query
def title_for_docs(doc_ids,title_pid,k):
    title = []
    count = 0
    for doc_id in doc_ids:
        title.append(title_pid[int(doc_id[1:])])
        count+=1
        if count==k:
            break
    return title
def Search(query,search_dictionary):
    Q = Query(query)
    Q.process()
    query =  Q.value()
    all_word_docs =[]
    for word in query:
        if word not in search_dictionary:
            continue
        line = search_dictionary[word].split("|")
        docs=set()
        for doc in line:
            docs.add(doc.split("-")[0])
        if(len(docs)>0):
            all_word_docs.append(docs)
    return sorted_results(all_word_docs)
def sorted_results(all_word_docs):
    if len(all_word_docs)==0:
        return []
    all_ = set.intersection(*all_word_docs)    
    union = set.union(*all_word_docs)
    diff = set.difference(union,all_)
    all_=list(all_) + list(diff)
    return all_
def load_index_dictionary(path_to_index_folder):
    dictionary_search = {}
    fp = open(path_to_index_folder+"/indexfile.txt")
    for i, line in enumerate(fp):#enumerate dont load whole in memory
        word , rest = line.split(":")[0],line.split(":")[1][:-1]
        dictionary_search[word] = rest
    fp.close()
    return dictionary_search
def load_titles(path_to_index_folder):
    titles = []
    fp = open(path_to_index_folder+"/title.txt")
    for i, line in enumerate(fp):#enumerate dont load whole in memory
        titles.append(line[:-1])
    fp.close()
    return titles

def read_file(testfile):
    with open(testfile, 'r') as file:
        queries = file.readlines()
    return queries


def write_file(outputs, path_to_output):
    '''outputs should be a list of lists.
        len(outputs) = number of queries
        Each element in outputs should be a list of titles corresponding to a particular query.'''
    with open(path_to_output, 'w') as file:
        for output in outputs:
            for line in output:
                file.write(line.strip() + '\n')
            file.write('\n')


def search_help(path_to_index, queries):
    '''Write your code here'''
    search_dic = load_index_dictionary(path_to_index)
    title_pid = load_titles(path_to_index)
    result = []
    for query in queries:
        all_word_docs = Search(query,search_dic)
        result.append(title_for_docs(all_word_docs,title_pid,10))
    return result


def main():
    path_to_index_folder = sys.argv[1]
    if path_to_index_folder[len(path_to_index_folder)-1]=="/":
        path_to_index_folder = path_to_index_folder[:-1]
    testfile = sys.argv[2]
    path_to_output = sys.argv[3]
    queries = read_file(testfile)
    outputs = search_help(path_to_index_folder, queries)
    write_file(outputs, path_to_output)


if __name__ == '__main__':
    main()
