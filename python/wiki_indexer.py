import xml.sax
import re
import string
from nltk.corpus import stopwords 
from nltk.stem.porter import *
from nltk.stem.snowball import SnowballStemmer
import datetime
import sys
import os
files_to_index_at_a_time = 50000
print_bool =False
index_dictionary = {}
STOPWORDS = set(stopwords.words('english')) 
URL_STOP_WORDS = set(["http", "https", "www", "ftp", "com", "net", "org", "archives", "pdf", "html", "png", "txt", "redirect"])
EXTENDED_PUNCTUATIONS = set(list(string.punctuation) + ['\n', '\t', " "])
INT_DIGITS = set(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

try:
    os.mkdir("tempind_")
except:
    pass
def cleanText(text):
    text = re.sub(r'<(.*?)>','',text) #Remove tags if any
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text, flags=re.MULTILINE) #Remove Url
    text = re.sub(r'{\|(.*?)\|}', '', text, flags=re.MULTILINE) #Remove CSS
    text = re.sub(r'\[\[file:(.*?)\]\]', '', text, flags=re.MULTILINE) #Remove File
    text = re.sub(r'[.,;_()"/\'=]', ' ', text, flags=re.MULTILINE) #Remove Punctuaion
    text = re.sub(r'[~`!@#$%&-^*+{\[}\]()":\|\\<>/?]', ' ', text, flags=re.MULTILINE)
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
def write_to_index(filenum,index_dictionary):
    outF = open("tempind_/"+str(filenum)+".txt", "w")
    sorted_keys = sorted(index_dictionary.keys())
    for key in sorted_keys:
        outF.write(key+":"+process_line(key))
        outF.write("\n")
    outF.close()

All_documents_done = True
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
                final_dictionary[word]=""+str(self.pid)
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
                final_dictionary[word]=""+str(self.pid)
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
                final_dictionary[word]=""+str(self.pid)
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
                final_dictionary[word]=""+str(self.pid)
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
                final_dictionary[word]=""+str(self.pid)
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
                final_dictionary[word]=""+str(self.pid)
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
filenm=1

def Kwaymerge():
    import heapq
    max_offset_file_size=10*1024*1024 #10 MB
    offset_file_size = 0
    dic_ = {}
    file_num=1
    heap = []
    import os
    num_files = len(os.listdir("tempind_"))
    while(file_num<=num_files):
        fp = open('tempind_/'+str(file_num)+'.txt','r+')
        heap.append((fp.readline().strip(),file_num))
        dic_[file_num]=fp
        file_num+=1
    heapq.heapify(heap)
    prev = "...."
    outF = open(index_folder_path+"/index1.txt", "w")
    outO = open(index_folder_path+"/offset1.txt", "w")
    outS = open(index_folder_path+"/secondary_index.txt", "w")
    First = True
    offset= 0 
    i_n = 2
    while(len(heap)>0):
        string = heap[0][0]
        stream = dic_[heap[0][1]]
        file_number = heap[0][1]
        if string=='':
            heapq.heappop(heap)
            os.remove('tempind_/'+str(file_number)+'.txt')
        else:
            heapq.heappop(heap)
            heapq.heappush(heap,(stream.readline().strip(),file_number))  
            if string.split(":")[0] == prev:
                outF.write("|"+string.split(":")[1])
                offset+=len("|"+string.split(":")[1])
            else:
                if(offset_file_size>max_offset_file_size):
                    prev = "...."
                    outF.close()
                    outO.close()
                    outF = open(index_folder_path+"/index"+str(i_n)+".txt", "w")
                    outO = open(index_folder_path+"/offset"+str(i_n)+".txt", "w")
                    i_n+=1
                    offset= 0 
                    offset_file_size=0
                    First = True
                if First:
                    outS.write(string.split(":")[0]+" "+str(i_n-1)+"\n")
                    First = False
                else:
                    offset+=1
                    outF.write("\n")                 
                prev = string.split(":")[0]
                outO.write(string.split(":")[0]+" "+str(offset)+"\n")
                offset_file_size+=len(string.split(":")[0]+" "+str(offset)+"\n")
                outF.write(string)
                offset += len(string)
    outF.close()
    outO.close()
    outS.close()

index_folder_p = sys.argv[2]
try:
    os.mkdir(index_folder_p)
except:
    pass
index_folder_path = index_folder_p
title_number=0
outF_title = open(index_folder_path+"/title"+str(title_number)+".txt", "w")
outF_offset = open(index_folder_path+"/offset_title"+str(title_number)+".txt", "w")
offset_title=0
class ParseHandler( xml.sax.ContentHandler ):
    def __init__(self):
        self.tag = ""
        self.title = ""
        self.body = ""
        self.page = False
    def startElement(self, tag, attributes):
        global All_documents_done
        self.tag = tag
        if self.tag == "page":
            self.page = True
            All_documents_done = False
            page.pid+=1            
    def endElement(self, tag):
        global filenm,All_documents_done,outF_title,title_number,offset_title,outF_offset
        if tag=="page" and (page.pid+1)%files_to_index_at_a_time==0:
            print(str(page.pid+1)+" articles processed")
            write_to_index(filenm,index_dictionary)
            index_dictionary.clear()
            filenm=filenm+1
            All_documents_done = True
        if tag == "page":
            self.page = False
        elif tag == "text":
            infobox , body , cat , links , ref = get_InfoBox_Category_Text(self.body.lower())
            page.set_info_cat_links_ref_body(infobox,body,cat,links,ref)
            page.process()
            self.body = ""
            
        elif tag == "title":
#             title_pid.append(self.title)
            if (page.pid)%files_to_index_at_a_time==0:
                outF_title.close()
                outF_offset.close()
                outF_offset = open(index_folder_path+"/offset_title"+str(title_number)+".txt", "w")
                outF_title = open(index_folder_path+"/title"+str(title_number)+".txt", "w")
                title_number+=1
                offset_title=0
            outF_offset.write(str(offset_title))
            outF_offset.write("\n")
            outF_title.write(self.title)
            outF_title.write("\n")
            offset_title+=len(self.title.encode('utf-8'))+1
            

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
dump_data = sys.argv[1]
parser.parse(dump_data)
if not All_documents_done:
    write_to_index(filenm,index_dictionary)
    index_dictionary.clear()
if not outF_title.closed:
    outF_title.close()
    outF_offset.close()

if index_folder_path[len(index_folder_path)-1]=="/":
    index_folder_path = index_folder_path[:-1]
    
print()
print("K - way Merging Start")
print()
Kwaymerge()

print()
print("K - way Merging End")
print()
end = datetime.datetime.now()
secs  = (end-start).seconds
hr = int(secs/(60*60))
rm = int(secs%(60*60))
mn = int(rm/60)
rm=int(rm%60)
secs = int(rm)
print("Indexing Time : ",hr," hrs ",mn," mns",secs," secs")
print("Total Articles : "+str(page.pid+1))
