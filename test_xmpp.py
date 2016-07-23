#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-
import xmpp
import sys, os

server = "chat.asmallorange.com"
user = "asownormandin"
passwd = "Ce2Z6vQG9aKVYLkM"

recipient = sys.argv[1]
msg = sys.argv[2]

client = xmpp.Client(server)
client.connect(server=(server,5223))
client.auth(xmpp.protocol.JID(user).getNode(),passwd,'PokeyMSG')
client.sendInitPresence()
message = xmpp.protocol.Message(recipient+'@'+server,msg)
message.setAttr('type','chat')
client.send(message)
