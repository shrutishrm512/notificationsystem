from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from cloudant.client import Cloudant
import datetime
from config import CLOUDANTPASSWORD, CLOUDANTUSERNAME
import json
import re
client = Cloudant(CLOUDANTUSERNAME, CLOUDANTPASSWORD, account=CLOUDANTUSERNAME)
client.connect()

def mainpage(request):
    return render(request, 'notification/main.html')

@csrf_protect
def loginUser(request):
    if request.method == 'GET':
        return render(request, 'notification/login.html')
    else:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            DBUSER = client['users']
            userList = DBUSER.get_view_result('_design/fetch', 'byUsername')[username]
            login(request, user)
            if request.GET.get('nextPage', None) is not None:
                return redirect(request.GET.get('nextPage', None))
            if userList[0]['value']['designation'] == 'User':
                return redirect('/dashboard')
        
        else:
            return render(request, 'notification/login.html', {'msg': 'Invalid Username or Password'})

@csrf_protect
def signup(request):
    if request.method == 'GET':
        return render(request, 'notification/signup.html')
    else:
        username = request.POST['usernamesignup']
        email = request.POST['emailsignup']
        password = request.POST['passwordsignup']
        fullName = request.POST['fullName']
        
        # Saving in sqlite
        try:
        	user = User.objects.create_user(username=username, email=email, password=password)
        	user.save()
        except Exception:
            return render(request, 'notification/signup.html', {
                'msg': 'Username already exists'})
        # Saving in cloudant
        DBUSERS = client['users']
        users = DBUSERS.get_view_result('_design/fetch', 'byUsername')
        subscribeList = []
        for u in users:
        	print("f")
        	name = []
        	name.append(u)
        	name.append(0)
        	subscribeList.append(name)
        #print(subscribeList)
        newUser = {'username': username, 'email': email, 'fullName': fullName, 'designation': 'User',
        			'status': '', 'subscribeList': subscribeList}
        DBUSERS.create_document(newUser)
        return redirect('/login')


def dashboard(request):
    DBUSER = client['users']
    users = DBUSER.get_view_result('_design/fetch', 'byUsername')
    user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
    user = DBUSER[user[0]['id']]
    subscribeList = user['subscribeList']
    newList = []
    for u in users:
   		if u['value']['username'] != user['username']:
   			flag = 0
   			print(u['value']['username'])
   			for s in subscribeList:
   				print("enter")
   				if u['value']['username'] == s[0]['value']['username']:
   					print("yes1")
   					flag = 1
   					types = s[1]
   					break
   					
   			if flag == 0:
   				print("new")
   				name = []
   				name.append(u)
   				name.append(0)
   				newList.append(name)
   			else:
   				print("old")
   				name = []
   				name.append(u)
   				name.append(types)
   				newList.append(name)
   		else:
   			continue


    #print(newList)
    user['subscribeList'] = newList
    user.save()
    notificationList = getNotification(request.user.username)
    print(notificationList)
    return render(request, 'notification/dashboard.html', {'user': request.user.username,
                                                          'userList': user['subscribeList'],
                                                          'notificationList': notificationList[:6],
                                                          'i': len(notificationList)})


def logoutUser(request):
    logout(request)
    return redirect('/')


def editProfile(request):
    if request.method == "GET":
        DBUSER = client['users']
        user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
        notificationList = getNotification(request.user.username)
        return render(request, 'notification/editProfile.html', {
            'user': user[0]['value'], 'notificationList': notificationList[:6],
            'i': len(notificationList)})

    else:
        # Saving in cloudant
        DBUSER = client['users']
        user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
        user = DBUSER[user[0]['id']]
        user['collegeName'] = request.POST['collegename']
        user['password'] = request.POST['password']
        user['dob'] = request.POST['dob']
        user['gender'] = request.POST['gender']
        user['motto'] = request.POST['motto']
        user['location'] = request.POST['location']
        user.save()
        subscribeList = user['subscribeList']
        text = request.user.username + " has updated the profile."
        print(text)
        print("h")
        for u in subscribeList:
        	usl = u[0]['value']
        	fornoti = u[0]['value']['username']
        	usl = usl['subscribeList']
        	print("first")
        	for s in usl:
        		print("sec")
        		print(s[0]['value']['username'])
        		if s[0]['value']['username'] == user['username']:
        			print("hi")
        			if s[1] == 1:
        				print("sat")
        				addNotification(text, fornoti, "status")
        				break

        return redirect('/profile')

