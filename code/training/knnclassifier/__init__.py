""" Init-Script for knn-training."""

# ## Imports
from scipy.sparse.csr import csr_matrix
from . import gen_knn
from sklearn.neighbors import KNeighborsClassifier 

# ## Function
def start_knn(tfidf_train: csr_matrix, all_classes: list) -> KNeighborsClassifier:
    # Call KNN-Training function
    clf = gen_knn.initialize_knn(tfidf_train, all_classes)
    return clf