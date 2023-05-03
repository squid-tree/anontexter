### DESIGN ### 
##  Script Design ##
# A server listens for an encrypted input, which the intended user can then request
# and translate
## Security Design ##
# Each user should have their own individual set of pgp keys, which the server 
# doesn't have access to. When a user requests messages, the local client should
# only take those messages that can be translated with their key. Users should b 
# able to specify a key before starting the program, which their messages will then
# be translated too. It's important that the server plays a passive role and thus
# if someone were to somehow hack into it all information would be encrypted

### CLIENT MODE ### 
import scripts
import settings 
import pgpy 
import fabric

# Get the pgp keys 
with open('recipientkey.txt', 'r') as file:
    recpgp = file.read()
with open('userkey.txt', 'r') as file:
    usrpgp = file.read()

recpgp = pgpy.PGPkey.from_blob(recpgp)
usrpgp = pgpy.PGPkey.from_blob(usrpgp)

while True:
    password = input("Password for your private pgp key: ")
    try:
        usrpgp.unlock(password)
    except PGPDecryptionError:
        print("The password was wrong, try again")
        continue
    except:
        print("Something went wrong, try again")
        continue
    else:
        print("Password was correct, messages may now be encrypted")
        break

# Get connection details for server
from fabric import Connection
from anontexter.settings.settings import * 

while True:
    pwd = input("Password for the server: ")
    try:
        conn = Connection(host=sshhost, user=sshuser, port=sshport, connect_kwargs={'password': pwd})
    except:
        print("There was an error connecting with that password, try again")
        continue
    else:
        break

# Get messages from server
messagelist = conn.run('ls %s' % messagesdirectory)

filelist=messagelist.stdout.splitlines()
filelist.sort()

filemessages={}

for i in filelist:
    msgcat = conn.run('cat %s/%s' % (messagesdirectory,i))
    filemessages[i] = msgcat.stdout

# Display messages chronologically
print("Loading decryptable messages from server ... ")
for i in filemessages:
    msg = pgpy.PGPMessage.new(filemessages[i])
    try: 
        decryptmsg = usrpgp.decrypt(msg).message
    except:
        print("")
    else:
        print ("%s  %s" % (i, filemessages[i]))
        print('\n')

# Allow the user to input more messages to the server

from datetime import datetime

while True:
    message = PGPMessage.new(input("> "))
    
    filename = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print('Encrypting Message ... ')
    msg = recpgp.encrypt(message)

    print('Posting Message to Server ...')
    try:
        conn.run(str("echo \'%s\' > %s/%s" % (msg, messagesdirectory, filename)))
    except:
        print("There was an error")
    else:
        print("Message successfully sent")
