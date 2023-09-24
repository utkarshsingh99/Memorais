from flask import Blueprint, request
from flask import current_app as app
from main.auth import token_required
from main.user.models import User
from paddleocr import PaddleOCR
from functools import cmp_to_key
import time

# Paddleocr supports Chinese, English, French, German, Korean and Japanese.
# You can set the parameter `lang` as `ch`, `en`, `french`, `german`, `korean`, `japan`
# to switch the language model in order.

user_blueprint = Blueprint("user", __name__)

@user_blueprint.route("/", methods=["GET"])
@token_required
def get():
	return User().get()

@user_blueprint.route("/auth/", methods=["GET"])
def getAuth():
	return User().getAuth()

@user_blueprint.route("/login/", methods=["POST"])
def login():
	return User().login()

@user_blueprint.route("/logout/", methods=["GET"])
def logout():
	return User().logout()

@user_blueprint.route("/", methods=["POST"])
def add():
	return User().add()

ocr = PaddleOCR(use_angle_cls=True, lang='en')

def compare_coord(item1, item2):
  item1_coords = item1[0][0]
  item2_coords = item2[0][0]

  if item1_coords[1] < item2_coords[1]:
    return -1
  elif item1_coords[1] > item2_coords[1]:
      return 1
  else:
      if item1_coords[0] < item2_coords[0]:
          return 1
      else:
          return -1

@user_blueprint.route('/img-upload', methods=["POST"])
@token_required
def upload():
	user = User().get()

	f = request.files['file']
	f.save('photos/' + f.filename)
	start_time = time.time()

	for img in images:
		result = ocr.ocr(img, cls=True)[0]
	# texts = []
	# for res in result:
		print(result)
		# for pred in res:
		# texts.append(pred[1][0])
	# print(str(texts))
	# print("\n\n################\n\n")

	sorted_result = sorted(result, key=cmp_to_key(compare_coord))
	print(sorted_result)

	print("--- %s seconds ---" % (time.time() - start_time))
	return sorted_result
