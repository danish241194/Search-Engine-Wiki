import xml.sax
import re
import string
from nltk.corpus import stopwords 
from nltk.stem.porter import *
from nltk.stem.snowball import SnowballStemmer
import datetime
import sys
print_bool =False
index_dictionary = {}
STOPWORDS = set(stopwords.words('english')) 
URL_STOP_WORDS = set(["http", "https", "www", "ftp", "com", "net", "org", "archives", "pdf", "html", "png", "txt", "redirect"])
EXTENDED_PUNCTUATIONS = set(list(string.punctuation) + ['\n', '\t', " "])
INT_DIGITS = set(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

def cleanText(text):
    text = re.sub(r'<(.*?)>','',text) #Remove tags if any
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text, flags=re.MULTILINE) #Remove Url
    text = re.sub(r'{\|(.*?)\|}', '', text, flags=re.MULTILINE) #Remove CSS
    text = re.sub(r'\[\[file:(.*?)\]\]', '', text, flags=re.MULTILINE) #Remove File
    text = re.sub(r'[.,;_()"/\'=]', ' ', text, flags=re.MULTILINE) #Remove Punctuaion
    text = re.sub(r'[~`!@#$%&\-^*+{\[}\]()":\|\\<>/?]', ' ', text, flags=re.MULTILINE)
    return " ".join(text.split())
def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

def get_InfoBox_Category_Text(body_text):
    infoBox , category , body , links , references = [],[],[],[],[]
    all_lines = body_text.split('\n')
    len_all_lines = len(all_lines)
    i=0
    
    while i < len_all_lines:
        if "{{infobox" in all_lines[i]:
            open_curly_brackets = 0
            while i < len_all_lines:
                if "{{" in all_lines[i]:
                    new_opened = all_lines[i].count("{{")
                    open_curly_brackets += new_opened
                if "}}" in all_lines[i]:
                    new_closed = all_lines[i].count("}}")
                    open_curly_brackets -= new_closed
                if open_curly_brackets > 0:
                        splitted_first_line = all_lines[i].split("{{infobox");
                        if("{{infobox" in all_lines[i] and len(splitted_first_line) >= 2 and len(splitted_first_line[1])>0):
                            infoBox.append(splitted_first_line[1])
                        else :
                            infoBox.append(all_lines[i])
                else:
                    break
                i+=1
        elif "[[category:" in all_lines[i]:
            category_line_split = all_lines[i].split("[[category:")
            if(len(category_line_split)>1):
                category.append(category_line_split[1].split("]]")[0])
                category.append(' ')
        elif "== external links ==" in all_lines[i] or "==external links ==" in all_lines[i] or "== external links==" in all_lines[i] or "==external links==" in all_lines[i]:
            i+=1
            while i < len_all_lines:
                if "*[" in all_lines[i] or "* [" in all_lines[i]:
                    links.extend(all_lines[i].split(' '))
                    i+=1
                else:
                    break 
        elif "==references==" in all_lines[i] or "== references==" in all_lines[i] or "==references ==" in all_lines[i] or "== references ==" in all_lines[i]:
            open_curly_brackets = 0
            i+=1
            while i < len_all_lines:
                if "{{" in all_lines[i]:
                    new_opened = all_lines[i].count("{{")
                    open_curly_brackets += new_opened
                if "}}" in all_lines[i]:
                    new_closed = all_lines[i].count("}}")
                    open_curly_brackets -= new_closed
                if open_curly_brackets > 0:
                    if "{{vcite" not in all_lines[i] and "{{cite" not in all_lines[i] and "{{reflist" not in all_lines[i]:
                        references.append(all_lines[i])
                else:
                    break
                i+=1
        else:
            body.append(all_lines[i])
        i+=1
    return cleanText(''.join(infoBox)),cleanText(''.join(body)),cleanText(''.join(category)),cleanText(''.join(links)),cleanText(''.join(references))
