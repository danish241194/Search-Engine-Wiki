from math import log
import sys
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords 
import re
import datetime
files_to_index_at_a_time = 50000

STOPWORDS = set(stopwords.words('english')) 
URL_STOP_WORDS = set(["http", "https", "www", "ftp", "com", "net", "org", "archives", "pdf", "html", "png", "txt", "redirect"])
Pstemmer = SnowballStemmer("english")
import bisect
def lower_bound(list_,word):
    i = bisect.bisect_left(list_,word)
    if(i<len(list_) and list_[i] == word):
        return i
    else:
        return i-1
def BinarySearch(list_,word): 
    i = bisect.bisect_left(list_,word) 
    if i != len(list_) and list_[i] == word: 
        return i 
    else: 
        return -1
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
        self.query = [Pstemmer.stem(titl) for titl in self.query]
    def process(self):
        self.lower()
        self.Tokenize()
        self.stop_word_removal()
        self.Stemming()
    def value(self):
        return self.query
    

#     print(secondary_list)
def get_posting_list(word):
    global secondary_list
    posting_list =  ""
    offset_file_num = lower_bound(secondary_list,word)
#     print("o f n",offset_file_num)
    if offset_file_num !=-1:
        fp = open(index_folder_path+"/offset"+str(offset_file_num+1)+".txt")
        dict_ = {}
        while True:
            string_ = fp.readline().strip();
            if string_=='':
                break;
            dict_[string_.split(" ")[0]]=int(string_.split(" ")[1])
        fp.close()
        fp = open(index_folder_path+"/index"+str(offset_file_num+1)+".txt")
        if word not in dict_:
            return posting_list
        fp.seek(dict_[word])
        posting_list = fp.readline().strip().split(":")[1]
        fp.close()
    return posting_list
def process_posting_field_tf(posting,field):
    all_parts = posting.split("|")
    dict_={}
    for part in all_parts:
        doc = int(part.split("-")[0])
        stng = r""+str(field)+'\d*'
        pattern = re.findall(stng,part.split("-")[1])
        sum_=0
        if len(pattern)>0:
            sum_ = int(pattern[0][1:])
            dict_[doc]=sum_
    return dict_
def process_posting_idf(posting):
    Total_documents = 19567268+1#page.pid+1
    return 1.0 + log(float(Total_documents) / len(posting.split("|")))
def process_posting_normal_tf(posting):
    all_parts = posting.split("|")
    dict_={}
    for part in all_parts:
        doc = int(part.split("-")[0])
        pattern = re.findall(r'[a-z]\d*',part.split("-")[1])
        sum_=0
        for p in pattern:
            sum_+=int(p[1:])
        dict_[doc]=sum_
    return dict_
def calculate_tf_idf_of_docs_normal(query):
    Q = Query(query)
    Q.process()
    query_parts =  Q.value()
#     print(query_parts)
    docs = {}
    for query_part in query_parts:
        posting = get_posting_list(query_part)
#         print(posting)
        if len(posting)<=0:
            continue
        dict_ = process_posting_normal_tf(posting)
        idf = process_posting_idf(posting)
        for key in dict_.keys():
            try:
                docs[key]+=log(1+dict_[key])*idf
            except:
                docs[key]=log(1+dict_[key])*idf
    return docs

def calculate_tf_idf_of_docs_field(query):
    query = query.lower()
    field_dict = get_field_list(query)
    field_results = []
    docs = {}
    for key in field_dict.keys():
        key_list = []
        lst = field_dict[key]
        for word in lst:
            word = Pstemmer.stem(word)
            posting = get_posting_list(word)
            if(len(posting)<=0):
                continue
            dic_ = process_posting_field_tf(posting,key)
            idf = process_posting_idf(posting)
            for key_ in dic_.keys():
                try:
                    docs[key_]+=log(1+dic_[key_])*idf
                except:
                    docs[key_]=log(1+dic_[key_])*idf
    return docs

def get_field_list(query):
    query = query.replace("body:","b:").replace("title:","t:").replace("category:","c:").replace("infobox:","i:").replace("ref:","e")
    words = query.split(" ")
    dictionary_query = {}
    field = ""
    for word in words:
        if re.search(r'[t|b|c|e|i]{1,}:', word):
            field = word.split(':')[0]
            word = word.split(':')[1]
        if field not in dictionary_query.keys():
            dictionary_query[field] = []
        dictionary_query[field].append(word)
    return dictionary_query

def get_title_of_doc(doc_id):
    file_num = int(doc_id/files_to_index_at_a_time)
    line_num = int(doc_id%files_to_index_at_a_time)
    with open(index_folder_path+"/offset_title"+str(file_num)+".txt") as f:
        mylist = f.read().splitlines()    
    title_file = open(index_folder_path+"/title"+str(file_num)+".txt",'r')
    title_file.seek(int(mylist[line_num]))
    result  = title_file.readline().strip()

    title_file.close()
    return result

def get_titles(doc_ids):
    titles=[]
    for doc_id in doc_ids:
        if(len(titles)>=10):
            break
        titles.append(get_title_of_doc(doc_id))
    return titles
def search_helper(query):
    dict_={}
    if ":" in query:
        dict_ = calculate_tf_idf_of_docs_field(query)
    else:
        dict_ = calculate_tf_idf_of_docs_normal(query)
    sorted_x = sorted(dict_.items(), key=lambda kv: kv[1],reverse=True)
    return get_titles([a[0] for a in sorted_x])
secondary_list=[]
index_folder_path = sys.argv[1]
with open(index_folder_path+'/secondary_index.txt') as f:
    secondary_list= f.read().splitlines() 
    secondary_list = [a.split(" ")[0] for a in secondary_list]
cmd ="cmd"
while cmd!="exit":
    cmd = input("\nEnter Query : ")
    if cmd=="exit":
        continue

    i=1
    start_s = datetime.datetime.now()
    res = search_helper(cmd)
    end_s = datetime.datetime.now()
    print("Results for Query \""+cmd+"\" in ",(end_s - start_s).seconds," seconds")
    for r in res:
        print(str(i)+".",r)
        i+=1


