# from kivy import * 
from copy import copy
import gc
import json
import math
import os
from io import BytesIO
from random import shuffle
# import cv2
import ffmpeg

#os.environ['KIVY_IMAGE'] = 'pil'
os.environ["KIVY_VIDEO"] = "ffpyplayer"

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics import RenderContext, Color, Rectangle, Line
from kivy.uix.video import Video
from kivy.uix.label import Label
from kivymd.uix.fitimage import FitImage
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.carousel import Carousel
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect
from PIL import Image as PilImage, ImageFilter as PilImageFilter, ImageFile
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithNoMenu, Settings
from kivy.config import ConfigParser
from kivy.uix.anchorlayout import AnchorLayout
# from skimage import color as sk_color
# import numpy as np
from screeninfo import get_monitors
from kivy.modules import inspector
from kivy.uix.button import Button

#ImageFile.LOAD_TRUNCATED_IMAGES = True

MANAGER = None
CAROUSEL = None
NAV = None
SLIDE_DURATION = 10
SLIDE_ADVANCE_EVENT = None
RESET_ZOOM_EVENT = None
CLOSE_NAV_TIMEOUT = None
LOCKED = False
DEBUG = False

PERFORMANT_MODE = True

CURRENT_SETTINGS = None

PIXEL_FILES = ['MakDeetsMuch1645881808448536576.png', 'child0.png', 'child1.png', 'KadaburaDraws1566865598193319938.png']
FILES_DIR = '../fanart'
SETTINGS_FILE = f'{FILES_DIR}/settings.json'

CONFIG = ConfigParser()
# try:
# 	1/0
# 	CONFIG.read('fanart_config.ini')
# 	# CONFIG.setdefaults('general', {
# 	# 	'slide_duration': SLIDE_DURATION,
# 	# 	'display_images': True,
# 	# 	'display_videos': True,
# 	# 	'display_gifs': True,
# 	# 	'display_long_images': True,
# 	# 	'display_bad_aspect_ratio': True,
# 	# 	'only_pixel_art': False,
# 	# })
# 	# # with open('fanart_config.ini', 'w') as configfile:
# 	# CONFIG.write()
# except:
# 	CONFIG.setdefaults('general', {
# 		'slide_duration': SLIDE_DURATION,
# 		'display_images': 1,
# 		'display_videos': 1,
# 		'display_gifs': 1,
# 		'display_long_images': 1,
# 		'display_bad_aspect_ratio': 1,
# 		'only_pixel_art': 0,
# 	})
# 	# with open('fanart_config.ini', 'w') as configfile:
# 	CONFIG.write()
CONFIG.read('fanart_config.ini')
if not os.path.exists('fanart_config.ini'):
	# CONFIG['landscape'] = True
	# CONFIG['general'] = {}
	# CONFIG.set('general', 'proceed_speed', SLIDE_DURATION)
	# CONFIG.set('general', 'display_images', True)
	# CONFIG.set('general', 'display_videos', True)
	# CONFIG.set('general', 'display_gifs', True)
	# CONFIG.set('general', 'display_long_images', True)
	# CONFIG.set('general', 'display_bad_aspect_ratio', True)
	# CONFIG.set('general', 'only_pixel_art', False)
	CONFIG.setdefaults('general', {
		'slide_duration': SLIDE_DURATION,
		'display_images': 1,
		'display_videos': 1,
		'display_gifs': 1,
		'display_long_images': 1,
		'display_bad_aspect_ratio': 1,
		'only_pixel_art': 0,
	})
	# with open('fanart_config.ini', 'w') as configfile:
	CONFIG.write()
	# monitor orientation: landscape xor vertical
	# proceed speed
	# display images: true xor false
	# display gifs: true xor false
	# display videos: true xor false
	# display long images: true xor false
	# display images that are bad for orientation: true xor false (maybe with a cutoff?)
	# only pixel art: true xor false
	# debug

def play_slide_if_video(slide):
	if isinstance(slide, Video):
		if slide.state != "play":
			slide.state = "play"
	else:
		if slide is not None and slide.children:
			for child in slide.children:
				if isinstance(child, Video):
					if child.state != "play":
						child.state = "play"
					break

def advance_carousel(dt):
	global CAROUSEL
	# if isinstance(CAROUSEL.next_slide, Video):
	# 	CAROUSEL.next_slide.state = "play"
	play_slide_if_video(CAROUSEL.next_slide)
	CAROUSEL.load_next()

	# global SLIDE_ADVANCE_EVENT
	# SLIDE_ADVANCE_EVENT = Clock.schedule_once(advance_carousel, SLIDE_DURATION)

def clear_slide_advance():
	global SLIDE_ADVANCE_EVENT
	if SLIDE_ADVANCE_EVENT is not None:
		Clock.unschedule(SLIDE_ADVANCE_EVENT)
		SLIDE_ADVANCE_EVENT = None

def enqueue_slide_advance(duration=int(CONFIG.get('general', 'slide_duration'))):
	global SLIDE_ADVANCE_EVENT
	if SLIDE_ADVANCE_EVENT is not None:
		Clock.unschedule(SLIDE_ADVANCE_EVENT)
	SLIDE_ADVANCE_EVENT = Clock.schedule_once(advance_carousel, duration)

def clear_reset_zoom():
	global RESET_ZOOM_EVENT
	if RESET_ZOOM_EVENT is not None:
		Clock.unschedule(RESET_ZOOM_EVENT)
		RESET_ZOOM_EVENT = None

def old_blur(parent, filepath, window_width, window_height):
	# not performant; this seems to be a large/the lain cuase of stuttering
	with PilImage.open(filepath) as pil_image:
		try:
			blurred_pil_image = pil_image.filter(PilImageFilter.BoxBlur(70))
		except ValueError:
			blurred_pil_image = pil_image.convert("RGB").filter(PilImageFilter.BoxBlur(70))
		data = BytesIO()
		blurred_pil_image.save(data, format='png')
		data.seek(0) # yes you actually need this

		almost_blurred = CoreImage(BytesIO(data.read()), ext='png', nocache=True)
		# blurred = Image(size=(window_width, window_height), fit_mode='cover', nocache=True)
		blurred = Image(size=(window_width, window_height), fit_mode='fill', nocache=True)
		blurred.texture = almost_blurred.texture
		parent.add_widget(blurred)

		radial_gradient = RadialGradient(window_width, window_height, (1,1,1,.25), (0,0,0,0.375))
		parent.add_widget(radial_gradient)

		del almost_blurred
		del blurred_pil_image
		del data

	del pil_image

