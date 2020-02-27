from flask import Flask, render_template, redirect, url_for, request, session

from pymongo import MongoClient
from pprint import pprint
from flask_uploads import UploadSet, IMAGES, configure_uploads
from bson import ObjectId
import datetime	
import hashlib

import time

app = Flask(__name__)
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static'
configure_uploads(app, photos)
app.config['SECRET_KEY'] = 'NEKI RANDOM STRING'

client = MongoClient('mongodb://test:test123@ds133017.mlab.com:33017/dljubisavljevic17')
db = client.dljubisavljevic17

users = db.users
items = db.items
prodaje= db.prodaje

@app.route('/')
@app.route('/index')
def index():

	lista_itema = []
	for item in items.find().sort('visits', -1):
	
		naziv = item['name']
		ajtem = str(item['_id'])
	
		lista_itema.append({'id': ajtem, 'naziv': naziv})

	return render_template('index.html', data=lista_itema)

@app.route('/registracija', methods = ['GET', 'POST'])
def register():
	if request.method == 'GET':
		return render_template('registracija.html')
	else:
		
		hash_object = hashlib.sha256(request.form['password'].encode())
		password_hashed = hash_object.hexdigest()

		email=request.form['email']
		
		if users.find_one({"ime": request.form['username']}) is not None:
			return 'Username vec postoji!'
		if email.__contains__('@') or email.__contains__('raf.rs') or email.__contains__('gmail.com'):
			users.insert_one({'ime':request.form['username'], 'prezime':request.form['prezime'],'broj kartice':request.form['broj'], 'email':request.form['email'], 'adresa':request.form['adresa'], 'password':password_hashed,'type': request.form['usertype'] ,'created': time.strftime("%d-%m-%Y.%H:%M:%S"),'pare':10})
			return redirect(url_for('login'))
		return 'Neispravna email adresa'

@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		hash_object = hashlib.sha256(request.form['password'].encode())
		password_hashed = hash_object.hexdigest()
		user = users.find_one({'ime':request.form['username'], 'password':password_hashed})
		if user is None:
			return 'Wrong login info!'
		session['_id'] = str(user['_id'])
		session['type'] = user['type']
		return 'Sucessfull login as: ' + user['type']

@app.route('/myprofile')
def my_profile():
	if '_id' not in session:
		return 'Niste ulogovani!'
	me = users.find_one({'_id': ObjectId(session['_id'])})
	
	if me['type'] == 'buyer':

		lista_prodaje=[]
		for prodaja in prodaje.find({'user_id':ObjectId(session['_id'])}):
			lista_prodaje.append(prodaja)

		return render_template('myprofile.html', user = me, lista=lista_prodaje)
	
	my_items = [item for item in items.find({'seller_id': ObjectId(session['_id'])})]

	

	return render_template('myprofile.html', user = me, items = my_items)

@app.route('/sellers')
def sellers():
	sellers_list = []
	for user in users.find({'type':'seler'}):
		user['_id'] = str(user['_id'])
		sellers_list.append(user)
	return render_template('sellers.html', sellers = sellers_list)

@app.route('/sellers/<id>')
def seller(id):
	seller = users.find_one({'_id': ObjectId(id)})
	if seller is None:
		return 'Ne postoji taj seller!'
	my_items = [item for item in items.find({'seller_id': ObjectId(id)})]
	return render_template('seller.html', items = my_items)

@app.route('/additem', methods = ['GET', 'POST'])
def add_item():
	if request.method == 'GET':
		return redirect(url_for('my_profile'))
	else:
		if '_id' not in session:
			return redirect(url_for('login'))
		
		if session['type'] != 'seler':
			return 'Niste seller!'
		
		me = users.find_one({'_id': ObjectId(session['_id'])})
		
		new_item = {
			'name': request.form['name'],
			'desc': request.form['desc'],
			'price': request.form['price'],
			'qtt': int(request.form['qtt']),
			'visits': 0,
			'likes': 0,
			'seller_id': ObjectId(session['_id']),
			'seller_name': me['ime']
		}
		pprint(new_item)
		items.insert_one(new_item)
		
		if 'slika' in request.files:
			photos.save(request.files['slika'], 'img', request.form['name'] + '.png')
		
		return redirect(url_for('my_profile'))
@app.route('/all-items')
def all_items():
	lista_item = []
	for item in items.find().sort('visits', -1):
	
		nazi = item['name']
		ajte = str(item['_id'])
	
		lista_item.append({'id': ajte, 'naziv': nazi})

	#found_items = [item for item in items.find({'qtt': {'$gt': 0}})]
	return render_template('all_items.html', l=lista_item)


@app.route('/lajk', methods = ['POST'])
def lajk():
	if '_id' not in session:
		return 'Niste ulogovani!'
	user_id = session['_id']
	item = items.find_one({'_id': ObjectId(request.form['item_id'])})
	if item is None:
		return 'Taj item ne postoji!'
	
	nova_lista = []
	if 'veclajkovali' in item:
		nova_lista = item['veclajkovali']
		if user_id in item['veclajkovali']:
			return 'Vec ste lajkovali ovo!'
	
	nova_lista.append(user_id)
	items.update_one({'_id': ObjectId(request.form['item_id'])}, {'$set': {'veclajkovali': nova_lista}})
	return redirect(url_for('item', id = request.form['item_id']))

