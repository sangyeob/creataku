#-*-coding:utf-8-*-

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import sys
from flask import Flask, request, render_template, redirect, flash, url_for, g, session, abort, make_response, current_app
from flask.ext.mysqldb import MySQL
from functools import wraps
import datetime
import json
import sqlite3
import hashlib
import threading
import time
import os
import random
import locale
import categories

DEBUG = True

application = Flask(__name__, instance_relative_config=True)

application.config['MYSQL_USER'] = os.environ['RDS_USERNAME']
application.config['MYSQL_PASSWORD'] = os.environ['RDS_PASSWORD']
application.config['MYSQL_DB'] = os.environ['RDS_DB_NAME']
application.config['MYSQL_HOST'] = os.environ['RDS_HOSTNAME']

application.config.from_object(__name__)

mysql = MySQL(application)

def query_db(query, args=(), one=False, format=True, noresult=False):
    cur = mysql.connection.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    if noresult:
    	cur.close()
    	return None
    else:
	    if not format:
	        cur.close()
	        return (rv[0] if rv else None) if one else rv
	    else:
	        ret = (format_row(cur, rv[0]) if rv else None) if one else [format_row(cur, r) for r in rv]
	        cur.close()
	        return ret

def format_row(cur, row):
    if row != None:
        return dict((cur.description[idx][0], value) for idx, value in enumerate(row))
    else:
        return None

'''
@application.before_request
def before_request():
    g.db = connect_db() 

@application.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
'''

