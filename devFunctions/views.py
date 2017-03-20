from django.shortcuts import render
from django.http import HttpResponse
from notification.views import client
import json
from django.contrib.auth.models import User


# Create your views here.
def resetCloudantDB(request):
    client.delete_database('users')
    client.delete_database('notifications')
    DB1 = client.create_database('users')
    DB2 = client.create_database('notifications')
    createDesignDoc('a')
    deleteSqlite('a')
    if DB1.exists():
        return HttpResponse('SUCCESS!!')


def deleteSqlite(request):
    userList = User.objects.all()
    for user in userList:
        user.delete()
    return HttpResponse('SUCCESS!!')


def createDesignDoc(request):
    DBUSERS = client['users']
    DBNOTIFICATION = client['notifications']
    designDoc = {
        "_id": "_design/fetch",
        "views": {
            "byEmail": {
                "map": "function(doc) { if (doc.email) { emit(doc.email, doc);} }""",
            },
            "byUsername": {
                "map": "function(doc) { if (doc.username) { emit(doc.username, doc);} }""",
            },
            "byDesignation": {
                "map": """function(doc) {
                    if (doc.designation) {
                        emit(doc.designation, doc);
                    }
                }""",
            }
        },
        "language": "javascript"
    }
    DBUSERS.create_document(designDoc)
    designDoc = {
        "_id": "_design/fetch",
        "views": {
            "byUsername": {
                "map": """function(doc) {
                    if (doc.username) {
                        emit(doc.username, doc);
                    }
                }""",
            },
            "byDate": {
                "map": """function(doc) {
                    if (doc.date) {
                        emit(doc.date, doc);
                    }
                }""",
            }
        },
        "language": "javascript"
    }
    DBNOTIFICATION.create_document(designDoc)


def populateData(request):
    DBUSERS = client['users']
    with open('devFunctions/users.json') as data_file:
        data = json.load(data_file)
        for user in data:
            DBUSERS.create_document(user)


def displayUsers(request):
    return HttpResponse(User.objects.all())