# stemmer = PorterStemmer()
stemmer = SnowballStemmer("english")
class Page:
    def __init__(self):
        self.title=""
        self.info = ""
        self.category = ""
        self.links = ""
        self.references = ""
        self.body = ""
        self.pid = -1
    def set_title(self,title):
        self.title = title
    def set_info_cat_links_ref_body(self,info,body,cat,links,ref):
        self.body = body
        self.info = info
        self.category = cat
        self.links = links
        self.references = ref
    def process(self):
        if print_bool:
            print("Page id ",self.pid)
            print("TITLE ",self.title)
            print("INFOBOX ",self.info)
            print("CAT ",self.category)
            print("LINKS ",self.links)
            print("REFERENCES ",self.references)
            print("BODY ",self.body)
            print("")
        self.Tokenize()
        self.stop_word_removal()
        self.Stemming()
        self.create_index()
    def Tokenize(self):
        self.title = self.title.split()
        self.info = self.info.split()
        self.category = self.category.split()
        self.links = self.links.split()
        self.references = self.references.split()
        self.body = self.body.split()
        
    def stop_word_removal(self):
        self.title = [x for x in self.title if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
        self.info = [x for x in self.info if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
        self.category = [x for x in self.category if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
        self.links = [x for x in self.links if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
        self.references = [x for x in self.references if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]
        self.body = [x for x in self.body if x not in STOPWORDS and x not in URL_STOP_WORDS and isEnglish(x)]

    def Stemming(self):
        self.title = [stemmer.stem(titl) for titl in self.title]
        self.body = [stemmer.stem(titl) for titl in self.body]
        self.references = [stemmer.stem(titl) for titl in self.references]
        self.links = [stemmer.stem(titl) for titl in self.links]
        self.category = [stemmer.stem(titl) for titl in self.category]
        self.info = [stemmer.stem(titl) for titl in self.info]

    def create_index(self):
        final_dictionary = {}
        dictionary_local = {}
        title_split = self.title
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " t"+str(dictionary_local[word])
        dictionary_local.clear()
        dictionary_local = {}
        title_split = self.body
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " b"+str(dictionary_local[word])
        dictionary_local.clear()
        dictionary_local = {}
        title_split = self.info
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " i"+str(dictionary_local[word])
        
        dictionary_local.clear()
        dictionary_local = {}
        title_split = self.category
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " c"+str(dictionary_local[word])
        dictionary_local.clear()
        dictionary_local = {}
        title_split = self.links
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " l"+str(dictionary_local[word])
        dictionary_local.clear()
        dictionary_local = {}
        title_split = self.references
        for word in title_split:
            if dictionary_local.get(word) is None:
                dictionary_local[word] = 0
            dictionary_local[word]+=1
        for word in dictionary_local:
            if final_dictionary.get(word) is None:
                final_dictionary[word]="p"+str(self.pid)
            final_dictionary[word]+= " r"+str(dictionary_local[word])
        for word in final_dictionary:
            if index_dictionary.get(word) is None:
                index_dictionary[word] = []
            index_dictionary[word].append(final_dictionary[word])
        dictionary_local.clear()
        final_dictionary.clear()
def process_line(key):
    list_ = index_dictionary[key]
    starter=""
    final_result=""
    for sub_list in list_:
        sublist_split = sub_list.split(" ");
        final_result+=starter
        is_page_number = True
        for elem in sublist_split:
            if is_page_number:
                final_result+=elem+"-"
                is_page_number=False
            else:
                final_result+=elem
        starter="|"
    return final_result

page = Page()
title_pid=[]
class ParseHandler( xml.sax.ContentHandler ):
    def __init__(self):
        self.tag = ""
        self.title = ""
        self.body = ""
        self.page = False
    def startElement(self, tag, attributes):
        self.tag = tag
        if self.tag == "page":
            self.page = True
            page.pid+=1
    def endElement(self, tag):
        if self.tag == "page":
            self.page = False
        elif self.tag == "text":
            infobox , body , cat , links , ref = get_InfoBox_Category_Text(self.body.lower())
            page.set_info_cat_links_ref_body(infobox,body,cat,links,ref)
            page.process()
            self.body = ""
        elif self.tag == "title":
            title_pid.append(self.title)
            page.set_title(cleanText(''.join(self.title.lower())))
    def characters(self, content):
        if self.page == True:    
            if self.tag == "title":
                self.title = content
            elif self.tag == "text":
                self.body +=content
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
Handler = ParseHandler()
parser.setContentHandler( Handler )
start = datetime.datetime.now()
parser.parse(sys.argv[1])

index_folder_path = sys.argv[2]
if index_folder_path[len(index_folder_path)-1]=="/":
    index_folder_path = index_folder_path[:-1]
outF = open(index_folder_path+"/title.txt", "w")
for line in title_pid:
    outF.write(line)
    outF.write("\n")
outF.close()
    
outF = open(index_folder_path+"/indexfile.txt", "w")
sorted_keys = sorted(index_dictionary.keys())
for key in sorted_keys:
    outF.write(key+":"+process_line(key))
    outF.write("\n")
outF.close()
end = datetime.datetime.now()
print("Index Creation Time",(end-start).seconds," seconds")
