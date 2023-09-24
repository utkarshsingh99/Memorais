from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
from functools import cmp_to_key
from paddleocr import PaddleOCR
import json
import math
import re

def helper_determine_begin_date(time_of_day, delta=None):
    """Returns an event at specified time of day."""
    # currently uses hardcoded values, in the future would ask for user preferences
    event = Event()
    if (time_of_day=="morning"):
        time = datetime.now().replace(hour=6, minute=0, second=0)
    elif (time_of_day=="afternoon"):
        time = datetime.now().replace(hour=15, minute=0, second=0)
    elif (time_of_day=="evening"):
        time = datetime.now().replace(hour=20, minute=0, second=0)
    elif (time_of_day=="bed"):
        time = datetime.now().replace(hour=22, minute=0, second=0)
    elif (time_of_day=="breakfast"):
        time = datetime.now().replace(hour=8, minute=0, second=0)
    elif (time_of_day=="lunch"):
        time = datetime.now().replace(hour=12, minute=0, second=0)
    elif (time_of_day=="dinner"):
        time = datetime.now().replace(hour=19, minute=0, second=0)
    else:
        time = datetime.now().replace(hour=9, minute=0, second=0) # default is 9 am
        print("Using default time of day for this event.")
    if delta:
        time = time+delta
    event.add("dtstart", time)
    event.add("dtend", time)
    return event

# ------------------------------------------------------------------------------------------------------------------------------

ocr = PaddleOCR(use_angle_cls=True, lang='en') # need to run only once to download and load model into memory

# Compare bounding boxes
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

def map_numbers(label):
  label = label.replace(' one ',' 1 ')
  label = label.replace(' two ',' 2 ')
  label = label.replace(' three ',' 3 ')
  label = label.replace(' four ',' 4 ')
  label = label.replace(' five ',' 5 ')
  label = label.replace(' six ',' 6 ')
  label = label.replace(' seven ',' 7 ')
  label = label.replace(' eight ',' 8 ')
  label = label.replace(' nine ',' 9 ')
  return label

def surround_numbers_with_spaces(label):
  # Define a regular expression pattern to match numbers
  pattern = r'\d+'
  # Use re.sub to replace all matches of the pattern with spaces around them
  result = re.sub(pattern, lambda match: f' {match.group()} ', label)
  result = ' '.join(result.split())
  return result

def preprocess_label(texts):
  label_text = ' '.join(texts)
  label_text = label_text.lower()
  label_text = map_numbers(label_text)
  label_text = surround_numbers_with_spaces(label_text)
  return label_text

frequency_indicator = [
    { "regex": r"every ([0-9]+) hours", "frequency_unit": "hours" },
    { "regex": r"every meal", "frequency": 1, "frequency_unit": "daily", "time_of_days": ["breakfast", "lunch", "dinner"] },
    { "regex": r"every night", "frequency": 1, "frequency_unit": "days", "time_of_days": ["evening"] },
    { "regex": r"every day", "frequency": 1, "frequency_unit": "days" },
    { "regex": r"every other day", "frequency": 0.5, "frequency_unit": "days" },
    { "regex": r"every week", "frequency": 1, "frequency_unit": "weeks" },
    { "regex": r"every ([0-9]+) weeks", "frequency_unit": "weeks" },
    { "regex": r"([0-9]+) times a day", "frequency_unit": "days" },
    { "regex": r"([0-9]+) times daily", "frequency_unit": "days" },
    { "regex": r"([0-9]+) x a day", "frequency_unit": "days" },
    { "regex": r"([0-9]+) x daily", "frequency_unit": "days" },
    { "regex": r"([0-9]+) to ([0-9]+) times a day", "frequency_unit": "days" },
    { "regex": r"([0-9]+) to ([0-9]+) times daily", "frequency_unit": "days" },
    { "regex": r"([0-9]+) x to ([0-9]+) x a day", "frequency_unit": "days" },
    { "regex": r"([0-9]+) x to ([0-9]+) x daily", "frequency_unit": "days" },
    { "regex": r"twice a day", "frequency": 2, "frequency_unit": "days" },
    { "regex": r"twice per day", "frequency": 2, "frequency_unit": "days" },
    { "regex": r"twice daily", "frequency": 2, "frequency_unit": "days" },
    { "regex": r"once daily", "frequency": 1, "frequency_unit": "days" },
    { "regex": r"daily", "frequency": 1, "frequency_unit": "days" }
]