def new_blur(parent, filepath, window_width, window_height, image):
	# right i forgot... the out of the box blur looks bad. it chunks it 
	# so it looks like a pixelated mess. so we have to do it ourselves.
	# for all i know it could also be slow.
	# alternatively, i could precalculate the blurred images...
	print('adding new blur')
	w = EffectWidget()
	w.add_widget(Image(texture=image.texture, size=(window_width, window_height), fit_mode='fill', nocache=True))
	w.effects = [HorizontalBlurEffect(size=window_width), VerticalBlurEffect(size=window_height)]
	w.size = (window_width, window_height)

	print(w)
	parent.add_widget(w)

def newer_blur(filename, window_width, window_height):
	filename = os.path.splitext(filename)[0]
	blurred_dir = os.path.join(FILES_DIR, 'blurred')
	if not os.path.exists(blurred_dir):
		return
	filepath = os.path.join(blurred_dir, f'{filename}.jpg')
	# print(filepath)
	print('blurred filepath:', filepath)
	image = CoreImage(filepath, keep_data=True, nocache=True)
	return Image(texture=image.texture, size=(window_width, window_height), fit_mode='cover', nocache=True)

class RadialGradient(BoxLayout):
	def __init__(self, window_width, window_height, start_color, end_color):
		super(RadialGradient, self).__init__()
		self.width = window_width
		self.height = window_height
		self.add_gradient(start_color, end_color)

	def add_gradient(self, start_color, end_color):
		max_radius = math.floor(math.sqrt((self.width / 2) ** 2 + (self.height / 2) ** 2))
		center_x = self.width / 2
		center_y = self.height / 2

		# print('center_x:', center_x)
		# print('center_y:', center_y)

		r_step = (start_color[0] - end_color[0]) / max_radius
		g_step = (start_color[1] - end_color[1]) / max_radius
		b_step = (start_color[2] - end_color[2]) / max_radius
		a_step = (start_color[3] - end_color[3]) / max_radius

		current_color = end_color

		# self.canvas.add(Color(rgba=(0, 1, 0, 1)))
		# # self.canvas.add(Line(points=[sep, 0, sep, self.height], width=1))
		# self.canvas.add(Line(circle=(center_x, center_y, 1500)))

		for radius in range(max_radius + 1, -1, -1):
			# print(current_color)
			# print(radius)
			self.canvas.add(Color(rgba=current_color))
			# self.canvas.add(Line(points=[sep, 0, sep, self.height], width=1))
			self.canvas.add(Line(circle=(center_x, center_y, radius)))
			current_color = (
				current_color[0] + r_step,
				current_color[1] + g_step,
				current_color[2] + b_step,
				current_color[3] + a_step,
			)

		# alpha_channel_rate = 0
		# increase_rate = 1 / self.width

		# for sep in range(self.width):
		# 	self.canvas.add(Color(rgba=(0, 1, 0, alpha_channel_rate)))
		# 	# self.canvas.add(Line(points=[sep, 0, sep, self.height], width=1))
		# 	self.canvas.add(Line(circle=(center_x, center_y, sep)))
		# 	alpha_channel_rate += increase_rate

# class BlurredBackgroundImage(FitImage):
# 	def __init__(self, **kwargs):
# 		fs = '''
# 		$HEADER$

# 		uniform vec2 resolution;

# 		void main(void) {
# 			int radius = 4;
# 			vec2 d = float(radius) / resolution;
# 			for (int dx = -radius; dx < radius; dx++)
# 				for (int dy = -radius; dy < radius; dy++)
# 					gl_FragColor += texture2D(texture0, tex_coord0 + vec2(float(dx), float(dy)) * d);

# 			gl_FragColor /= float( 4 * radius * radius);
# 		}
# 		'''
# 		self.canvas = RenderContext()
# 		# self.canvas.shader.fs = fs
# 		super(BlurredBackgroundImage, self).__init__(**kwargs)

# 	def on_size(self, *args):
# 		self.canvas['projection_mat'] = Window.render_context['projection_mat']
# 		self.canvas['modelview_mat'] = Window.render_context['modelview_mat']
# 		self.canvas['resolution'] = list(map(float, self.size))
# 		print("size changed")

# 	# tried updating the shader whenever the position changes but still no improvements
# 	'''def on_pos(self, *args):
# 		self.canvas['projection_mat'] = Window.render_context['projection_mat']
# 		self.canvas['modelview_mat'] = Window.render_context['modelview_mat']
# 		self.canvas['resolution'] = list(map(float, self.size))
# 		print("pos changed")'''

def get_forced_background(file_settings, filename, window_width, window_height):
	forced_background = file_settings.get(filename, {}).get('background', '')

	if forced_background is None or forced_background == '':
		return None

	if forced_background == 'b':
		return newer_blur(filename, window_width, window_height)
	elif is_hex(forced_background):
		color = hex_to_color(forced_background)
		print("color", color, forced_background)
		return Image(color=color, size_hint=(1.0, 1.0), nocache=True)

def align(widget, orientation, width, height, window_width, window_height):
	actual_width = width * (window_height / height) if height > window_height else width
	if orientation == 'l':
		# image_widget.pos_hint = {'left': 1}
		# image_widget.pos_hint = {'x': -1}
		# image_widget.pos_hint = {'x': -0.5}
		# image_widget.pos = (0, 0)
		# image_widget.pos = (0, 0)
		# anchor = AnchorLayout(size_hint=(1.0, 1.0), size=(window_width, window_height), anchor_x='left', anchor_y='center')
		# anchor.add_widget(image_widget)
		# parent.add_widget(anchor)
		widget.pos = (0 - (window_width - actual_width) / 2, 0)
	elif orientation == 'r':
		# image_widget.pos_hint = {'right': 1}
		# image_widget.pos_hint = {'x': 1}
		# image_widget.pos_hint = {'x': 0.5}
		# print('image widget width:', image_widget.width, image.width)
		widget.pos = ((window_width - actual_width) / 2, 0)
		# anchor = AnchorLayout(size_hint=(1.0, 1.0), size=(window_width, window_height), anchor_x='right', anchor_y='center')
		# image_widget.anchor_x = 'right'
		# anchor.add_widget(image_widget)
		# parent.add_widget(anchor)

def free_stencil(stencil_view):
	scatter = stencil_view.children[0]
	for child in scatter.children:
		del child
	del scatter

