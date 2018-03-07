from moabb.evaluations import WithinSessionEvaluation
from moabb.paradigms.motor_imagery import LeftRightImagery
from pyriemann.estimation import Covariances
from pyriemann.spatialfilters import CSP
from pyriemann.classification import TSclassifier
from sklearn.pipeline import make_pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.svm import SVC

from collections import OrderedDict
from moabb.datasets import utils
from moabb.viz import analyze

import mne
mne.set_log_level(False)

datasets = utils.dataset_search('imagery', events=['right_hand', 'left_hand'],
                                has_all_events=True, min_subjects=2,
                                multi_session=False)

pipelines = OrderedDict()
pipelines['TS'] = make_pipeline(Covariances('oas'), TSclassifier())
pipelines['CSP+LDA'] = make_pipeline(Covariances('oas'), CSP(8), LDA())
pipelines['CSP+SVM'] = make_pipeline(Covariances('oas'), CSP(8), SVC())  #

context = LeftRightImagery(pipelines, WithinSessionEvaluation(), datasets)

results = context.process()

analyze(results, './')