def generate_password_hash(plain):
    return hashlib.sha224(plain + '42dda7bbd8f735b49ecbfa2f8bcf39ed').hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isAuthenticated():
            return redirect(url_for('login_auction', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def getUserAgent():
	return request.headers.get('User-Agent')

def setFlash(message):
    session['flash'] = message

def getFlash():
    if 'flash' in session:
        ret = session['flash']
        session.pop('flash', None)
        return ret
    return None

def get_default_context(page_name, generate_url = True):
    mainimg_id = int(random.random() * 12 + 1)
    if mainimg_id < 10:
        mainimg_id = "0" + str(mainimg_id)
    else:
        mainimg_id = str(mainimg_id)

    ret = {
        "mainimg_id": mainimg_id,
        "time_now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "time_end": "2017-01-15 23:59:59",
        "is_authenticated": isAuthenticated(),
        "categories": categories.categories.keys(),
        "category_names": categories.categories,
        "flash": getFlash(),
    }
    if generate_url:
        ret['next'] = url_for(page_name)
    return ret


@application.route('/')
def index(): 
    context = get_default_context('index')
    return render_template('redesign/index.html', context = context)

@application.route('/auction/')
def auction():
    return redirect(url_for('auction_category', category = 'figure'))

def generatelot(id):
    id = str(id);
    if len(id) == 1:
        return '00' + id;
    if len(id) == 2:
        return '0' + id;
    return id;

def addCommasToNumber(num):
    return format(num, ',d')

def getElapsedTime(timestr):
    ts = datetime.datetime.now() - datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    s = ts.total_seconds()
    if s > 60 * 60 * 24:
        s /= 60 * 60 * 24
        return u"{0}일 전".format(int(s))
    if s > 60 * 60:
        s /= 60 * 60
        return u"{0}시간 전".format(int(s))
    if s > 60:
        s /= 60
        return u"{0}분 전".format(int(s))
    return u"{0}초 전".format(int(s))

@application.route('/auction/<category>/')
def auction_category(category):
    context = get_default_context('auction', generate_url = False)
    context['next'] = url_for('auction_category', category = category)
    context['category'] = category
    context['items'] = query_db('select * from auction_item where category = %s', (category,))
    for i in context['items']:
        i['lot'] = generatelot(i['id'])
        i['start_price_str'] = addCommasToNumber(i['start_price'])
        i['current_price_str'] = addCommasToNumber(i['current_price'])
        if isAuthenticated():
            i['ismine'] = str(i['last_bidder']) == str(session['user'])
        else:
            i['ismine'] = False
    return render_template('redesign/auction.html', context = context)

@application.route('/auction/view/<lot>/')
def auction_view_lot(lot):
    context = get_default_context('auction_view_lot', generate_url = False)
    context['next'] = url_for('auction_view_lot', lot = lot)
    context['item'] = query_db('select * from auction_item where id = %s', (lot,), one = True)
    context['item']['lot'] = generatelot(context['item']['id'])
    context['item']['start_price_str'] = addCommasToNumber(context['item']['start_price'])
    context['item']['current_price_str'] = addCommasToNumber(context['item']['current_price'])
    context['last_bid'] = query_db('select * from auction_bid where auction_id = %s order by id desc limit 1', (lot,), one = True)
    context['time_end'] = context['item']['end_at']
    if context['last_bid'] != None:
        context['last_bid_at_str'] = getElapsedTime(context['last_bid']['bid_at'])
    else:
        context['last_bid_at_str'] = None

    if context['item']['related']:
        context['item']['related'] = json.loads(context['item']['related'])
        for i in xrange(len(context['item']['related'])):
            context['item']['related'][i] = query_db('select * from auction_item where id = %s', (context['item']['related'][i],), one=True)
    if isAuthenticated():
        context['item']['ismine'] = str(context['item']['last_bidder']) == str(session['user'])
    else:
        context['item']['ismine'] = False
    context['log'] = query_db('select * from auction_bid where auction_id = %s order by id desc', (context['item']['id'],))
    for l in context['log']:
        l['user'] = query_db('select * from auction_user where id = %s', (l['user_id'],), one=True)
    return render_template('redesign/auction_view.html', context = context)

@application.route('/auction/account/check_validity/', methods = ["POST"])
def auction_account_check_validity():
    email = request.json['email']
    pw = request.json['password']
    res = query_db('select * from auction_user where email = %s', (email,), one = True)
    if res == None:
        return "NotRegistered"
    if res['password'] == generate_password_hash(pw):
        return "OK"
    return "WrongPassword"

@application.route('/auction/account/check_availability/', methods = ["POST"])
def auction_account_check_availability():
    email = request.json['email']
    pw = request.json['password']
    pw_confirm  = request.json['password_confirm']
    if email == "":
        return "EmailEmpty"
    if pw == "":
        return "PasswordEmpty"
    if pw != pw_confirm:
        return "PasswordConfirmFailed"
    res = query_db('select * from auction_user where email = %s', (email,), one = True)
    if res == None:
        return "OK"
    return "AccountExist"

@application.route('/my/')
def auction_my():
    context = get_default_context('auction_my')
    context['items'] = []
    aucids = query_db('select auction_id from auction_bid where user_id = %s order by auction_id asc', (session['user'],));
    for i in xrange(len(aucids)):
        if i == 0 or aucids[i - 1]['auction_id'] != aucids[i]['auction_id']:
            context['items'].append(query_db('select * from auction_item where id = %s', (aucids[i]['auction_id'],), one=True))

    for i in context['items']:
        i['lot'] = generatelot(i['id'])
        i['start_price_str'] = addCommasToNumber(i['start_price'])
        i['current_price_str'] = addCommasToNumber(i['current_price'])
        if isAuthenticated():
            i['ismine'] = str(i['last_bidder']) == str(session['user'])
        else:
            i['ismine'] = False

    return render_template('redesign/my.html', context = context)

def authenticate(session, user):
    session['user'] = user

def logout(session):
    session.pop('user', None)

def isAuthenticated():
    return 'user' in session

@application.route('/auction/account/loginproc/', methods = ["POST"])
def auction_account_login():
    email = request.form['email']
    pw = request.form['password']
    res = query_db('select * from auction_user where email = %s', (email,), one = True)
    if res == None:
        return "NotRegistered"
    if res['password'] == generate_password_hash(pw):
        authenticate(session, res['id'])
        return redirect(request.form['next'])
    return "WrongPassword"

@application.route('/auction/account/signupproc/', methods = ["POST"])
def auction_account_signup():
    email = request.form['email']
    pw = request.form['password']
    res = query_db('select * from auction_user where email = %s', (email,), one = True)
    if res == None:
        query_db('insert into auction_user (email, password, registered_at) values (%s, %s, %s)', 
            (email, generate_password_hash(pw), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), noresult = True)
        mysql.connection.commit()
    else:
        return "AccountExist"
    res = query_db('select * from auction_user where email = %s', (email,), one = True)
    authenticate(session, res['id'])
    return redirect(request.form['next'])

@application.route('/auction/account/logout/')
def auction_account_logout():
    logout(session)
    return redirect(url_for("index"))

@application.route('/auction/bid/', methods = ["POST"])
@login_required
def auction_bid():
    next = request.form['location']
    user_id = request.form['user_id']
    auc_id = request.form['auc_id']
    price = request.form['price']
    current_price = request.form['current_price']
    now = datetime.datetime.now()
    auc = query_db('SELECT * FROM auction_item WHERE id = %s', (auc_id,), one = True)

    if now > datetime.datetime.strptime(auc['end_at'], "%Y-%m-%d %H:%M:%S"):
        setFlash(u'경매 마감 시간이 지났습니다.')
        return redirect(next)

    if price == '':
        setFlash(u'응찰가를 입력해 주세요');
        return redirect(next)
    try:
        price = int(price)
    except ValueError:
        setFlash(u'잘못된 입력입니다.')
        return redirect(next)

    if price % 1000 != 0:
        setFlash(u'응찰가는 1,000원 단위로만 입력할 수 있습니다.')
        return redirect(next)
    
    price += int(current_price)

    bids = query_db('SELECT * FROM auction_bid WHERE auction_id = %s order by bid_price DESC', (auc['id'],))
    if len(bids) > 0:
        if int(price) <= int(bids[0]['bid_price']):
            setFlash(u'더 높은 가격에 입찰되어 있습니다. 다시 시도해주세요.')
            return redirect(next)

    query_db('INSERT into auction_bid (auction_id, user_id, bid_price, bid_at) values (%s, %s, %s, %s)',
        (auc_id, user_id, price, now.strftime("%Y-%m-%d %H:%M:%S")), noresult = True)
    query_db('UPDATE auction_item SET last_bid = %s, last_bidder = %s, current_price=%s WHERE id=%s', (now.strftime("%Y-%m-%d %H:%M:%S"), user_id, price, auc_id), noresult = True)
    mysql.connection.commit()

    setFlash(u'{0} KRW에 응찰되었습니다.<br /> 현재가: {1} KRW'.format(addCommasToNumber(price - int(current_price)), addCommasToNumber(price)))
    return redirect(next)

'''
@application.route('/auction/list/<listtype>/')
@login_required
def auction_list(listtype):
    context = {
        "flash": getFlash(),
        "next": url_for('auction_list', listtype = listtype),
        "isAuthenticated": isAuthenticated(),
        "listtype": listtype,
    }
    if listtype == "ing":
        context["auctions"] = query_auctions()[0];
    else:
        context["auctions"] = query_auctions()[1];

    return render_template('auction_list.html', context = context)

@application.route('/auction/')
def index_auction():
    context = {
        "flash": getFlash(),
        "next": url_for('index_auction'),
        "isAuthenticated": isAuthenticated(),
        "auctions": query_auctions(),
    }
    return render_template('index_auction.html', context = context)

@application.route('/auction/account/login/')
def login_auction():
    context = {
        "flash": getFlash(),
        "next": url_for('login_auction'),
        "isAuthenticated": isAuthenticated(),
    }
    return render_template('auction_login.html', context = context)

def query_auctions():
    ret = [[], []]
    res = query_db('select * from auction')
    for r in res:
        r['photo'] = json.loads(r['thumbnails'])[0]['url']
        r['start_price'] = locale.format("%d", int(r['start_price']), grouping=True)
        r['current_price'] = locale.format("%d", int(r['current_price']), grouping=True)
        r['buynow_price'] = locale.format("%d", int(r['buynow_price']), grouping=True)
        if r['status'] == 'closed':
           ret[1].append(r)
        else: 
            if datetime.datetime.now() < datetime.datetime.strptime(r['end_at'], "%Y-%m-%d %H:%M:%S"):
                ret[0].append(r)
            else:
                ret[1].append(r)
                query_db('UPDATE auction SET status="closed" WHERE id=%s', (r['id'],), noresult = True)
                mysql.connection.commit()

    return ret

@application.route('/auction/view/<id>/')
@login_required
def auction_view(id):
    context = {
        "flash": getFlash(),
        "next": url_for('auction_view', id = id),
        "isAuthenticated": isAuthenticated(),
    }
    r = query_db('select * from auction where id = %s', (id,), one = True)
    r['photo'] = json.loads(r['thumbnails'])[0]['url']
    r['start_price_grp'] = locale.format("%d", int(r['start_price']), grouping=True)
    r['current_price_grp'] = locale.format("%d", int(r['current_price']), grouping=True)
    r['buynow_price_grp'] = locale.format("%d", int(r['buynow_price']), grouping=True)
    if r['status'] == 'open':
        if datetime.datetime.now() > datetime.datetime.strptime(r['end_at'], "%Y-%m-%d %H:%M:%S"):
            r['status'] = 'closed'
            query_db('UPDATE auction SET status="closed" WHERE id=%s', (r['id'],), noresult = True)
            mysql.connection.commit()
    context['auction'] = r

    bids = query_db('select * from auction_bid where auction_id=%s order by bid_price desc', (r['id'],))
    for b in bids:
        b['bid_price_grp'] = locale.format("%d", int(b['bid_price']), grouping=True)
    context['bids'] = bids

    if len(bids) > 0:
        min_bid = bids[0]['bid_price']
    else:
        min_bid = r['start_price']

    bid_step = 10 ** len(str(min_bid)) * 5 / 1000

    if len(bids) > 0:
        min_bid += bid_step

    context['min_bid'] = min_bid
    context['bid_step'] = bid_step

    return render_template('auction_view.html', context = context)

@application.route('/auction/bid/', methods = ["POST"])
@login_required
def auction_bid():
    next = request.form['location']
    user_id = request.form['user_id']
    auc_id = request.form['auc_id']
    price = request.form['price']
    now = datetime.datetime.now()
    auc = query_db('SELECT * FROM auction WHERE id = %s', (auc_id,), one = True)
    if now > datetime.datetime.strptime(auc['end_at'], "%Y-%m-%d %H:%M:%S"):
        setFlash(u'경매 마감 시간이 지났습니다.')
        query_db('UPDATE auction SET status="closed" WHERE id=%s', (auc_id,), noresult = True)
        mysql.connection.commit()
        return redirect(next)

    bids = query_db('SELECT * FROM auction_bid WHERE auction_id = %s order by bid_price DESC', (auc['id'],))
    if len(bids) > 0:
        if int(price) <= int(bids[0]['bid_price']):
            setFlash(u'더 높은 가격에 입찰되어 있습니다. 다시 시도해주세요.')
            return redirect(next)

    if int(price) >= int(auc['buynow_price']):
        price = auc['buynow_price']
        query_db('UPDATE auction SET status="closed" WHERE id=%s', (auc_id,), noresult = True)

    query_db('INSERT into auction_bid (auction_id, user_id, bid_price, bid_at) values (%s, %s, %s, %s)',
        (auc_id, user_id, price, now.strftime("%Y-%m-%d %H:%M:%S")), noresult = True)
    mysql.connection.commit()

    r = query_db('SELECT * FROM auction_bid WHERE auction_id = %s order by bid_price DESC', (auc['id'],))
    query_db('UPDATE auction SET bid_count=%s, current_price=%s WHERE id=%s', (len(r), price, auc_id), noresult = True)
    mysql.connection.commit()

    setFlash(u'성공적으로 입찰하였습니다!')

    return redirect(next)

@application.route('/auction/register/')
def auction_register():
    return render_template('auction_register.html')

@application.route('/auction/register/', methods = ["POST"])
def auction_register_post():
    name = request.form['name']
    started_at = request.form['started_at']
    start_price = request.form['start_price']
    current_price = request.form['current_price']
    end_at = request.form['end_at']
    bid_count = request.form['bid_count']
    buynow_price = request.form['buynow_price']
    body = request.form['body']
    thumbnails = request.form['thumbnails']

    query_db('insert into auction (name, started_at, start_price, current_price, end_at, bid_count, buynow_price, body, thumbnails) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)', 
        (name, started_at, start_price, current_price, end_at, bid_count, buynow_price, body, thumbnails), noresult = True)
    mysql.connection.commit()
    return "OK"

@application.route('/test/')
def test_ac():
    context = {
        "flash": getFlash(),
        "next": url_for('auction_guide'),
        "isAuthenticated": isAuthenticated(),
    }
    return render_template('auction_complete.html', context = context)
'''

conn = S3Connection(os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'])
bucket = conn.get_bucket('gangnam-proto-image')

def uploadFile(filename, files):
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_string(files.read())
    k.set_acl('public-read')
    k.generate_url(3600 * 24 * 7)
    return 'https://s3-ap-northeast-1.amazonaws.com/gangnam-proto-image/' + filename

application.secret_key = 'super secret key'

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    locale.setlocale(locale.LC_ALL, 'en_US')
    application.config['SESSION_TYPE'] = 'filesystem'
    application.debug = True
    application.run(host='0.0.0.0', port=5000)