class CustomScatterLayout(ScatterLayout):
	def __init__(self, **kwargs):
		super(CustomScatterLayout, self).__init__(**kwargs)
		self.window_width = self.width
		self.window_height= self.height

	def on_size(self, instance, value, **kwargs):
		self.window_width = value[0]
		self.window_height = value[1]
		# super(CustomScatterLayout, self).on_size(new_width, new_height, **kwargs)

	def schedule_reset(self):
		clear_slide_advance()
		clear_reset_zoom()

		def reset_zoom(dt):
			# scale should be whatever the initial scale is, which i don't think is necessarily 1.... although maybe it is?
			print('animating')
			anim = Animation(scale=1, duration=int(CONFIG.get('general', 'slide_duration')) / 4) & Animation(x=0, duration=int(CONFIG.get('general', 'slide_duration')) / 4) & Animation(y=0, duration=int(CONFIG.get('general', 'slide_duration')) / 4)
			anim.start(self)
			enqueue_slide_advance(int(CONFIG.get('general', 'slide_duration')) / 2)

		global RESET_ZOOM_EVENT
		RESET_ZOOM_EVENT = Clock.schedule_once(reset_zoom, int(CONFIG.get('general', 'slide_duration')) / 2)
		print('RESET_ZOOM_EVENT 1', RESET_ZOOM_EVENT)

	# set temp lock
	def on_transform_with_touch(self, arg, **kwargs):
		global LOCKED
		if not LOCKED:
			super(CustomScatterLayout, self).on_transform_with_touch(arg, **kwargs)

			# print(self.bbox)
			# print(arg)

			self.schedule_reset()

	def on_touch_move(self, arg, **kwargs):
		global LOCKED
		if not LOCKED:
			super(CustomScatterLayout, self).on_touch_move(arg, **kwargs)



			# max_x = (self.window_width - self.width) / 2
			# min_x = -max_x

			# print(self.x)
			# print(max_x)
			# if self.x < min_x:
			# 	self.x = min_x
			# elif self.x > max_x:
			# 	self.x = max_x



			# max_y = (self.window_height - self.height) / 2
			# min_y = -max_y
			# if self.y < min_y:
			# 	self.y = min_y
			# elif self.y > max_y:
			# 	self.y = max_y

			# max_x = (self.width * self.scale - self.window_width)
			# # min_x = -max_x

			# print(self.x)
			# print(max_x)
			# if self.x < 0:
			# 	self.x = 0
			# elif self.x > max_x:
			# 	self.x = max_x



			# max_y = (self.height * self.scale - self.window_height)
			# # min_y = -max_y
			# if self.y < 0:
			# 	self.y = 0
			# elif self.y > max_y:
			# 	self.y = max_y

			min_x = (self.window_width - self.width * self.scale)
			print(self.x)
			print(min_x)
			# min_x = -max_x

			# print(self.x)
			# print(max_x)
			if self.x < min_x:
				self.x = min_x
			elif self.x > 0:
				self.x = 0



			min_y = (self.window_height - self.height * self.scale)
			# min_y = -max_y
			if self.y < min_y:
				self.y = min_y
			elif self.y > 0:
				self.y = 0

	# def on_scale(self, instance, value):
	# 	global LOCKED
	# 	if not LOCKED:
	# 		super(CustomScatterLayout, self).on_scale(arg, **kwargs)

	# def on_x(self, obj, new_x, **kwargs):
	# 	# make sure that x doesn't become something that would allow a portion of the screen to not be covered by the scatter layout
	# 	# if self.bbox
	# 	# print(a)
	# 	# print(b)
	# 	# max_x = (self.window_width - self.width) / 2
	# 	# min_x = -max_x
	# 	# if new_x < min_x:
	# 	# 	self.x = min_x
	# 	# elif new_x > max_x:
	# 	# 	self.x = max_x
	# 	pass

	# def on_y(self, **kwargs):
	# 	pass


class PixelArt(CoreImage):
	def __init__(self, **kwargs):
		print('here1')

		super(PixelArt, self).__init__(**kwargs)
		self.texture.mag_filter = 'nearest'

	# def build(self):
	# 	print('here2')
	# 	self.texture.mag_filter = 'nearest'
	# 	print(self.texture)
	# 	# return self
	# 	return super(PixelArt, self).build()

class WhiteBackgroundLayout(RelativeLayout):
	def __init__(self, **kwargs):
		super(RelativeLayout, self).__init__(**kwargs)


# 		self.kv = Builder.load_string('''
# RelativeLayout:
# 	canvas.before:
# 		Color:
# 			rgba: 1, 1, 1, 1
# 		Rectangle:
# 			pos: self.pos
# 			size: self.size
# 		''')

class FileCarousel(Carousel):
	def __init__(self, files_dir, window_width, window_height, settings_file, **kwargs):
		super(FileCarousel, self).__init__(**kwargs)
		# self.file_list = file_list
		# self.num_files = len(file_list)
		self.files_dir = files_dir
		self.init_settings(settings_file)
		self.window_width = window_width
		self.window_height = window_height
		self.updating = False
		# self.true_index = 2
		self.is_moving = False
		self.applying_config = False
