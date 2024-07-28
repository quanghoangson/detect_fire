from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from rest_framework.exceptions import ValidationError
from threading import Thread


import re
from django.conf import settings
import os

# Thread decorator definition
def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

# Upload alert
@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def post_alert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        identify_email_sms(serializer)

    else:
        return "Error: Unable to process data!"

    return Response(request.META.get('HTTP_AUTHORIZATION'))

# Identifies if the user provided an email 
def identify_email_sms(serializer):

    if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', serializer.data['alert_receiver'])):  
        print("Valid Email")
        send_email(serializer)
    elif re.compile("[+84][0-9]{10}").match(serializer.data['alert_receiver']):
        # 1) Begins with +3706
        # 2) Then contains 7 digits 
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")

#  SMS
@start_new_thread
def send_sms(serializer):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(body=prepare_alert_message(serializer),
                                    from_=settings.TWILIO_NUMBER,
                                    to=serializer.data['alert_receiver'])

# Sends email
@start_new_thread
def send_email(serializer):
    
    subject = 'Weapon Detected!'
    message = prepare_alert_message(serializer) 
    email = EmailMessage(subject, message, 'firedetectsystem@gmail.com', [serializer.data['alert_receiver']])
    
    # Attach the image file to the email
    image_path = os.path.join(settings.MEDIA_ROOT, serializer.data['image'].strip('/')) 
    print(image_path)
 
    try:
        # Send the email using send_mail
        with open(image_path, 'rb') as image_file:
            email.attach(filename='weapon_image.jpg', content=image_file.read(), mimetype='image/jpeg')

        email.send(fail_silently=True)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")  



# Prepares the alert message
def prepare_alert_message(serializer):
    uuid_with_slashes = split(serializer.data['image'], ".")
    uuid = uuid_with_slashes[0]

    print("uuid: ", uuid)
    url = 'http://127.0.0.1:8000/alerts' + uuid
    print("URL: ", url)
    return '\nWeapon Detected! \nView alert at ' + url

# Splits string into a list
def split(value, key):
    return str(value).split(key)