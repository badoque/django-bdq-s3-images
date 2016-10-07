from django.shortcuts import render
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework import status

from .models import ExternalImage
from .models import ProcessedImage

from django.http import HttpResponse
from django.http import HttpResponseRedirect
import math
from django.views.generic import View
from django.shortcuts import get_object_or_404


# Create your views here.
class ExternalImageUploadUrlSign(APIView):

    def generate_full_path(self, original_filename):
        from uuid import uuid4

        ext = original_filename.split('.')[-1]
        new_filename = "%s.%s" % (uuid4(), ext)
        while ExternalImage.objects.filter(url__iendswith=new_filename).count() != 0:
            new_filename = "%s.%s" % (uuid4(), ext)

        return ("general_images/%s" % (new_filename), new_filename)

    def sign_url(self, request):
        import urllib
        import base64
        import hmac
        from hashlib import sha1
        import time
        from django.http import JsonResponse
        from django.conf import settings
        import datetime
        import json

        object_name = request.GET.get('s3_object_name')
        mime_type = request.GET.get('s3_object_type')
        
        path, new_filename = self.generate_full_path(object_name)
        expires = (datetime.datetime.utcnow()+datetime.timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        policy = json.dumps({
            "expiration": expires,
            "conditions": [
                {"bucket": settings.AWS_STORAGE_BUCKET_NAME},
                ["starts-with", "$key", path[0:len(path) - len(new_filename)]],
                {"acl": "public-read"},
                ["eq", "$Content-Type", mime_type],
                ["eq", "$filename", new_filename]
            ]
        })
        

        encoded_policy = base64.b64encode(policy.encode('utf-8')) # Here we base64 encode a UTF-8 version of our policy.  Make sure there are no new lines, Amazon doesn't like them.    
        signature = base64.b64encode(hmac.new(bytes(settings.AWS_SECRET_ACCESS_KEY, 'utf-8'), encoded_policy, sha1).digest()).decode('utf-8')
        
        url = 'https://%s.s3.amazonaws.com' % settings.AWS_STORAGE_BUCKET_NAME
        
        return Response({
                'signed_request': '%s/%s?AWSAccessKeyId=%s&Expires=%s&signature=%s' % (url, path , settings.AWS_ACCESS_KEY_ID, expires, signature),
                'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
                'url': url,
                'acl': 'public-read',
                'signature': signature,
                'expires': expires,
                'policy': encoded_policy.decode('utf-8'),
                'path': path,
                'file_name': new_filename,
            }, status=status.HTTP_200_OK)

    def get(self, request):
        return self.sign_url(request)

class PutExternalImageUploadUrlSign(APIView):

    def generate_full_path(self, original_filename):
        from uuid import uuid4

        ext = original_filename.split('.')[-1]
        new_filename = "%s.%s" % (uuid4(), ext)
        while ExternalImage.objects.filter(url__iendswith=new_filename).count() != 0:
            new_filename = "%s.%s" % (uuid4(), ext)

        return ("general_images/%s" % (new_filename,), new_filename)

    def sign_url(self, request):
        import urllib
        import base64
        import hmac
        from hashlib import sha1
        import time
        from django.http import JsonResponse
        from django.conf import settings
        import datetime
        import json

        object_name = request.GET.get('s3_object_name')
        mime_type = request.GET.get('s3_object_type')
        expires = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S") + ' GMT'
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        path, new_filename = self.generate_full_path(object_name)

        string_to_sign = 'PUT\n\n%s\n%s\n/%s/%s' % (mime_type, expires, bucket, path)

        print(string_to_sign)

        aws_signature = base64.b64encode(hmac.new(
                bytes(settings.AWS_SECRET_ACCESS_KEY, 'utf-8'), 
                string_to_sign.encode('utf-8'),
                sha1
            ).digest()).decode('utf-8')
        aws_auth_header = 'AWS ' + settings.AWS_ACCESS_KEY_ID + ':' + aws_signature
                
        return Response({
                'aws_auth_header': aws_auth_header,
                'expires': expires,
                'path': path,
                'file_name': new_filename,
            }, status=status.HTTP_200_OK)

    def get(self, request):
        return self.sign_url(request)


class HerokuExternalImageUploadUrlSign(APIView):

    def generate_full_path(self, original_filename):
        from uuid import uuid4

        ext = original_filename.split('.')[-1]
        new_filename = "%s.%s" % (uuid4(), ext)
        while ExternalImage.objects.filter(url__iendswith=new_filename).count() != 0:
            new_filename = "%s.%s" % (uuid4(), ext)

        return ("general_images/%s" % (new_filename), new_filename)

    def sign_url(self, request):
        import urllib
        import base64
        import hmac
        from hashlib import sha1
        import time
        from django.http import JsonResponse
        from django.conf import settings
        import datetime
        import json

        object_name = request.GET.get('s3_object_name')
        mime_type = request.GET.get('s3_object_type')
        
        path, new_filename = self.generate_full_path(object_name)
        expires = (datetime.datetime.utcnow()+datetime.timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        policy = json.dumps({
            "expiration": expires,
            "conditions": [
                {"bucket": settings.AWS_STORAGE_BUCKET_NAME},
                ["starts-with", "$key", path[0:len(path) - len(new_filename)]],
                {"acl": "public-read"},
                ["eq", "$Content-Type", mime_type],
                ["eq", "$filename", new_filename]
            ]
        })
        

        encoded_policy = base64.b64encode(policy.encode('utf-8')) # Here we base64 encode a UTF-8 version of our policy.  Make sure there are no new lines, Amazon doesn't like them.    
        signature = base64.b64encode(hmac.new(bytes(settings.AWS_SECRET_ACCESS_KEY, 'utf-8'), encoded_policy, sha1).digest()).decode('utf-8')
        
        url = 'https://%s.s3.amazonaws.com' % settings.AWS_STORAGE_BUCKET_NAME
        
        return Response({
                'url': '%s/%s?AWSAccessKeyId=%s&Expires=%s&signature=%s' % (url, path , settings.AWS_ACCESS_KEY_ID, expires, signature),
                'data': policy
            }, status=status.HTTP_200_OK)

    def get(self, request):
        return self.sign_url(request)

# Redirects client to an image on Amazon S3 given a valid image ID
# Params (optional):
#       * size - size of image requested (e.g. sm, md, lg, thumbnail...)
#       * height - height of image requested (e.g. 500, 600...)
# Obs.: If no params are given, redirects to image in original size
class ProcessedImageRedirect(View):

    def get(self, request, id):
        image = get_object_or_404(ExternalImage, id=id)

        # Get params from request
        image_size_requested = request.GET.get('size')
        image_height_requested = request.GET.get('height')

        # Height will take precedence over size in case both params are passed
        if image_height_requested is not None:
            image_size_requested = None

        # If no params are passed, redirects to image in original size
        if image_size_requested==None and image_height_requested==None:
            return HttpResponseRedirect(str(image.url))

        # In case params are passed
        else:
            if image_size_requested=='thumbnail':
                processed_image = image.get_or_create_thumbnail()

            else:
                processed_image = image.get_or_create_processed_image(
                        image_size_requested, image_height_requested)

            return HttpResponseRedirect(str(processed_image.url))
            #return HttpResponsePermanentRedirect(str(new_image_key_url))