# 		self.kv = Builder.load_string('''
# Carousel:
# 	canvas.before:
# 	    Color:
# 	        rgba: 1, 1, 1, 1
# 	    Rectangle:
# 	        pos: self.pos
# 	        size: self.size
# 	    ''')
# 		# with self.canvas.before:
# 		# 	Color(1, 1, 1, 1)
# 		# 	self.rect = Rectangle(pos=self.pos, size=self.size)

	def init_settings(self, settings_file):
		with open(settings_file, 'r') as settings_file:
			self.file_settings = json.load(settings_file)

		print(self.file_settings)
		
	def get_widget_for_file(self, filepath, window_width, window_height):
		print(filepath)
		_, ext = os.path.splitext(filepath)
		filename = os.path.basename(filepath)
		if ext == '.mp4':
			widget = Video(source=filepath)
			widget.position = 0
			# self.slides[value].state = "play"
			widget.options = {'eos': 'loop'}
			widget.allow_stretch = True
			widget.loaded = True
			# video.state = "play"
			# video.options = {'eos': 'loop'}
			# video.allow_stretch = True
			# video.loaded = True
			orientation = self.file_settings.get(filename, {}).get('orientation', False)
			if orientation:
				# vid = cv2.VideoCapture(filepath)
				# height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
				# width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

				video_streams = ffmpeg.probe(filepath, select_streams = "v")
				width = video_streams['streams'][0]['width']
				height = video_streams['streams'][0]['height']

				align(widget, orientation, width, height, window_width, window_height)

				del video_streams

			background = get_forced_background(self.file_settings, filename, window_width, window_height)
			print("\n\n\n\n\nforced background", background)
			if background:
				print("background for video")
				parent = WhiteBackgroundLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				parent.add_widget(background)
				parent.add_widget(widget)
				widget = parent
			elif orientation:
				parent = WhiteBackgroundLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				parent.add_widget(widget)
				widget = parent

		elif ext == '.gif':
			anim_delay = 0.04 if filename in ['cannonbreed1576816909458149376_1.gif', 'cannonbreed1603175701049327616_1.gif'] else 0.1
			widget = Image(source=filepath, fit_mode='contain', anim_delay=anim_delay, nocache=True)

			orientation = self.file_settings.get(filename, {}).get('orientation', False)
			if orientation:
				# vid = cv2.VideoCapture(filepath)
				# height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
				# width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

				video_streams = ffmpeg.probe(filepath, select_streams = "v")
				width = video_streams['streams'][0]['width']
				height = video_streams['streams'][0]['height']

				print("width:", width, "height:", height)

				align(widget, orientation, width, height, window_width, window_height)

				del video_streams

			background = get_forced_background(self.file_settings, filename, window_width, window_height)
			if background:
				parent = WhiteBackgroundLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				parent.add_widget(background)
				parent.add_widget(widget)
				widget = parent
			elif orientation:
				parent = WhiteBackgroundLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				parent.add_widget(widget)
				widget = parent
		else:
			# if filename in PIXEL_FILES:
			if self.file_settings.get(filename, {}).get('is_pixel', False):
				image = CoreImage(filepath, keep_data=True, nocache=True)
				image.texture.mag_filter = 'nearest'
			else:
				image = CoreImage(filepath, keep_data=True, nocache=True)

			if not PERFORMANT_MODE:
				parent = CustomScatterLayout(do_rotation=False, scale_min=1)
			else:
				parent = WhiteBackgroundLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				# parent = AnchorLayout(size_hint=(1.0, 1.0), size=(window_width, window_height))
				# parent = 

			parent.size = (window_width, window_height)
			orientation = self.file_settings.get(filename, {}).get('orientation', False)

			# only need to create a background if the entire window isn't covered
			# if not PERFORMANT_MODE and image.height / image.width != window_height / window_width:
			if image.height / image.width != window_height / window_width:
				forced_background = get_forced_background(self.file_settings, filename, window_width, window_height)

				if forced_background:
					parent.add_widget(forced_background)
				else:
					if orientation and orientation == 'l':
						pixels = [
							image.read_pixel(image.texture.size[0] - 1, 0),
							image.read_pixel(image.texture.size[0] - 1, image.texture.size[1] - 1),
						]
					elif orientation and orientation == 'r':
						pixels = [
							image.read_pixel(0, 0),
							image.read_pixel(0, image.texture.size[1] - 1),
						]
					else:
						pixels = [
							image.read_pixel(0, 0),
							image.read_pixel(0, image.texture.size[1] - 1),
							image.read_pixel(image.texture.size[0] - 1, 0),
							image.read_pixel(image.texture.size[0] - 1, image.texture.size[1] - 1),
						]

					# print(pixel_1, pixel_2, pixel_3, pixel_4)

					if not all_pixels_transparent(pixels):
						# image does not have transparent edges, so apply a background
						background_color = get_background_color(pixels)
						if background_color is not None:
							parent.add_widget(Image(color=background_color, size_hint=(1.0, 1.0), nocache=True))
						else:
							# blur the image as the background
							# old_blur(parent, filepath, window_width, window_height)
							# new_blur(parent, filepath, window_width, window_height, image)
							bg = newer_blur(filename, window_width, window_height)
							parent.add_widget(bg)

							# with PilImage.open(filepath) as pil_image:
							# 	try:
							# 		blurred_pil_image = pil_image.filter(PilImageFilter.BoxBlur(70))
							# 	except ValueError:
							# 		blurred_pil_image = pil_image.convert("RGB").filter(PilImageFilter.BoxBlur(70))
							# 	data = BytesIO()
							# 	blurred_pil_image.save(data, format='png')
							# 	data.seek(0) # yes you actually need this

							# 	almost_blurred = CoreImage(BytesIO(data.read()), ext='png', nocache=True)
							# 	# blurred = Image(size=(window_width, window_height), fit_mode='cover', nocache=True)
							# 	blurred = Image(size=(window_width, window_height), fit_mode='fill', nocache=True)
							# 	blurred.texture = almost_blurred.texture
							# 	parent.add_widget(blurred)

							# 	radial_gradient = RadialGradient(window_width, window_height, (1,1,1,.25), (0,0,0,0.375))
							# 	parent.add_widget(radial_gradient)

							# 	del almost_blurred
							# 	del blurred_pil_image
							# 	del data

							# del pil_image

			# image_widget = Image(texture=image.texture, size_hint=(1.0, 1.0))
			# this mostly works, but it crops things slightly - maybe it's just a resolution thing and when going to 1920/1080 it'll be fixed?
			image_widget = Image(texture=image.texture, fit_mode='contain', nocache=True)

			if orientation:
				align(image_widget, orientation, image.texture.size[0], image.texture.size[1], window_width, window_height)
			
			parent.add_widget(image_widget)

			del image

			if DEBUG:
				parent.add_widget(Label(text=f'{filename}', size_hint=(None, None), size=(200, 50), pos=(10, 10)))

			# if PERFORMANT_MODE:
			# 	widget = parent
			# else:
			# 	# stencil crops the display so it doesn't bleed onto other slides
			# 	stencil = StencilView(size_hint=(1.0, 1.0))
			# 	stencil.add_widget(parent)
			# 	widget = stencil

			stencil = StencilView(size_hint=(1.0, 1.0))
			stencil.add_widget(parent)
			widget = stencil

		return widget

	def apply_config(self):
		self.applying_config = True
		self.clear_widgets()

		self.true_index = 2

		acceptable_extensions = [item for sublist in [
			['.jpg', '.jpeg', '.png'] if CONFIG.get('general', 'display_images') != '0' else [],
			['.mp4'] if CONFIG.get('general', 'display_videos') != '0' else [],
			['.gif'] if CONFIG.get('general', 'display_gifs') != '0' else [],
		] for item in sublist]
		files = [f for f in os.listdir(self.files_dir) if f != '.DS_Store' and f != 'blurred' and os.path.splitext(f)[1] in acceptable_extensions]
		if CONFIG.get('general', 'only_pixel_art') != '0':
			files = [f for f in files if self.file_settings.get(f, {}).get('is_pixel', False)]

		# files = [f for f in files if (self.file_settings.get(f, {}).get('orientation', False) or self.file_settings.get(f, {}).get('background', False)) and f.count('Cortoony_EJy')]

		# print('files:', files)

		shuffle(files)

		self.file_list = files
		self.num_files = len(self.file_list)

		for i, file in enumerate(files):
		# for file in [f for f in os.listdir(files_dir) if f.endswith('.gif')]:
		# for i, file in enumerate(['child0.png', 'child1.png', 'sovanjedi1607959631216709632_1.gif', 'KadaburaDraws1566865598193319938.png']):
			# if (i > 2 and i < len(files) - 2):
			if i > 4:
				# widget = CAROUSEL.placeholder_widget()
				continue
			else:
				widget = self.get_widget_for_file(os.path.join(self.files_dir, file), self.window_width, self.window_height)

			print(file, widget, i)

			self.add_widget(widget)

		enqueue_slide_advance()

		self.index = 2

		self.applying_config = False

	def index_two_right(self, index):
		if index == self.num_files - 2:
			return 0
		elif index == self.num_files - 1:
			return 1
		else:
			return index + 2

	def index_two_left(self, index):
		if index == 0:
			return self.num_files - 2
		elif index == 1:
			return self.num_files - 1
		else:
			return index - 2

	def index_three_right(self):
		if self.index == self.num_files - 3:
			return 0
		elif self.index == self.num_files - 2:
			return 1
		elif self.index == self.num_files - 1:
			return 2
		else:
			return self.index + 3

	def index_three_left(self):
		if self.index == 0:
			return self.num_files - 3
		elif self.index == 1:
			return self.num_files - 2
		elif self.index == 2:
			return self.num_files - 1
		else:
			return self.index - 3

	def placeholder_widget(self):
		return Label(text="placeholder")

	def clear_index(self, index):
		widget_to_remove = self.slides[index]
		self.add_widget(self.get_widget_for_file(os.path.join(self.files_dir, self.file_list[index]), self.window_width, self.window_height), index=index)
		self.remove_widget(widget_to_remove)

	def populate_index(self, index):
		widget_to_remove = self.slides[index]
		self.add_widget(self.placeholder_widget(), index=index)
		self.remove_widget(widget_to_remove)
		

	def on_index(self, instance, value):
		# if self.updating:
		# 	return

		print('new index:', value)
		# print('My property a changed to', value)
		
		# else:
		# 	print("it's not a video")
		super(FileCarousel, self).on_index(instance, value)

		if value == None:
			return

		play_slide_if_video(self.slides[value])
		# if isinstance(self.slides[value], Video):
		# 	# print("it's a video")
		# 	# self.slides[value].position = 0
		# 	if self.slides[value].state != "play":
		# 		self.slides[value].state = "play"
		# 	# self.slides[value].options = {'eos': 'loop'}
		# 	# self.slides[value].allow_stretch = True
		# 	# self.slides[value].loaded = True

		if self.applying_config:
			return

		enqueue_slide_advance()

		if value == 2 or self.num_files <= 5:
			# if value == 2:
			# 	if isinstance(self.slides[value-1], Video):
			# 		# print("it's a video")
			# 		# self.slides[value].position = 0
			# 		if self.slides[value-1].state != "stop":
			# 			self.slides[value-1].state = "stop"
			# 	if isinstance(self.slides[value+1], Video):
			# 		# print("it's a video")
			# 		# self.slides[value].position = 0
			# 		if self.slides[value+1].state != "stop":
			# 			self.slides[value+1].state = "stop"
			return

		def update_widgets(dt):
			if value == 1:
				print('here1')
				self.true_index -= 1
				if self.true_index < 0:
					self.true_index = self.num_files + self.true_index
				deleted_widget = self.slides[4]
				self.remove_widget(self.slides[4])
				print('true index:', self.true_index )
				new_widget = self.get_widget_for_file(os.path.join(self.files_dir, self.file_list[self.index_two_left(self.true_index)]), self.window_width, self.window_height)
				print('new widget:', new_widget)
				# don't ask me why, but -1 adds it to the beginning of the slides
				self.add_widget(new_widget, index=-1)
				if isinstance(deleted_widget, Video):
					deleted_widget.unload()
				else:
					free_stencil(deleted_widget)
				del deleted_widget
			elif value == 3:
				print('here2')
				self.true_index += 1
				if self.true_index >= self.num_files:
					self.true_index -= self.num_files
				print('removing widget:', self.slides[0])
				print('true index:', self.true_index )
				deleted_widget = self.slides[0]
				self.remove_widget(self.slides[0])
				new_widget = self.get_widget_for_file(os.path.join(self.files_dir, self.file_list[self.index_two_right(self.true_index)]), self.window_width, self.window_height)
				print('new widget:', new_widget)
				print('adding at index:', self.true_index + 2)
				# don't ask me why, but zero adds it to the end of the slides
				self.add_widget(new_widget, index=0)
				if isinstance(deleted_widget, Video):
					deleted_widget.unload()
				else:
					free_stencil(deleted_widget)
				del deleted_widget
			# self.index 
			# del deleted_widget
			self.index = 2
			gc.collect()

		Clock.schedule_once(update_widgets, 3)
		# if len(self.slides) > 5:
		# 	index_two_right = self.index_two_right()
		# 	# index_two_left = self.index_two_left()
		# 	# index_three_right = self.index_two_right()
		# 	# index_two_left = self.index_two_left()
		# 	self.updating = True
		# 	if not isinstance(self.slides[index_two_right], Label):
		# 		# proceeded right
		# 		self.clear_index(self.index_three_left())
		# 		self.populate_index(index_two_right)
		# 	else:
		# 		# proceeded left
		# 		self.clear_index(self.index_three_right())
		# 		self.populate_index(self.index_two_left())
		# 	self.updating = False
				
		print(self.slides)


		# print(self.slides)
		# print(value)
		# print(self.index)
		# print(len(self.file_list) - 1)
		# if value != len(self.file_list) - 1:
		# 	self.index = len(self.file_list) - 1

	def current_slide_zoomed(self):
		if PERFORMANT_MODE:
			return False
		return isinstance(self.current_slide, StencilView) and self.current_slide.children[0].scale != 1


	def on_touch_move(self, event, **kwargs):
		# global NAV
		# NAV.visible = not NAV.visible
		# print(NAV)
		print("here")
		global LOCKED
		# if isinstance(self.current_slide, CustomScatterLayout):
		# 	print(self.current_slide.scale)
		if not self.current_slide_zoomed() and not LOCKED:
			super(FileCarousel, self).on_touch_move(event, **kwargs)
			self.is_moving = True

	def on_touch_up(self, event, **kwargs):
		if not self.is_moving and not PERFORMANT_MODE:
			global NAV
			print(NAV.visible)
			# NAV.visible = not NAV.visible
			NAV.toggle_visibility()
			print(NAV.visible)
			print(NAV)
		# if not (isinstance(self.current_slide, CustomScatterLayout) and self.current_slide.scale != 1):
		super(FileCarousel, self).on_touch_up(event, **kwargs)
		self.is_moving = False

	# disable manual scrolling if current child is scatter and zoom is not initial


