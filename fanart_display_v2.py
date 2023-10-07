# from kivy import * 
from copy import copy
import gc
import math
import os
from io import BytesIO
from random import shuffle

#os.environ['KIVY_IMAGE'] = 'pil'

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
# from skimage import color as sk_color
# import numpy as np
from screeninfo import get_monitors

#ImageFile.LOAD_TRUNCATED_IMAGES = True

MANAGER = None
CAROUSEL = None
NAV = None
SLIDE_DURATION = 10
SLIDE_ADVANCE_EVENT = None
RESET_ZOOM_EVENT = None
CLOSE_NAV_TIMEOUT = None
LOCKED = False

CURRENT_SETTINGS = None

PIXEL_FILES = ['MakDeetsMuch1645881808448536576.png', 'child0.png', 'child1.png', 'KadaburaDraws1566865598193319938.png']

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


def advance_carousel(dt):
	global CAROUSEL
	if isinstance(CAROUSEL.next_slide, Video):
		CAROUSEL.next_slide.state = "play"
	CAROUSEL.load_next()

	# global SLIDE_ADVANCE_EVENT
	# SLIDE_ADVANCE_EVENT = Clock.schedule_once(advance_carousel, SLIDE_DURATION)

def clear_slide_advance():
	global SLIDE_ADVANCE_EVENT
	if SLIDE_ADVANCE_EVENT is not None:
		Clock.unschedule(SLIDE_ADVANCE_EVENT)
		SLIDE_ADVANCE_EVENT = None

def enqueue_slide_advance(duration=SLIDE_DURATION):
	global SLIDE_ADVANCE_EVENT
	if SLIDE_ADVANCE_EVENT is not None:
		Clock.unschedule(SLIDE_ADVANCE_EVENT)
	SLIDE_ADVANCE_EVENT = Clock.schedule_once(advance_carousel, duration)

def clear_reset_zoom():
	global RESET_ZOOM_EVENT
	if RESET_ZOOM_EVENT is not None:
		Clock.unschedule(RESET_ZOOM_EVENT)
		RESET_ZOOM_EVENT = None

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
			anim = Animation(scale=1, duration=SLIDE_DURATION / 4) & Animation(x=0, duration=SLIDE_DURATION / 4) & Animation(y=0, duration=SLIDE_DURATION / 4)
			anim.start(self)
			enqueue_slide_advance(SLIDE_DURATION / 2)

		global RESET_ZOOM_EVENT
		RESET_ZOOM_EVENT = Clock.schedule_once(reset_zoom, SLIDE_DURATION / 2)
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
	def __init__(self, files_dir, window_width, window_height, **kwargs):
		super(FileCarousel, self).__init__(**kwargs)
		# self.file_list = file_list
		# self.num_files = len(file_list)
		self.files_dir = files_dir
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

	def apply_config(self):
		self.applying_config = True
		self.clear_widgets()

		self.true_index = 2

		acceptable_extensions = [item for sublist in [
			['.jpg', '.jpeg', '.png'] if CONFIG.get('general', 'display_images') != '0' else [],
			['.mp4'] if CONFIG.get('general', 'display_videos') != '0' else [],
			['.gif'] if CONFIG.get('general', 'display_gifs') != '0' else [],
		] for item in sublist]
		files = [f for f in os.listdir(self.files_dir) if f != '.DS_Store' and os.path.splitext(f)[1] in acceptable_extensions]
		if CONFIG.get('general', 'only_pixel_art') != '0':
			files = [f for f in files if f in PIXEL_FILES]
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
				widget = get_widget_for_file(os.path.join(self.files_dir, file), self.window_width, self.window_height)

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
		self.add_widget(get_widget_for_file(os.path.join(self.files_dir, self.file_list[index]), self.window_width, self.window_height), index=index)
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

		if isinstance(self.slides[value], Video):
			# print("it's a video")
			# self.slides[value].position = 0
			if self.slides[value].state != "play":
				self.slides[value].state = "play"
			# self.slides[value].options = {'eos': 'loop'}
			# self.slides[value].allow_stretch = True
			# self.slides[value].loaded = True

		if self.applying_config:
			return

		enqueue_slide_advance()

		if value == 2 or self.num_files <= 5:
			return

		def update_widgets(dt):
			if value == 1:
				print('here1')
				self.true_index -= 1
				if self.true_index < 0:
					self.true_index = self.num_files + self.true_index
				self.remove_widget(self.slides[4])
				print('true index:', self.true_index )
				new_widget = get_widget_for_file(os.path.join(self.files_dir, self.file_list[self.index_two_left(self.true_index)]), self.window_width, self.window_height)
				print('new widget:', new_widget)
				# don't ask me why, but -1 adds it to the beginning of the slides
				self.add_widget(new_widget, index=-1)
			elif value == 3:
				print('here2')
				self.true_index += 1
				if self.true_index >= self.num_files:
					self.true_index -= self.num_files
				print('removing widget:', self.slides[0])
				print('true index:', self.true_index )
				self.remove_widget(self.slides[0])
				new_widget = get_widget_for_file(os.path.join(self.files_dir, self.file_list[self.index_two_right(self.true_index)]), self.window_width, self.window_height)
				print('new widget:', new_widget)
				print('adding at index:', self.true_index + 2)
				# don't ask me why, but zero adds it to the end of the slides
				self.add_widget(new_widget, index=0)
			# self.index 
			self.index = 2
			gc.collect()

		Clock.schedule_once(update_widgets, 1)
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
		if not self.is_moving:
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

