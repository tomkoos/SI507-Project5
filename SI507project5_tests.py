import unittest
from SI507project5_code import *

class Test_caching(unittest.TestCase):
  def setUp(self):
    self.cache_file = open("cache_contents.json", encoding='utf-8-sig')

  def test_cache_file(self):
    read = self.cache_file.read()
    self.assertTrue(read)
    self.assertIsInstance(read, str)
    cache_diction = json.loads(read)
    self.assertIsInstance(cache_diction, dict)

  def tearDown(self):
    self.cache_file.close()

class Test_Event(unittest.TestCase):
  def setUp(self):
    self.cache_file = open("cache_contents.json", encoding='utf-8-sig')
    self.cache_json = json.loads(self.cache_file.read())
    self.url = "https://www.eventbriteapi.com/v3/events/search/"
    self.params_diction = {"sort_by": "date",                  
                           "start_date.keyword": "this_month",
                           "location.address": "Ann Arbor",
                           "location.within": "1mi",
                           "expand": "category,organizer,venue",
                           "price": "free",
                           "page": "1"}

  def test_init_from_cache(self):
    identifier = create_request_identifier(self.url, self.params_diction)
    # select the first event of the list
    event_diction = self.cache_json[identifier]['values']['events'][0]
    test_event = Event(event_diction)
    self.assertEqual(test_event.name,
                       "Free Course on Python for Machine Learning - Live "
                       "Instructor-led Classes | Certification & Projects "
                       "Included | Limited Seats | Ann Arbor, MI")
    self.assertEqual(test_event.category, "Science & Technology")
    self.assertIsInstance(test_event.start_date_local, datetime)
    self.assertIsInstance(test_event.end_date_local, datetime)
    self.assertIsInstance(test_event.description, str)
    self.assertEqual(test_event.organizer_name, "CloudxLab")
    self.assertEqual(test_event.venue_name, "Ann Arbor")
    self.assertEqual(test_event.venue_address, "Ann Arbor, MI")
    self.assertEqual(test_event.url,
                       "https://www.eventbrite.com/e/free-course-on-python-for"
                       "-machine-learning-live-instructor-led-classes"
                       "-certification-projects-tickets-39360957684?aff=ebapi")
  def tearDown(self):
    self.cache_file.close()

class Test_csv(unittest.TestCase):
  def setUp(self):
    self.free_file = open("Eventbrite_Free_AnnArbor.csv", encoding='utf-8-sig')
    self.paid_file = open("Eventbrite_Free_AnnArbor.csv", encoding='utf-8-sig')
  
  def test_csv_files(self):
    self.assertTrue(self.free_file.read())
    self.assertTrue(self.paid_file.read())

  def tearDown(self):
    self.free_file.close()
    self.paid_file.close()

if __name__ == "__main__":
  unittest.main(verbosity=2)