def kivy_rgba_to_normal_rgba(pixel_color):
	return [pixel_color[0] * 255, pixel_color[1] * 255, pixel_color[2] * 255, pixel_color[3] * 255]

def simple_rgba_to_rgb(pixel_color):
	return [pixel_color[0], pixel_color[1], pixel_color[2]]

def normal_rgb_to_kivy_rgba(pixel_color):
	return [pixel_color[0] / 255.0, pixel_color[1] / 255.0, pixel_color[2] / 255.0, 1]

def euclidean_distance(color_1, color_2):
	return math.sqrt((color_1[0] - color_2[0]) ** 2 + (color_1[1] - color_2[1]) ** 2 + (color_1[2] - color_2[2]) ** 2)

def is_hex(string):
	# Check if the string starts with '#' and is followed by 6 or 8 hexadecimal characters
	if string.startswith('#') and (len(string) == 7 or len(string) == 9):
		return all(c in '0123456789abcdefABCDEF' for c in string[1:])
	return False

def hex_to_color(hex_color):
	# hex_color = hex_color.lstrip('#')
	# return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
	if len(hex_color) == 7:
		return [int(hex_color[1:3], 16) / 255.0, int(hex_color[3:5], 16) / 255.0, int(hex_color[5:7], 16) / 255.0]
	else:
		raise ValueError("Invalid hex color format")

