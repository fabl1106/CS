# because each callback has its own stack,
# the local variables in the stack frame will be lost on returning
# it means it lost the state and context of where I am doing.
# To keep state, the stacks must be stored in the heap and passed into callbacks as parameters 
# it ls called "stack ripping" 
import socket 
import ssl 
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ 
from bs4 import BeautifulSoup

urls_go=set(['/'])
urls_done=set()

selector=DefaultSelector()

class Fetcher:
	def __init__(self, url):
		self.response=b''
		self.url=url
		self.sock=None
		self.ss=None

	def fetch(self):
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(False)
		self.ss=ssl.wrap_socket(self.sock, ssl_version=ssl.PROTOCOL_TLS)
		
		try:
			self.ss.connect(('xkcd.com', 443))
		except:
			pass 
	    	
		selector.register(self.ss.fileno(), EVENT_WRITE, self.connected) 
	
	def connected(self, key, mask):
		selector.unregister(self.ss.fileno())
		request='GET {} HTTP1.1\r\nHost: xkcd.com\r\nConnection: close\r\n\r\n'.format(self.url)
			
		self.ss.send(request.encode())		
		selector.register(self.ss.fileno(), EVENT_READ, self.read_response)
		
	def read_response(self, key, mask):
		chunk=self.ss.recv(4096)
		if chunk:
			self.response+=chunk
		else:
			print(self.response)
			selector.unregister(self.ss.fileno())
			links=self.parse_links()

			for link in links.difference(urls_done):
				urls_go.add(link)
				Fetcher(link).fetch()

			urls_done.update(links)
			urls_go.remove(self.url)

	def parse_links(self):
		soup=BeautifulSoup(self.response, 'html.parser')
		anchors=soup.find_all('a')
		links=set()
		for anchor in anchors:
			if anchor.get('href'):
				links.add(anchor['href'])
		
		return links

def loop():
	while True: 
		events=selector.select()
		for key, mask in events:
			callback=key.data
			print(callback.__name__)
			callback(key, mask)

fetcher=Fetcher('/')
fetcher.fetch()

loop()
