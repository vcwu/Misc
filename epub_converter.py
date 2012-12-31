#Scrapes story text from fanfic site, then converts to an epub.
#not very robust at the moment - only works for henneth-annun, no error checks.
#need to manually insert url of wanted story
#written by victoria wu, dec 2012

import unicodedata
from urllib import urlopen
from bs4 import BeautifulSoup
import zipfile
import os

def bookInfo(url):
    """Returns chapter titles and book title, author"""
    print "Getting book and chapter titles"
    chapters= []
    mod_url = url+str(1)
    soup = BeautifulSoup(urlopen(mod_url).read())
    chap = soup.find(action="chapter_view.cfm")
    chap = unicodedata.normalize("NFKD", chap.fieldset.get_text()).encode("ascii", "ignore")
    chapters = chap.strip().replace(".", "").split("\n")
    title = soup.title.get_text()
    author = soup.find("meta", attrs={"name":"author"})["content"]
    return (title, chapters, author)


def make_xhtml(filename, chapters, story,i):
    """Makes a new xhtml file from the given story"""

    with open(filename, 'w') as f:
        doctype = "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">"
        html_tag = "<html xmlns=\"http://www.w3.org/1999/xhtml\">"
        begin_tags = "<head> <title>" + chapters[i-1] + "</title> </head> <body>"
        end_tags = "</body> </html>"

        meat = doctype + html_tag + begin_tags + story + end_tags
        f.write(meat)
    

def generate_xhtml_chapters(base_url, title, chapters):
    """Makes all the xhtml files from the given base url."""
    print "Generating xhtmls..."

    #getting # of chapters
    upper_chapter = len(chapters)


    #iterate through all chapters
    for i in range(1, upper_chapter+1):
        
        #getting info    
        mod_url = base_url + str(i)
        raw = urlopen(mod_url).read()
        soup = BeautifulSoup(raw)

        #get rid of the disclaimer
        soup.find(id="disclaimertext").decompose()

        #extract the story text
        story = str(soup.find("div", class_='block chapter'))
        
        #writing up the xhtml file
        filename = chapters[i-1] + ".xhtml"
        make_xhtml(filename, chapters, story,i)

def directoryNameExists(path, title):
    """I have no idea how to explain this. It returns a path so you're not overwriting
    an exisiting folder."""

    i = 2
    try_path = os.path.join(path, title)
    while(os.path.isdir(try_path)):
        try_title = title+ " " + str(i)
        try_path = os.path.join(path, try_title)
        i = i+1
    return try_path

def generate_content(title, chapters, author):
    #Not gonna bother with generating a UUID.
    print "generating content.opf"
   
    begin_tag = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n   \
                <package xmlns:dc=\"htpp://idpf.org/2007/opf\" unique-identifier=\"bookid\" version=\"1.0\">\n"
    meta = "<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1\" xmlns:opf=\"http://www.idpf.org/2007/opf\">" + \
                "<dc:title>" + title+ "</dc:title>" + \
                "<dc:language>en-US</dc:language>" + \
                "<dc:creator opf:role=\"aut\">" + author + "</dc:creator>"+ \
                "<dc:identifier id=\"bookid\">"+title+ "</dc:identifier> "+ \
            "</metadata>"
    #generating manifest and spine
    manifest_begin = "<manifest> \
                    <item id=\"ncx\" href=\"toc.ncx\" media-type=\"application/x-dtbncx+xml\" />"
    manifest =[manifest_begin, "</manifest>"]
    spine = ["<spine toc=\"ncx\">", "</spine>"]

    for i,chap in enumerate(chapters):
        item = "<item id=\"%s\" href=\"%s\" media-type=\"application/xhtml+xml\" /> " %(chap, chap+".xhtml")
        manifest.insert(len(manifest)-1, item)

        itemref = "<itemref idref=\"%s\" />" %(chap)
        spine.insert(len(spine)-1, itemref)

    manifest = "".join(manifest)
    spine = "".join(spine)

    meat = begin_tag + meta + manifest + spine+ "</package>"
    with open("content.opf", 'w') as f:
        f.write(meat)
    

def generate_toc(title, chapters):
    print "Generating toc.ncx"
    with open("toc.ncx", "w") as f:
        begin_tag = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<ncx xmlns=\"http://www.w3.org/1999/xhtml\">\n"
        head_tag = "<head> \n<meta name=\"dtb:uid\" content=\"" +title+"\"/>  \
                    \n<meta name=\"dtb:depth\" content=\"1\"> \
                    \n<meta name=\"dtb:totalPageCount\" content=\"0\">    \
                    \n<meta name=\"dtb:maxPageNumber\" content=\"0\"> \n</head>\n"
        title_tag = "<docTitle> <text>"+title+ "</text></docTitle>\n"
        navPoint = ["<navMap>\n", "</navMap>\n"]
        for i,chap in enumerate(chapters):
            nav = "<navPoint id=\""+chapters[i]+"\" playOrder=\""+ str(i+1) + "\">"  \
                    + "<navLabel> <text>" + chapters[i] +" </text> </navLabel>  \
                    <content src=\""+ chapters[i] +".xhtml\"/> </navPoint>\n"
            navPoint.insert(len(navPoint)-1, nav)

        nav_map = "".join(navPoint)
        meat = begin_tag + head_tag + title_tag + nav_map + " </ncx>"
        f.write(meat)
    
        
        
def generate_META_INF():
    print "generating meta inf"
    with open("container.xml", 'w') as f:
        container = "<container version=\"1.0\" \
            xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">  \
            <rootfiles> <rootfile full-path=\"OEBPS/content.opf\"   \
            media-type= \"application/oebps-package+xml\" />  \
            </rootfiles></container>"
        f.write(container)    


#ok i'm using a variant of someone else's method, taken from
#http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
def zipDirectory(zf, basedir):
    for root, dirs, files in os.walk(basedir):
        for fn in files:
            zf.write(os.path.join(basedir, fn))


#prelims
base_url = "http://www.henneth-annun.net/stories/chapter_view.cfm?stid=8&spordinal="
title, chapters, author = bookInfo(base_url)
title = title[:50]

#Readying a home for our epub
epub_path = directoryNameExists(os.getcwd(), title)
rootDir = os.getcwd()
os.mkdir(epub_path)
os.chdir(epub_path)

with open("mimetype", 'w') as f:
    f.write("application/epub+zip")

#filling up META-INF
os.mkdir("META-INF")
os.chdir("META-INF")
generate_META_INF()

#filling up OEBPS
os.chdir("../")
os.mkdir("OEBPS")
os.chdir("OEBPS")
generate_content(title, chapters, author) #content.opf
generate_toc(title, chapters)   #toc.ncx
generate_xhtml_chapters(base_url, title, chapters)

#ziiiip
print "Zipping file..."
os.chdir(epub_path) #go back to parent directory, in order to delete our thingy
fname = title + ".epub"
zf = zipfile.ZipFile(fname, mode='w')

zf.write("mimetype")
zipDirectory(zf, "META-INF")
zipDirectory(zf, "OEBPS")

zf.close()

print "Done."




