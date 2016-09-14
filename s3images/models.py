from django.db import models
from image_management.utils import *

# Create your models here.
class ExternalImage(models.Model):
    url = models.TextField()
    type = models.CharField(max_length=60)
    size = models.IntegerField()

    def _get_path_to_save(self):
        # Return path to save image

        return 'media/'


    def _save_to_s3(self, image_to_process_string):
        from django.conf import settings
        from boto.s3.connection import S3Connection
        from uuid import uuid4

        path_to_save = self._get_path_to_save()

        # Connect to Amazon S3
        s3_connection = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        s3_bucket = s3_connection.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

        # Create new image and upload to S3
        image_extension = '.' + self.type.split('/')[1]
        new_image_key = s3_bucket.new_key('%s%s%s' % (path_to_save, uuid4(), image_extension))
        new_image_key.content_type = self.type              
        new_image_key.set_contents_from_string(image_to_process_string.getvalue())
        new_image_key.make_public()
        new_image_key_url = new_image_key.generate_url(expires_in=0, query_auth=False)

        return new_image_key_url


    def _run_resize_algorythm(self, image_to_process, image_width_to_be_used, image_height_to_be_used):
        from PIL import Image
        import cStringIO
        
        # If size requested is not thumbnail
        # Check if original height of image is three times greater than height of thumbnail
        if(image_to_process.size[1] > (image_height_to_be_used*3)):
            # resize image to double the target size ('image_height_to_be_used*2')
            # with the fastest algorithm (NEAREST), then resize the 
            # smaller image to the target resolution with the best algorithm (ANTIALIAS)
            image_to_process.thumbnail((image_width_to_be_used*2, image_height_to_be_used*2))
            image_to_process.thumbnail((image_width_to_be_used, image_height_to_be_used), Image.ANTIALIAS)
        else:
            # resize image using best algorithm (ANTIALIAS)
            image_to_process.thumbnail((image_width_to_be_used, image_height_to_be_used), Image.ANTIALIAS)

        # Saving the image into a cStringIO object to avoid writing to disk
        image_to_process_string = cStringIO.StringIO()
        image_to_process.save(image_to_process_string, self.type.split('/')[1].upper())

        return (image_to_process, image_to_process_string)

    def _get_size_name(self, image_height_to_be_used):
        # Name size of the processed image on database
        size_name = None
        for size in DEFAULT_IMAGE_SIZES:
            if DEFAULT_IMAGE_SIZES[size]==image_height_to_be_used and str(size)!='thumbnail':
                size_name = str(size)

        size_name = size_name if (size_name is not None) else str(image_height_to_be_used)

        return size_name


    def _get_image_dimensions(self, image_to_process, size_key=None, height=None):
        # Max height that image can have
        image_max_height = 2000

        # Chooses a height from the dictionary based on the size requested (e.g. sm, md, lg...)
        height = height_from_dictionary(dictionary=DEFAULT_IMAGE_SIZES, 
            default_height=700, key=size_key, height=height, max_height=image_max_height)

        # Proportionally calculate 'width' based on 'height'
        width = proportional_width(image_to_process, height)

        return (width, height)


    def _request_image(self):
        import requests
        import StringIO
        from PIL import Image

        # Requests original image to process
        request_image_to_process = requests.get(str(self.url))

        # Converts response content to string
        image_to_process_string = StringIO.StringIO(request_image_to_process.content)

        # Converts string to Image object
        image_to_process = Image.open(image_to_process_string)

        return (image_to_process, image_to_process_string)

    def create_processed_image(self, size_key=None, height=None):  
        image_to_process, image_to_process_string = self._request_image()

        image_width_to_be_used, image_height_to_be_used = self._get_image_dimensions(
                                                    image_to_process, size_key=size_key, height=height)

        image_to_process, image_to_process_string = self._run_resize_algorythm(image_to_process, image_width_to_be_used, image_height_to_be_used)

        new_image_key_url = self._save_to_s3(image_to_process_string)

        processed_image = ProcessedImage(external_image=self, size=self._get_size_name(image_height_to_be_used),
             url=new_image_key_url)
        processed_image.save()

        return processed_image

    def create_thumbnail(self):     
        import cStringIO
        image_to_process, image_to_process_string = self._request_image()
        # If a thumbnail is requested, image will be proportionally cropped to a 1:1 aspect ratio if needed
        # and then resized to a thumbnail height, as specified by DEFAULT_IMAGE_SIZES
        image_to_process = image_to_thumbnail(image_to_process, int(DEFAULT_IMAGE_SIZES['thumbnail']))
       
        # Saving the image into a cStringIO object to avoid writing to disk
        image_to_process_string = cStringIO.StringIO()
        image_to_process.save(image_to_process_string, self.type.split('/')[1].upper())
        
        new_image_key_url = self._save_to_s3(image_to_process_string)
        processed_image = ProcessedImage(external_image=self, size='thumbnail', url=new_image_key_url)
        processed_image.save()
        return processed_image


    def get_or_create_processed_image(self, size_key=None, height=None):
        try:
            if size_key is not None:
                return self.processed_images.filter(size=size_key)[0]
            else:
                return self.processed_images.filter(size=str(height))[0]

        except IndexError:
            return self.create_processed_image(size_key=size_key, height=height)

    def get_or_create_email_clipping_thumbnail(self):
        try:
            return self.processed_images.filter(size='email')[0]

        except IndexError:
            image_to_process, image_to_process_string = self._request_image()
            if image_to_process.size[0] > image_to_process.size[1]:
                height = proportional_height(image_to_process, 134)
                width = 134
            else:
                width = proportional_width(image_to_process, 134)
                height = 134

            image_to_process, image_to_process_string = self._run_resize_algorythm(image_to_process, width, height)

            new_image_key_url = self._save_to_s3(image_to_process_string)

            processed_image = ProcessedImage(external_image=self, size='email',
                 url=new_image_key_url)
            processed_image.save()

            return processed_image



    def get_or_create_thumbnail(self):
        try:
            return self.processed_images.filter(size='thumbnail')[0]

        except IndexError:
            return self.create_processed_image()

    def get_or_create_logo(self):
       return self.get_or_create_processed_image(height=60)


class ProcessedImage(models.Model):
    external_image = models.ForeignKey('ExternalImage', related_name='processed_images')
    size = models.CharField(max_length=30)
    url = models.TextField()