def average_color(color_list):
	r = 0
	g = 0
	b = 0
	num_colors = 0
	for color in color_list:
		r += color[0]
		g += color[1]
		b += color[2]
		num_colors += 1

	return [r / num_colors, g / num_colors, b / num_colors]

def get_background_color(pixels):
	all_same = True
	for pixel in pixels[1:]:
		if pixel != pixels[0]:
			all_same = False
			break

	if all_same:
		return pixels[0]

	cutoff = 0.2
	
	rgb_pixels = [simple_rgba_to_rgb(pixel) for pixel in pixels]

	if len(rgb_pixels) == 2:
		if euclidean_distance(rgb_pixels[0], rgb_pixels[1]) <= cutoff:
			return average_color(rgb_pixels)
	else:
		rgb_1, rgb_2, rgb_3, rgb_4 = rgb_pixels
		if euclidean_distance(rgb_1, rgb_4) <= cutoff and euclidean_distance(rgb_1, rgb_2) <= cutoff and euclidean_distance(rgb_1, rgb_3) <= cutoff and euclidean_distance(rgb_3, rgb_4) <= cutoff:
			return average_color([rgb_1, rgb_2, rgb_3, rgb_4])
	
	return None

# def get_background_color_np(pixel_1, pixel_2, pixel_3, pixel_4):
# 	if pixel_1 == pixel_2 and pixel_1 == pixel_3 and pixel_1 == pixel_4:
# 		# just check this early to avoid extra processing
# 		print('here3')
# 		return pixel_1

# 	# print(pixel_1, pixel_2, pixel_3, pixel_4)
# 	# print(kivy_rgba_to_normal_rgba(pixel_1), kivy_rgba_to_normal_rgba(pixel_2), kivy_rgba_to_normal_rgba(pixel_3), kivy_rgba_to_normal_rgba(pixel_4))
# 	# print(sk_color.rgba2rgb(kivy_rgba_to_normal_rgba(pixel_1)), sk_color.rgba2rgb(kivy_rgba_to_normal_rgba(pixel_2)), sk_color.rgba2rgb(kivy_rgba_to_normal_rgba(pixel_3)), sk_color.rgba2rgb(kivy_rgba_to_normal_rgba(pixel_4)))
# 	# print(sk_color.rgba2rgb(pixel_1), sk_color.rgba2rgb(pixel_2), sk_color.rgba2rgb(pixel_3), sk_color.rgba2rgb(pixel_4))

# 	# lab_1 = sk_color.rgb2lab(sk_color.rgba2rgb(pixel_1))
# 	# lab_2 = sk_color.rgb2lab(sk_color.rgba2rgb(pixel_2))
# 	# lab_3 = sk_color.rgb2lab(sk_color.rgba2rgb(pixel_3))
# 	# lab_4 = sk_color.rgb2lab(sk_color.rgba2rgb(pixel_4))

# 	lab_1 = sk_color.rgb2lab(simple_rgba_to_rgb(pixel_1))
# 	lab_2 = sk_color.rgb2lab(simple_rgba_to_rgb(pixel_2))
# 	lab_3 = sk_color.rgb2lab(simple_rgba_to_rgb(pixel_3))
# 	lab_4 = sk_color.rgb2lab(simple_rgba_to_rgb(pixel_4))

# 	if np.linalg.norm(lab_1 - lab_4) <= 7 and np.linalg.norm(lab_1 - lab_2) <= 7 and np.linalg.norm(lab_1 - lab_3) <= 7 and np.linalg.norm(lab_3 - lab_4) <= 7:
# 		# print(lab_1, lab_2, lab_3, lab_4)
# 		# print(np.array((sk_color.lab2rgb(lab_1), sk_color.lab2rgb(lab_2), sk_color.lab2rgb(lab_3), sk_color.lab2rgb(lab_4))).mean(axis=0))
# 		return np.array((sk_color.lab2rgb(lab_1), sk_color.lab2rgb(lab_2), sk_color.lab2rgb(lab_3), sk_color.lab2rgb(lab_4))).mean(axis=0)
	
# 	return None

def pixel_is_transparent(pixel):
	return len(pixel) == 4 and pixel[3] == 0

def all_pixels_transparent(pixels):
	for pixel in pixels:
		if not pixel_is_transparent(pixel):
			return False
		
	return True

