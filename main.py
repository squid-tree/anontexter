import settings 
import pgpy 
import fabric
import os
import multiprocessing
from pgpy import PGPKey
import inspect
from fabric import Connection
from settings.settings import * 
from datetime import datetime

pwd = os.path.dirname(os.path.realpath(__file__))

recpgp = PGPKey()
usrpgp = PGPKey()
usrpgp.unlock('test')

recpgp = PGPKey.from_file(str('%s/settings/recipientkey.asc' % pwd))
usrpgp = PGPKey.from_file(str('%s/settings/userkey.asc' % pwd))

usrpgp = usrpgp[0]

while True:
    password = input(str("Password for your secret pgp key: "))
    try:
        usrpgp.unlock(password)
    except pgpy.errors.PGPDecryptionError:
        print("The password was wrong, try again")
        continue
    except Exception as e:
        print(repr(e))
        continue
    else:
        print("Password was correct, messages may now be encrypted")
        break

while True:
    pwd = input("Password for the server: ")
    try:
        conn = fabric.Connection(host=sshhost, user=sshuser, port=sshport, connect_kwargs={'password': pwd}, connect_timeout=5)
    except TimeoutError:
        print("Timed out: dets might be wrong")
        continue
    except:
        print("There was an error connecting with that password, try again")
        continue
    else:
        try:
            messagelist = conn.run('ls %s' % messagesdirectory).stdout
        except:
            print("Timed out (password or other dets might be wrong")
            continue
        else:
            break

filelist=messagelist.splitlines()
filelist.sort()
filemessages={}

for i in filelist:
    try:
        msgcat = conn.run('cat \'%s\'/\'%s\'' % (messagesdirectory,i))
    except TimeoutError:
        print("Timed out (password or other dets might be wrong)")
        quit()
    filemessages[i] = msgcat.stdout

os.system('clear')

print("Loading decryptable messages from server ... ")
for i in filemessages:
    msg = pgpy.PGPMessage.from_blob(filemessages[i])
    try: 
        with usrpgp.unlock(password):
            decryptmsg = usrpgp.decrypt(msg).message
    except Exception as e:
        print("%sUnencryptable message(Could be made by you or another message not intended towards you" % i)
        continue
    else:
        print ("%s  %s" % (i, decryptmsg))

while True:
    message = pgpy.PGPMessage.new(input("> "))
    
    filename = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print('Encrypting Message ... ')
    print(recpgp[0])
    msg = recpgp[0].encrypt(message)

    print('Posting Message to Server ...')
    try:
        conn.run(str("echo \'%s\' > %s/\'%s\'" % (msg, messagesdirectory, filename)))
    except:
        print("There was an error")
    else:
        print("Message successfully sent")