@app.route('/items/<id>')
def item(id):
	me = users.find_one({'_id': ObjectId(session['_id'])})
	item = items.find_one({'_id': ObjectId(id)})
	if item is None:
		return 'Ne postoji takav item!'
	item['_id'] = str(item['_id'])
	lista_lajkova = []
	if 'veclajkovali' in item:
		lista_lajkova = item['veclajkovali']
		
	lista_usernameova = []
	for user in lista_lajkova:
		tuser = users.find_one({'_id': ObjectId(user)})
		lista_usernameova.append(tuser['ime'])

	lista_kom = []
	if 'komentari' in item:
		lista_kom = item['komentari']

	visits = item['visits'] + 1
	items.update_one({'_id':ObjectId(id)}, {"$set": {"visits": visits}})
	
	return render_template('item.html', item = item, lajkovi = len(lista_lajkova), lista_korisnika = lista_usernameova,lista_komentara=lista_kom,me=me)

@app.route('/komentar', methods = ['POST'])
def komentar():
	if '_id' not in session:
		return 'Niste ulogovani!'
	user_id = session['_id']
	item = items.find_one({'_id': ObjectId(request.form['item_id'])})
	if item is None:
		return 'Taj item ne postoji!'
	sada= datetime.datetime.now()
	

	lista=[]
	if 'komentari' in item:
		lista = item['komentari']
	nov_komentar={
		'komentar': request.form['komentar'],
		'vreme': sada,
		'user_id': user_id,
		'user_ime': users.find_one({'_id': ObjectId(user_id)})['ime']
	}
	
	lista.append(nov_komentar)
	items.update_one({'_id': ObjectId(request.form['item_id'])}, {'$set': {'komentari': lista}})
	return redirect(url_for('item', id = request.form['item_id']))

@app.route('/brisanje', methods = ['POST'])
def brisanje():

	item = items.delete_one({'_id': ObjectId(request.form['item_id'])})
	return(redirect(url_for('index')))

@app.route('/all_users')
def all_users():
	me = users.find_one({'_id': ObjectId(session['_id'])})
	if me['type']!='admin':
		return 'Niste admin'

	svi_korisnici = []
	for user in users.find({}):
		user['_id'] = str(user['_id'])
		svi_korisnici.append(user)
	return render_template('users.html', users = svi_korisnici,me=me)

@app.route('/brisanje_korisnika', methods = ['POST'])
def brisanje_korisnika():
	me = users.find_one({'_id': ObjectId(session['_id'])})
	if me['type']!='admin':
		return 'Niste admin'

	user_za_brisanje=users.find_one({'_id': ObjectId(request.form['user_id'])})
	if user_za_brisanje['type']=='seler':
		item = items.delete_many({'seller_id': ObjectId(request.form['user_id'])})
		
	user=users.delete_one({'_id': ObjectId(request.form['user_id'])})

	return redirect(url_for('all_users'))
	
@app.route('/dodaj_pare', methods = ['POST'])
def dodaj_pare():
	me = users.find_one({'_id': ObjectId(session['_id'])})
	pare = me['pare'] + 10
	users.update_one({'_id':ObjectId(session['_id'])}, {"$set": {"pare": pare}})

	return redirect(url_for('my_profile'))

@app.route('/dodaj_kolicinu', methods = ['POST'])
def dodaj_kolicinu():
	item = items.find_one({'_id': ObjectId(request.form['item_id'])})
	qtt = int(item['qtt']) + 1
	items.update_one({'_id': ObjectId(request.form['item_id'])}, {"$set": {'qtt': qtt}})

	return redirect(url_for('item', id = request.form['item_id']))

@app.route('/kupovina', methods = ['POST'])
def kupovina():

	me = users.find_one({'_id': ObjectId(session['_id'])})
	item = items.find_one({'_id': ObjectId(request.form['item_id'])})

	ukupna_cena= int(request.form['kolicina']) * int(item['price'])

	if me['pare']<ukupna_cena:
		return 'Nemate dovoljno para!'
	if int(request.form['kolicina'])>int(item['qtt']):
		return 'Nema na stanju'
	nova_prodaja={
		'seller_id': item['seller_id'],
		'seller_ime': item['seller_name'],
		'item_ime':item['name'],
		'user_id': me['_id'],
		'cena': ukupna_cena,
		'item': item['_id']
	}

	nova_kolicina=int(item['qtt'])-int(request.form['kolicina'])
	nove_pare=int(me['pare'])-ukupna_cena
	users.update_one({'_id':ObjectId(session['_id'])}, {"$set": {"pare": nove_pare}})
	items.update_one({'_id': ObjectId(request.form['item_id'])}, {'$set': {'qtt': nova_kolicina}})

	prodaje.insert_one(nova_prodaja)

	return redirect(url_for('my_profile'))

if __name__ == '__main__':
	app.run()