class NavButtons(BoxLayout):
	def __init__(self, **kwargs):
		super(NavButtons, self).__init__(**kwargs)

		def gallery_click(instance):
			# switch to gallery view
			MANAGER.current = 'gallery'

		gallery_button = MDIconButton(
			icon="apps",
			size_hint=(0.33333333, 1), 
			icon_size="100sp"
			# pos_hint={"center_x": 0.5, "center_y": 0.5},
		)
		self.add_widget(gallery_button)
		gallery_button.bind(on_press=gallery_click)

		def lock_click(instance):
			global LOCKED
			if instance.icon == "lock-open-outline":
				print('here10')
				instance.icon = "lock"
				clear_slide_advance()
				clear_reset_zoom()
				print('SLIDE_ADVANCE_EVENT', SLIDE_ADVANCE_EVENT)
				print('RESET_ZOOM_EVENT 3', RESET_ZOOM_EVENT)
				# clear timeouts, lock zooming and carousel proceeding
				LOCKED = True 
			else:
				print('here11')
				instance.icon = "lock-open-outline"
				current_slide = CAROUSEL.current_slide
				LOCKED = False 
				if isinstance(current_slide, StencilView):
					current_slide.children[0].schedule_reset()
					print('RESET_ZOOM_EVENT 2', RESET_ZOOM_EVENT)
				# unlock and set timeouts

		lock_button = MDIconButton(
			icon="lock-open-outline",  # lock when locked
			size_hint=(0.33333333, 1), 
			icon_size="100sp"
			# pos_hint={"center_x": 0.5, "center_y": 0.5},
		)
		self.add_widget(lock_button)
		lock_button.bind(on_press=lock_click)

		def settings_click(instance):
			# switch to settings view
			global CURRENT_SETTINGS
			CURRENT_SETTINGS = copy(CONFIG._sections['general'])
			MANAGER.current = 'settings'

		settings_button = MDIconButton(
			icon="cog",
			size_hint=(0.33333333, 1), 
			icon_size="100sp"
			# pos_hint={"center_x": 0.5, "center_y": 0.5},
		)
		self.add_widget(settings_button)
		settings_button.bind(on_press=settings_click)

class Nav(RelativeLayout):
	def __init__(self, **kwargs):
		super(Nav, self).__init__(**kwargs)
		self.visible = False
		self.size_hint = (1, 0.2)
		# self.disabled = True
		self.orientation = 'horizontal'

		# self.background = Image(color=(0,0,0,0), size_hint=(1, 1))
		self.background = Image(color=(0.8,0.8,0.8,0.5), size_hint=(1, 1))
		self.add_widget(self.background)

		self.add_widget(NavButtons(size_hint=(1, 1)))

		self.pos_hint = {'top': 1.2}

		# NAV.background = nav_background
		# self.pos = (960, 0)
# 		self.kv = Builder.load_string('''
# BoxLayout:
# 	canvas.before:
# 		Color:
# 			rgba: 0.5, 0.5, 0.5, 1
# 		Rectangle:
# 			pos: self.pos
# 			size: self.size
# 		''')

	def toggle_visibility(self):
		self.visible = not self.visible
		print(self.background)
		if self.visible:
			print('here1')
			# self.size_hint_y = 0.2
			# self.size_hint = (1, 0.2)
			# self.pos_hint = {'top': 1}
			# self.background.opacity = 0.5
			# self.background.color = (0.8,0.8,0.8,0.5)
			# self.disabled = False

			anim = Animation(pos_hint={'top': 1}, duration=0.2)
			anim.start(self)

			def toggle_nav(dt):
				if NAV.visible:
					NAV.toggle_visibility()

			global CLOSE_NAV_TIMEOUT
			if CLOSE_NAV_TIMEOUT is not None:
				Clock.unschedule(CLOSE_NAV_TIMEOUT)
			CLOSE_NAV_TIMEOUT = Clock.schedule_once(toggle_nav, 5)
		else:
			print('here2')
			# self.size_hint_y = 0
			# self.size_hint = (1, 0)
			# self.pos_hint = {'top': 1.2}
			# self.background.opacity = 0
			# self.background.color = (0,0,0,0)
			# self.disabled = True

			anim = Animation(pos_hint={'top': 1.2}, duration=0.2)
			anim.start(self)

	# def on_visible(self, instance, value):
	# 	print('changing')
	# 	print(value)
	# 	if value:
	# 		print('here1')
	# 		# self.size_hint_y = 0.2
	# 		self.size_hint = (1, 0.2)
	# 		self.opacity = 0.5
	# 		self.disabled = False
	# 	else:
	# 		print('here2')
	# 		# self.size_hint_y = 0
	# 		self.size_hint = (1, 0)
	# 		self.opacity = 0
	# 		self.disabled = True

# class SettingsInput(BoxLayout):
# 	def __init__(self, **kwargs):
# 		super(SettingsInput, self).__init__(**kwargs)
# 		self.orientation = 'vertical'

# 		def back_click(instance):
# 			# switch to settings view
# 			MANAGER.current = 'carousel'

# 		back_button = MDIconButton(
# 			icon="chevron-left",
# 			size_hint=(0.33333333, 0.1), 
# 			icon_size="100sp"
# 			# pos_hint={"center_x": 0.5, "center_y": 0.5},
# 		)
# 		self.add_widget(back_button)
# 		back_button.bind(on_press=back_click)

class CustomSettings(BoxLayout):
	def __init__(self, **kwargs):
		super(CustomSettings, self).__init__(**kwargs)

		# self.background = Image(color=(1,1,1,1), size_hint=(1, 1))
		# self.add_widget(self.background)

		# self.add_widget(SettingsInput(size_hint=(1, 1)))
		self.orientation = 'vertical'

		# def back_click(instance):
		# 	# switch to settings view
		# 	MANAGER.current = 'carousel'

		# back_button = MDIconButton(
		# 	icon="chevron-left",
		# 	size_hint=(0.33333333, 0.1), 
		# 	icon_size="100sp"
		# 	# pos_hint={"center_x": 0.5, "center_y": 0.5},
		# )
		# self.add_widget(back_button)
		# back_button.bind(on_press=back_click)

		def back_click(instance):
			# switch to settings view
			global CURRENT_SETTINGS
			print(CURRENT_SETTINGS)
			print(CONFIG._sections['general'])
			if CONFIG._sections['general'] != CURRENT_SETTINGS:
				print('here20')
				# reload, and set loading
				CAROUSEL.apply_config()
			MANAGER.current = 'carousel'
			CURRENT_SETTINGS = None

		back_button = MDIconButton(
			icon="chevron-left",
			size_hint=(0.33333333, 0.1), 
			icon_size="100sp"
			# pos_hint={"center_x": 0.5, "center_y": 0.5},
		)
		self.add_widget(back_button)
		back_button.bind(on_press=back_click)

		settings = SettingsWithNoMenu()
		settings.add_json_panel('Settings', CONFIG, 'fanart_settings_info.json')
		self.add_widget(settings)

