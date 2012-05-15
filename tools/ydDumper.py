#This Python file uses the following encoding: utf-8
#Author:Superfan
#Version 1.0
#Latest Update:July,31,2011
#Usage:This script will convert youdao dictonary(plus version) to Mdict source file,put it in the same directory which offline glossories exist, and run it with python VM.
#This script is for STUDY use ONLY.DO NOT USE IT FOR ANY COMMERCIAL PURPOSE!!!
from __future__ import division
import string,re
import xml.parsers.expat

#change the index number to select local glossory to convert
(file,pointer)=[('21yh.ydic',0x404),('xhy.ydic',0x404)][1]
#whether or not to delete entries with the same name as a former one.(for xhy.ydic keep this value for False)
delDuplicate=False
f=open(file,'rb')
buffer=''
f.seek(pointer)
counter=0
phrs=[]
names=[]
output=open('output.txt','wb')

class xmlParser:
	def __init__(self,strXML):
		self.strXML=strXML
		self.xmlParsed=''
		self.name=''
		self.stack=[]
		self.entryNum=0
		self.phrsNum=0
		self.lEncounterd=False
		self.nameBegin=True
		self.phrs=[]
		self.dataBuffer=''
		self.parse()
	def StartElementHandler(self,name,attrs):
		#tag checker
		if name not in ['word','return-phrase','l','i','phone','trs','tr','phr','des','phrs','pos','wfs','wf','exam','f','n','syno','anto']:	
			print name
			print self.strXML
			open('tmp.xml','wb').write(self.strXML)
			raw_input()
		self.stack.append(name)
		if attrs!={}:
			print attrs
			print strXML
			raw_input()
		if name in ['trs','phrs']:self.entryNum=0
		if name=='tr':
			self.lEncounterd=False
			self.entryNum+=1
		self.xmlParsed+='<span class="%s">'%name	#write current tag
		if name=='l':
			self.lNum=+1
			if self.lEncounterd==False and 'return-phrase' not in self.stack and 'trs' in self.stack:
				self.lEncounterd=True
				self.xmlParsed+='<span class="entryNum">%d.</span>'%self.entryNum
				self.xmlParsed+=u'<span class="entryDot">■</span>'
		if name=='syno':
			self.xmlParsed+=u'<span class="tongyici">近义词</span>'
		if name=='anto':
			self.xmlParsed+=u'<span class="fanyici">反义词</span>'
		if name=='wf':
			self.xmlParsed+=u'<span class="bianxing">变形</span>'
	def EndElementHandler(self,name):
		if self.dataBuffer!='':
			if self.stack[-3:]==['phr','l','i']:
				self.phrsNum+=1
				if self.dataBuffer[-1]==';':self.dataBuffer=self.dataBuffer[0:-1]
				self.phrs.append((self.dataBuffer,self.name,self.phrsNum))
				self.xmlParsed+='<a name="phr%d">'%self.phrsNum+self.dataBuffer+'</a>'
			else:self.xmlParsed+=self.dataBuffer
			self.dataBuffer=''
		self.stack.pop()
		self.xmlParsed+=r'</span>'
	def CharacterDataHandler(self,data):
		if 'return-phrase' in self.stack:
			if re.search(r'^\d+',data)!=None and data!='' and self.nameBegin==False:
				tmp=re.search(r'(^\d+)(.*)',data)
				self.name+=' %s'%data
				self.dataBuffer+='<span class="upper">%s</span>%s'%tmp.groups()
				return
			self.nameBegin=False
			self.name+=data.replace('\n','')
		if self.stack[-1]=='phone':
			self.xmlParsed+='['+data+']'
			return
		#self.xmlParsed+=data
		self.dataBuffer+=data
	def parse(self):
		p=xml.parsers.expat.ParserCreate('UTF-8')
		p.StartElementHandler=self.StartElementHandler
		p.EndElementHandler=self.EndElementHandler
		p.CharacterDataHandler=self.CharacterDataHandler
		p.returns_unicode=True
		p.Parse(self.strXML)
def decrypt(str):
	i=0
	tmp=''
	try:
		while True:
			tmp+=chr((255-ord(str[i])))   #XD
			i+=1
	except IndexError:pass
	return tmp
	

while True:
	if len(buffer)<5*1024*1024:
		buffer+=decrypt(f.read(10*1024*1024))
	if buffer.find(r'</word>')==-1:break
	a=buffer.find(r'</word>')
	if a==-1:break
	else:
		counter+=1
		#open('./sample/%d.xml'%counter,'wb').write(buffer[:a+len(r'</word>')])
	P=xmlParser(buffer[:a+len(r'</word>')])
	#open('./sample/%d.html'%counter,'wb').write('<html><head><META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8"></head><body><link rel="stylesheet" type="text/css" href="sf.css"/>'+P.xmlParsed.encode('UTF-8')+'</body></html>')
	buffer=buffer[(a+len(r'</word>')):]
	#print '%d\r'%counter,P.name.encode('UTF-8')
	if delDuplicate and P.name in names:continue
	output.write(P.name.encode('UTF-8')+'\x0d\x0a')
	names.append(P.name)
	output.write('<link rel="stylesheet" type="text/css" href="sf_ecce.css"/>\x0d\x0a'+P.xmlParsed.encode('UTF-8')+'\x0d\x0a</>\x0d\x0a')
	phrs+=P.phrs
	if counter%10==0:
		print '%d\r'%counter,
		
print 'Done!Total %d entries'%counter
print 'Processing references...Total:%d'%len(phrs)
counter=0
for (phrName,entry,phrNum) in phrs:
	counter+=1
	if delDuplicate and phrName in names:continue
	if counter%20==0:
		print 'Percentage:%%%.2f\r'%(counter/len(phrs)),
	names.append(phrName)
	output.write(phrName.encode('utf-8'))
	output.write('\x0d\x0a<link rel="stylesheet" type="text/css" href="sf_ecce.css"/>\x0d\x0a')
	output.write(u'<span class="reference"><span class="ref_title">见:</span>'.encode('utf-8'))
	output.write('<a href="entry://%s#phr%d">%s</a></span>\x0d\x0a</>\x0d\x0a'%(entry.encode('utf-8'),phrNum,phrName.encode('utf-8')))