duration_indicator = [
    { "regex": r"for ([0-9]+) days", "duration_unit": "days" },
    { "regex": r"after ([0-9]+) days", "duration_unit": "days" },
    { "regex": r"x ([0-9]+) days", "duration_unit": "days" },
    { "regex": r"for ([0-9]+) weeks", "duration_unit": "weeks" },
    { "regex": r"after ([0-9]+) weeks", "duration_unit": "weeks" },
    { "regex": r"x ([0-9]+) weeks", "duration_unit": "weeks" },
    { "regex": r"for ([0-9]+) months", "duration_unit": "months" },
    { "regex": r"after ([0-9]+) months", "duration_unit": "months" },
    { "regex": r"x ([0-9]+) months", "duration_unit": "months" },
]

with_meals_indicator = [
    { "regex": r"with meals"},
    { "regex": r"w meals" },
    { "regex": r"w/ meals" }
]

# ------------------------------------------------------------------------------------------------------------------------------

def analyze_img(path):
  print("Moment of truth...")
  # img: img for OCR, support ndarray, img_path and list or ndarray
  ocr_result = ocr.ocr(path, cls=True)[0]
  print("OCR success!")
  sorted_result = sorted(ocr_result, key=cmp_to_key(compare_coord))
  
  texts = []
  for pred in sorted_result:
    texts.append(pred[1][0])

  label_text = preprocess_label(texts)

  time_of_days = None
  frequency = None
  frequency_unit = None
  duration = None
  duration_unit = None
  time_of_days = None
  medication_name = ""
  method = ""

  for freq_ind in frequency_indicator:
    match = re.search(freq_ind["regex"], label_text)
    if match:
      print('Matched!', str(freq_ind))
      if "frequency" not in freq_ind.keys():
        frequency = int(match.group(1))
      else:
        frequency = freq_ind["frequency"]
      if "time_of_days" in freq_ind:
        time_of_days = freq_ind["time_of_days"]
      frequency_unit = freq_ind['frequency_unit']
      break

  for dur_ind in duration_indicator:
    match = re.search(dur_ind["regex"], label_text)
    if match:
      print('Matched!', str(dur_ind))
      if match.group(1):
        duration = int(match.group(1))
      duration_unit = dur_ind['duration_unit']
      break

  for wm_ind in with_meals_indicator:
    match = re.search(wm_ind["regex"], label_text)
    if match:
      print('Matched!', str(wm_ind))
      if frequency == 1:
        time_of_days = ["breakfast"]
        frequency = 1
        frequency_unit = "days"
      elif frequency == 2:
        time_of_days = ["breakfast", "dinner"]
        frequency = 1
        frequency_unit = "days"
      elif frequency == 3:
        time_of_days = ["breakfast", "lunch", "dinner"]
        frequency = 1
        frequency_unit = "days"
      break

  input_json = {
    "frequency": frequency,
    "frequency_unit": frequency_unit,
    "duration": duration,
    "duration_unit": duration_unit,
    "time_of_days": time_of_days,
    "medication_name": medication_name,
    "method": method
  }

  # Create an ICS calendar
  cal = Calendar()
  events = []

  # Extract input values from JSON
  medication_name = input_json["medication_name"] or "" # string
  duration = input_json["duration"] or -1 # int
  duration_unit = input_json["duration_unit"] or "" # string
  frequency = input_json["frequency"] or 1 # either an int or a dict with two ints. see google doc.
  frequency_unit = input_json["frequency_unit"] or "days" # string
  time_of_days = input_json["time_of_days"] or ["morning"] # string
  method = input_json["method"] or "" # string

  rrule = None # event property for repetition (sets how frequent as well as when it stops repeating)
  if (frequency_unit=="hours"): # user takes med on a hourly basis
      rrule = {"freq": "daily", "interval": 1} # if you take a med on an hourly basis, you take it on a daily basis
      if (duration != -1):
          if (duration_unit=="days"):
              rrule["count"] = math.floor(duration / rrule["interval"])
          elif (duration_unit=="weeks"):
              rrule["count"] = math.floor(duration * 7 / rrule["interval"])
          elif (duration_unit=="months"):
              rrule["count"] = math.floor(duration * 30 / rrule["interval"])
          else:
              raise Exception(f"Invalid duration unit: {duration_unit}")
      every = frequency["every"]
      for i in range(frequency["count"]):
          events.append(helper_determine_begin_date(time_of_days[0], timedelta(hours=i*every)))
  elif (frequency_unit=="days"): # user takes med on a daily basis (may be several times per day)
      rrule = {"freq": "daily", "interval": math.floor(1/frequency)}
      if (frequency > 1): # this is an edge case
          rrule["interval"] = 1
          print("The preference for a medication that you take several times daily is to supply multiple values in the time_of_days array.")
          if (frequency==2):
              time_of_days = ["morning", "evening"]
          elif (frequency==3):
              time_of_days = ["morning", "afternoon", "evening"]
          elif (frequency==4):
              time_of_days = ["morning", "lunch", "afternoon", "evening"]
          elif (frequency==5):
              time_of_days = ["morning", "lunch", "afternoon", "dinner", "bed"]
          elif (frequency==6):
              time_of_days = ["morning", "lunch", "afternoon", "dinner", "evening", "bed"]
          elif (frequency==7):
              time_of_days = ["morning", "breakfast", "lunch", "afternoon", "dinner", "evening", "bed"]
          else:
              raise Exception("Cannot handle a frequency of more than 7 times daily.")
      if (duration != -1):
          if (duration_unit=="days"):
              rrule["count"] = math.floor(duration / rrule["interval"])
          elif (duration_unit=="weeks"):
              rrule["count"] = math.floor(duration * 7 / rrule["interval"])
          elif (duration_unit=="months"):
              rrule["count"] = math.floor(duration * 30 / rrule["interval"])
          else:
              raise Exception(f"Invalid duration unit: {duration_unit}")
      for time_of_day in time_of_days:
          events.append(helper_determine_begin_date(time_of_day))
  elif (frequency_unit=="weeks"): # user takes med on a monthly basis
      current_day_of_week = datetime.now().strftime("%a").upper()[:2] # get the abbreviation of the weekday
      rrule = {"freq": "weekly", "interval": frequency, "byday": current_day_of_week}
      if (duration!=-1):
          if (duration_unit=="weeks"):
              rrule["count"] = math.floor(duration / rrule["interval"])
          elif (duration_unit=="months"):
              rrule["count"] = math.floor(duration * (365.25/12/7) / rrule["interval"]) # 365.25/12/7 = avg amount of weeks per month
          elif (duration_unit=="days"):
              raise Exception("Days is an invalid duration unit for an event that repeats on a weekly basis")
          else:
              raise Exception(f"Invalid duration unit: {duration_unit}")
      events.append(helper_determine_begin_date(time_of_days[0])) # we assume that if you take a med on a weekly basis, you only take it once that day
  else:
      raise Exception(f"Invalid frequency unit: {frequency_unit}.")

  for event in events:
      event.add("summary", "Medication Reminder!" if medication_name == "" else f"Medication Reminder: {medication_name.title()}")
      event.add("description", method)
      if rrule:
          event.add('rrule', rrule)
      alert = Alarm()
      alert.add('action', 'DISPLAY')
      alert.add('description', f'Medication Reminder: {medication_name}')  # Alert message
      alert.add('trigger', timedelta(0))  # Alert 1 minute before
      event.add_component(alert)
      cal.add_component(event)
  return cal

image = "./example_bottle.jpg"
print(analyze_img(image))

def analyze_test_img():
    result = analyze_img(image)
    return result