def subscribe(request, username):
    DBUSER = client['users']
    print("sub")
    user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
    #userId[1] = 1
    print("sub")
    user = DBUSER[user[0]['id']]
    subscribeList = user['subscribeList']
    for u in subscribeList:
    	if u[0]['value']['username'] == username:
    		u[1] = 1
    		text = request.user.username + " has subscribed you."
    		addNotification(text, username, "subscribe")

    user['subscribeList'] = subscribeList
    user.save()
    return redirect('/dashboard')

def unsubscribe(request, username):
    DBUSER = client['users']
    user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
    user = DBUSER[user[0]['id']]
    subscribeList = user['subscribeList']
    for u in subscribeList:
    	if u[0]['value']['username'] == username:
    		u[1] = 0

    user['subscribeList'] = subscribeList
    user.save()
    return redirect('/dashboard')

def status(request):
	DBUSER = client['users']
	user = DBUSER.get_view_result('_design/fetch', 'byUsername')[request.user.username]
	dateCreated = str(datetime.datetime.strftime(datetime.datetime.now(), '%B %d, %Y, %H:%M %p'))
	user = DBUSER[user[0]['id']]
	user['status'] = request.POST['body']
	subscribeList = user['subscribeList']
	text = request.user.username + " updated the status " + user['status']
	print(text)
	print("h")
	for u in subscribeList:
		usl = u[0]['value']
		fornoti = u[0]['value']['username']
		usl = usl['subscribeList']
		print("first")
		#print(usl)
		for s in usl:
			print("sec")
			print(s[0]['value']['username'])
			if s[0]['value']['username'] == user['username']:
				print("hi")
				if s[1] == 1:
					print("sat")
					addNotification(text, fornoti, "status")
					break

	return redirect('/dashboard')

def addNotification(text, user, typeNoti):
    DBNOTIFICATION = client['notifications']
    dateCreated = str(datetime.datetime.strftime(datetime.datetime.now(), '%B %d, %Y, %H:%M %p'))
    date = str(datetime.datetime.strftime(datetime.datetime.now(), '%d-%m-%Y, %H:%M %p'))
    DBNOTIFICATION.create_document({'text': text, 'to': user, 'dateCreated': dateCreated,
                                    'read': "false", 'type': typeNoti, 'date': date})


def getNotification(username):
    DBNOTIFICATION = client['notifications']
    notificationlist = DBNOTIFICATION.get_view_result('_design/fetch', 'byDate')[:]
    print(notificationlist)
    notificationList = []
    for notification in notificationlist:
        val = notification['value']
        if val['to'] == username and val['read'] == "false":
            notificationList.append(notification)
    notificationList.reverse()
    return notificationList


def read(request, notifyId):
    if request.method == "GET":
        DBNOTIFICATION = client['notifications']
        notification = DBNOTIFICATION[notifyId]
        notification['read'] = 'true'
        notification.save()
        return redirect('/dashboard')


def notifications(request):
    DBNOTIFICATION = client['notifications']
    notificationlist = DBNOTIFICATION.get_view_result('_design/fetch', 'byDate')
    notificationList = []
    for notification in notificationlist:
        if notification['value']['to'] == request.user.username and notification['value']['read'] == "false":
            notificationList.append(notification)
    notificationList.reverse()
    return render(request, 'notification/notification.html', {'user': request.user.username,
                                                             'notificationList': notificationList,
                                                             'i': len(notificationList)})