class Manager(ScreenManager):
	def __init__(self, **kwargs):
		super(Manager, self).__init__(**kwargs)

class MainApp(MDApp):
	def __init__(self, **kwargs):
		super(MainApp, self).__init__(**kwargs)
#         self.kv = Builder.load_string('''
# ScreenManager:
#     Screen:
#         name: "main-menu"
#         Button:
#             text: "Go to next Page!"
#             on_release:
#                 root.transition.direction = "down"
#                 root.current = "song-view"
#     Screen:
#         name: "song-view"
#         RelativeLayout:
#             Video:
#                 source: "art to display/Daydream_Stream1620482802692104203_1.mkv"
#             Button:
#                 text: "Return to main menu!"
#                 size_hint: .25, .25
#                 pos_hint: {"center_x": .5, "center_y": .5}
#                 on_release:
#                     root.transition.direction = "up"
#                     root.current = "main-menu"
# ''')

	def build(self):
		Window.fullscreen = 'auto'
		#monitor_1 = get_monitors()[0]
		# Window.size = (1920, 1080)
		# window_width = 1920.0
		# window_height = 1080.0
		#dpi_multiplier = 2
		#window_width = monitor_1.width * dpi_multiplier
		#window_height = monitor_1.height * dpi_multiplier
		window_width = 1920
		window_height = 1080
		# window_ratio = window_width / window_height
		Window.size = (window_width, window_height)

		layout = WhiteBackgroundLayout()
		layout.add_widget(Image(color=(1,1,1,1), size_hint=(1, 1)))

		# two potential solutons to memory issue -
		# 1) switch to recycle view
		# 2) only fully load close objects in carousel, and leave the rest as placeholders, then load/unload while scrolling

		# acceptable_extensions = [item for sublist in [
		# 	['.jpg', '.jpeg', '.png'] if CONFIG.get('general', 'display_images') else [],
		# 	['.mp4'] if CONFIG.get('general', 'display_videos') else [],
		# 	['.gif'] if CONFIG.get('general', 'display_gifs') else [],
		# ] for item in sublist]
		# files = [f for f in os.listdir(files_dir) if f != '.DS_Store' and os.path.splitext(f)[1] in acceptable_extensions]
		# shuffle(files)

		# files = [f for f in files if f.endswith('.mp4')]
		# files = [f for f in files if f.endswith('.gif')]
		# files = ['SovanJedi1469488665596502020_1.mp4']

		# files = ['child0.png', 'child1.png', 'sovanjedi1607959631216709632_1.gif', 'KadaburaDraws1566865598193319938.png']

		global CAROUSEL
		CAROUSEL = FileCarousel(direction='right', loop=True, files_dir=FILES_DIR, window_width=window_width, settings_file=SETTINGS_FILE, window_height=window_height)
		CAROUSEL.apply_config()

		# for i, file in enumerate(files):
		# # for file in [f for f in os.listdir(files_dir) if f.endswith('.gif')]:
		# # for i, file in enumerate(['child0.png', 'child1.png', 'sovanjedi1607959631216709632_1.gif', 'KadaburaDraws1566865598193319938.png']):
		# 	# if (i > 2 and i < len(files) - 2):
		# 	if i > 4:
		# 		# widget = CAROUSEL.placeholder_widget()
		# 		continue
		# 	else:
		# 		widget = get_widget_for_file(os.path.join(files_dir, file), window_width, window_height)

		# 	print(file, widget, i)

		# 	CAROUSEL.add_widget(widget)

		# enqueue_slide_advance()

		# CAROUSEL.index = 2

		print(CAROUSEL.slides)

		layout.add_widget(CAROUSEL)

		if not PERFORMANT_MODE:
			global NAV
			NAV = Nav()

			layout.add_widget(NAV)

			print(NAV)
			# NAV.toggle_visibility()

		# return layout

		global MANAGER
		MANAGER = Manager()

		carousel_screen = Screen(name="carousel")
		carousel_screen.add_widget(layout)

		# print(CONFIG.__dict__)
		# print(CONFIG._sections['general'])
		# # print(CONFIG._dict)
		# print(CONFIG['general'].__dict__)
		if not PERFORMANT_MODE:
			settings_screen = Screen(name="settings")
			settings_screen.add_widget(CustomSettings())

			gallery_screen = Screen(name="gallery")

		MANAGER.add_widget(carousel_screen)
		if not PERFORMANT_MODE:
			MANAGER.add_widget(settings_screen)
			MANAGER.add_widget(gallery_screen)

		# if DEBUG:
		# 	button = Button(text="Test")
		# 	inspector.create_inspector(Window, button)

		return MANAGER


if __name__ == '__main__':
	MainApp().run()


print("ok")


# child0 or child1 has blurred backgroudn but i think it should have etended background
# 'KadaburaDraws1566865598193319938.png' is small and not expanded - actually a lot of them - mostly fixed
# add settings
# add lock - done?
# add temp lock when interacting (and unzoom) - done i think?
# have minimum zoom and boundaries - think this is working, but need to verify on device
# figure out how to lock debian in kiosk mode - actually, as long as there's no keyboard it's probably fine?
# blurred backgrounds - done; don't like this blur function taht much, maybe cnage it in the future....
# either gifs or videos may not be looping properly
# gallery should definitely use recycle grid
# shoudl clear clocks whne going to settings and gallery
# load new images a bit after the carousel has scrolled to the next image
# gc/ensure that widgets have actually been removed... somehow

# if unlocking on image, unzoom first before proceeding
# reshuffle on returning to start - a bit more complicated here
# might need to make explicit list of blurred background/colored background -or, at least, overrides. or could check if pixels are within some distance of each other.
# long images (scroll through them; also something similar for child0 and child1)
# image align (left/right/up/down/center)
# have gallery view that you can click on to view full screen and start shuffle from there
# keep scroll position in gallery
# i guess... gallery should correspond to current filters?
# and gallery should be for current order, and it'll have a reshuffle button...?
# hm, maybe two views, one alphabetical, one for current sort
# need support for urls
# write a script for formatting files correctly

# settings:
# monitor orientation: landscape xor vertical
# proceed speed
# display images: true xor false
# display gifs: true xor false
# display videos: true xor false
# display long images: true xor false
# display images that are bad for orientation: true xor false (maybe with a cutoff?)
# only pixel art: true xor false
