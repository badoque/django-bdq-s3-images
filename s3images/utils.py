from PIL import Image
import math

DEFAULT_IMAGE_SIZES = {
	'xs': 100,
	'sm': 400,
	'md': 700,
	'lg': 1000,
	'xl': 2000,
	'thumbnail': 200
}

VALID_IMAGE_EXTENSIONS = [
	".jpg",
	".jpeg",
	".png",
	".gif",
]


# Verifies if URL ends with any of the valid extesions
# Parameters: 
#	* url - url to image (type: String)
#	* extension_list - List of valid extensions (type: String Array )
# Return type: Boolean
# Returns: True if URL is valid, otherwise False
def valid_url_extension(url, extension_list=VALID_IMAGE_EXTENSIONS):
	return any([url.endswith(e) for e in extension_list])



# Proportionally calculates a with based on a given height and image
# Parameters: 
#	* image - base image (type: Image object)
#	* height - base height (type: Int)
# Return type: Int
# Returns: width 
def proportional_width(image, height):
	height_percent = (height / float(image.size[1]))
	height_percent = math.ceil(height_percent*10)/10
	width = int((float(image.size[0]) * float(height_percent)))
	return width


# Proportionally calculates a height based on a given width and image
# Parameters: 
#	* image - base image (type: Image object)
#	* width - base width (type: Int)
# Return type: Int
# Returns: height 
def proportional_height(image, width):
	width_percent = (width / float(image.size[0]))
	width_percent = math.ceil(width_percent*10)/10
	height = int((float(image.size[1]) * float(width_percent)))
	return height



# Resizes an Image to a specified height. Image will be cropped 
# proportionally if needed, in order to keep a 1:1 aspect ratio.
# Parameters: 
#	* image - image to resize (type: Image object)
#	* height - base height (type: Int)
# Return type: Image object
# Returns: the image resized and cropped based on the height 
def image_to_thumbnail(image, height):
	image_to_resize = image.copy()
	box_width, box_height = image_to_resize.size

	# Check if aspect ratio of image is different from 1:1, cropping image if necessary
	if box_width != box_height:

		# Calculate left and right sides to crop proportionally
		if box_width > box_height:
			delta = box_width - box_height
			left_coordinate = int(delta/2)
			upper_coordinate = 0
			right_coordinate = box_height + left_coordinate
			lower_coordinate = box_height

		# Calculate upper and lower sides to crop proportionally
		else:
			delta = box_height - box_width
			left_coordinate = 0
			upper_coordinate = int(delta/2)
			right_coordinate = box_width
			lower_coordinate = box_width + upper_coordinate

		# Crop image proportionally, transforming the image aspect ratio to 1:1
		image_to_resize = image_to_resize.crop((left_coordinate, upper_coordinate, right_coordinate, lower_coordinate))
		
		# Resize image using the 'height' requested 
		# If size of the image is relativy greater than the height passed,
		# resize image to double the target size ('height')
		# with the fastest algorithm (NEAREST), then resize the 
		# smaller image to the target resolution with the best algorithm (ANTIALIAS)
		if box_height > (3 * height):
			image_to_resize.thumbnail((height * 2, height * 2))
			image_to_resize.thumbnail((height, height), Image.ANTIALIAS)
			return image_to_resize
		else:
			image_to_resize.thumbnail((height, height), Image.ANTIALIAS)
			return image_to_resize

	# If aspect ratio of image is 1:1, resizes the image using the default height of a 'thumbnail'
	else:
		image_to_resize.thumbnail((height, height), Image.ANTIALIAS)
		return image_to_resize



# Returns a height value from a dictionary given a key (e.g. sm, md)
# If a height argument is passed, it will take precendence over the key
# Parameters: 
#	* dictionary - dictionary of dimensions (type: Dicionary).  Contains key-value 
#					pairs such as 'sm': 300, representing the dimension key and its value.
#	* key - dictionary's key to be used (type: String).
#	* default_height - (type: Int). It will be used if a given key is not found 
#					and a height argument is not provided
#	* height - base height (type: Int). It will take precendence over a 'key' argument.
#	* max_height - (type: Int). It will take precedence if the height argument is greater
# Return type: Int
# Returns: the height to be used when resizing a Image object 
def height_from_dictionary(dictionary, default_height, key=None, height=None, max_height=None):

	# Inicial settings
	image_max_height = max_height
	dictionary_key = key
	base_height = height

	# If the param 'height' exists, it will take precedence over 'size' if specified
	if base_height is not None:
		dictionary_key = None

		if image_max_height is not None:
			# If 'height' requested is greater than the max height, then the max height will be used instead
			image_height_to_be_used = int(base_height) if int(base_height) <= image_max_height else image_max_height
		else:
			image_height_to_be_used = default_height


	# Check if an image size was passed in the request
	if dictionary_key is not None:

		# Check if the size requested is a default image size (e.g. xs, sm, md...)
		if dictionary_key in dictionary:
			# Set 'height' as the height equivalent to the size requested (note: see dictionary)
			image_height_to_be_used = dictionary[dictionary_key]
		else:
			# If 'size' is not valid, height will be 'md' (medium)
			image_height_to_be_used = default_height

	# If neither 'size' nor 'height' are specifield, height will be 'md' (medium)
	if dictionary_key==None and base_height==None:
		image_height_to_be_used = default_height

	return image_height_to_be_used

