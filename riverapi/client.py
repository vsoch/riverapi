__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "MPL 2.0"

from riverapi.logger import logger
import riverapi.defaults as defaults

import json
import dill
import requests


class Client:
    """
    Interact with a River Server
    """

    def __init__(self, baseurl=None, quiet=False):
        self.baseurl = (baseurl or defaults.baseurl).strip("/")
        self.quiet = quiet
        self.flavors = ["regression", "binary", "multiclass"]

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[riverapi-client]"

    def check_flavor(self, flavor):
        """
        Verify that the flavor is known
        """
        if flavor not in self.flavors:
            logger.exit(
                "%s is not a valid flavor. Choices are: %s"
                % (flavor, " ".join(self.flavors))
            )

    def check_response(self, r):
        """
        Ensure the response status code is 20x
        """
        if r.status_code not in [200, 201]:
            logger.exit("Unsuccessful response: %s, %s" % r.status_code, r.reason)

    def print_response(self, r):
        """
        Print the result of a response
        """
        response = r.json()
        logger.info("%s: %s" % (r.url, json.dumps(response, indent=4)))

    def do_request(
        self, typ, url, data=None, json=None, headers=None, return_json=True
    ):
        if not self.quiet:
            logger.info("%s %s" % (typ.uppercase(), url))

        # The first post when you upload the model defines the flavor (regression)
        if json:
            r = requests.request(typ, self.baseurl + url, json=json, headers=headers)
        else:
            r = requests.request(typ, self.baseurl + url, data=data, headers=headers)
        if not self.quiet:
            self.print_response(r)
        self.check_response(r)

        # All data is typically json
        if return_json:
            return r.json()
        return r

    def post(self, url, data=None, json=None, headers=None, return_json=True):
        return self.do_request(
            "post", url, data=data, json=json, headers=headers, return_json=return_json
        )

    def get(self, url, data=None, json=None, headers=None, return_json=True):
        return self.do_request(
            "get", url, data=data, json=json, headers=headers, return_json=return_json
        )

    def upload_model(self, model, flavor):
        """
        Given a model / pipeline, upload to an online-ml server.

        model = preprocessing.StandardScaler() | linear_model.LinearRegression()
        """
        self.check_flavor(flavor)
        r = self.post("/api/model/%s/" % flavor, data=dill.dumps(model))
        model_name = r["name"]
        logger.info("Created model %s" % model_name)
        return model_name

    def train(self, model_name, x, y=None):
        """
        Train on some data. You are required to provide at least the model
        name known to the server and x (data).

        for x, y in datasets.TrumpApproval().take(100):
            cli.train(x, y)
        """
        return self.post(
            "/api/learn/", json={"model": model_name, "features": x, "ground_truth": y}
        )

    def get_model_json(self, model_name):
        """
        Get a json respresentation of a model.
        """
        return self.get("/api/model/%s/" % model_name)

    def download_model(self, model_name, dest=None):
        """
        Download a model to file (e.g., pickle)

        with open("muffled-pancake-9439.pkl", "rb") as fd:
            content=pickle.load(fd)
        """
        # Get the model (this is a download of the pickled model with dill)
        r = self.get("/api/model/download/%s/" % model_name, return_json=False)

        # Default to pickle in PWD
        dest = dest or "%s.pkg" % model_name

        # Save to dest file
        with open(dest, "wb") as f:
            for chunk in r:
                f.write(chunk)
        return dest

    def predict(self, model_name, x, y):
        """
        Make a prediction
        """
        return self.post("/api/predict/", json={"model": model_name, "features": x})

    def models(self):
        return self.get("/api/models/")

    # TODO need to add streaming events/other endpoints and authentication