def get_background_color(pixel_1, pixel_2, pixel_3, pixel_4):
	if pixel_1 == pixel_2 and pixel_1 == pixel_3 and pixel_1 == pixel_4:
		# just check this early to avoid extra processing
		print('here3')
		return pixel_1

	cutoff = 0.2

	rgb_1 = simple_rgba_to_rgb(pixel_1)
	rgb_2 = simple_rgba_to_rgb(pixel_2)
	rgb_3 = simple_rgba_to_rgb(pixel_3)
	rgb_4 = simple_rgba_to_rgb(pixel_4)

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

def get_widget_for_file(filepath, window_width, window_height):
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
	elif ext == '.gif':
		anim_delay = 0.04 if filename in ['cannonbreed1576816909458149376_1.gif', 'cannonbreed1603175701049327616_1.gif'] else 0.1
		widget = Image(source=filepath, fit_mode='contain', anim_delay=anim_delay)
	else:
		if filename in PIXEL_FILES:
			image = CoreImage(filepath, keep_data=True, nocache=True)
			image.texture.mag_filter = 'nearest'
		else:
			image = CoreImage(filepath, keep_data=True, nocache=True)
		scatter = CustomScatterLayout(do_rotation=False, scale_min=1)
		scatter.size = (window_width, window_height)

		pixel_1 = image.read_pixel(0, 0)
		pixel_2 = image.read_pixel(0, image.texture.size[1] - 1)
		pixel_3 = image.read_pixel(image.texture.size[0] - 1, 0)
		pixel_4 = image.read_pixel(image.texture.size[0] - 1, image.texture.size[1] - 1)

		print(pixel_1, pixel_2, pixel_3, pixel_4)

		if not (pixel_is_transparent(pixel_1) and pixel_is_transparent(pixel_2) and pixel_is_transparent(pixel_3) and pixel_is_transparent(pixel_4)):
			# image does not have transparent edges, so apply a backgorund
			background_color = get_background_color(pixel_1, pixel_2, pixel_3, pixel_4)
			if background_color is not None:
				scatter.add_widget(Image(color=background_color, size_hint=(1.0, 1.0)))
			else:
				# blur the image as the background
				with PilImage.open(filepath) as pil_image:
					try:
						blurred_pil_image = pil_image.filter(PilImageFilter.BoxBlur(50))
					except ValueError:
						blurred_pil_image = pil_image.convert("RGB").filter(PilImageFilter.BoxBlur(50))
					data = BytesIO()
					blurred_pil_image.save(data, format='png')
					data.seek(0) # yes you actually need this

					almost_blurred = CoreImage(BytesIO(data.read()), ext='png', nocache=True)
					blurred = Image(size=(window_width, window_height), fit_mode='cover')
					blurred.texture = almost_blurred.texture
					scatter.add_widget(blurred)

					radial_gradient = RadialGradient(window_width, window_height, (1,1,1,.25), (0,0,0,0.375))
					scatter.add_widget(radial_gradient)

		# image_widget = Image(texture=image.texture, size_hint=(1.0, 1.0))
		# this mostly works, but it crops things slightly - maybe it's just a resolution thing and when going to 1920/1080 it'll be fixed?
		image_widget = Image(texture=image.texture, fit_mode='contain')
		scatter.add_widget(image_widget)

		# stencil crops the display so it doesn't bleed onto other slides
		stencil = StencilView(size_hint=(1.0, 1.0))
		stencil.add_widget(scatter)
		widget = stencil

	return widget

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
		window_ratio = window_width / window_height
		Window.size = (window_width, window_height)

		layout = WhiteBackgroundLayout()
		layout.add_widget(Image(color=(1,1,1,1), size_hint=(1, 1)))

		# two potential solutons to memory issue -
		# 1) switch to recycle view
		# 2) only fully load close objects in carousel, and leave the rest as placeholders, then load/unload while scrolling

		files_dir = '../fanart'

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
		CAROUSEL = FileCarousel(direction='right', loop=True, files_dir=files_dir, window_width=window_width, window_height=window_height)
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
		settings_screen = Screen(name="settings")
		settings_screen.add_widget(CustomSettings())

		gallery_screen = Screen(name="gallery")

		MANAGER.add_widget(carousel_screen)
		MANAGER.add_widget(settings_screen)
		MANAGER.add_widget(gallery_screen)

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
