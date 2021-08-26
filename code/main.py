""" Main Script of the application. Manages the main components of the tool. """

# ## Imports
from information_extraction import extract
from classification import classify
from training import initialize_model

""" # ## Initiate Logging-Module
logging.basicConfig(
    format='%(asctime)s : %(threadName)s : %(levelname)s : %(message)s',
    level=logging.DEBUG, filename='logger.log', filemode='w+',
) """

# STEP 1: Train or Load Vectorizer and KNN as Class-object model
model = initialize_model()


# STEP 2: Start Classification
classify(model)

# STEP 3a: Information Extraction
# TODO Parameter as option tool or competences
extract()
# STEP 3b: Matching 




