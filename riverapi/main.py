__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "MPL 2.0"

from riverapi.logger import logger
from riverapi.auth import parse_auth_header
import riverapi.defaults as defaults

from copy import deepcopy

import base64
import os
import json
import dill
import requests


class Client:
    """
    Interact with a River Server
    """

    def __init__(self, baseurl=None, quiet=False, prefix="api"):
        self.baseurl = (baseurl or defaults.baseurl).strip("/")
        self.quiet = quiet
        self.flavors = ["regression", "binary", "multiclass", "cluster", "custom"]
        self.session = requests.session()
        self.headers = {"Accept": "application/json", "User-Agent": "riverapi-python"}
        self.prefix = prefix
        self.getenv()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[riverapi-client]"

    @property
    def apiroot(self):
        """
        Combine the baseurl and prefix to get the complete root.
        """
        return self.baseurl + "/" + self.prefix.strip("/")

    def check(self):
        """
        The user can run check to perform a service info, and update the
        prefix or baseurl if the server provides different ones.
        """
        info = self.info()
        for field in ["prefix", "baseurl"]:
            if field in info:
                updated = info[field].strip("/")
                print("Updating %s to %s" % (field, updated))
                setattr(self, field, updated)

    def getenv(self):
        """
        Get any token / username set in the environment
        """
        self.token = os.environ.get("RIVER_ML_TOKEN")
        self.user = os.environ.get("RIVER_ML_USER")

    def check_flavor(self, flavor):
        """
        Verify that the flavor is known
        """
        if flavor not in self.flavors:
            logger.exit(
                "%s is not a valid flavor. Choices are: %s"
                % (flavor, " ".join(self.flavors))
            )

    def check_response(self, typ, r, return_json=True, stream=False, retry=True):
        """
        Ensure the response status code is 20x
        """
        if r.status_code == 401 and retry:
            if self.authenticate_request(r):
                r.request.headers.update(self.headers)
                r = self.session.send(r.request)

                # Call itself once more just to check the status code
                return self.check_response(typ, r, return_json, stream, retry=False)

        if r.status_code not in [200, 201]:
            logger.exit("Unsuccessful response: %s, %s" % (r.status_code, r.reason))

        # All data is typically json
        if return_json and not stream:
            return r.json()
        return r

    def set_basic_auth(self, username, password):
        """
        A wrapper to adding basic authentication to the Request
        """
        auth_str = "%s:%s" % (username, password)
        auth_header = base64.b64encode(auth_str.encode("utf-8"))
        self.set_header("Authorization", "Basic %s" % auth_header.decode("utf-8"))

    def set_header(self, name, value):
        """
        Set a header, name and value pair
        """
        self.headers.update({name: value})

    def authenticate_request(self, originalResponse):
        """
        Authenticate the request.

        Given a response (an HTTPError 401), look for a Www-Authenticate
        header to parse. We return True/False to indicate if the request
        should be retried.
        """
        authHeaderRaw = originalResponse.headers.get("Www-Authenticate")
        if not authHeaderRaw:
            return False

        # If we have a username and password, set basic auth automatically
        if self.token and self.user:
            self.set_basic_auth(self.user, self.token)

        headers = deepcopy(self.headers)
        if "Authorization" not in headers:
            logger.exit(
                "This endpoint requires a token. Please export RIVER_ML_TOKEN and RIVER_ML_USER first."
            )
            return False

        # Prepare request to retry
        h = parse_auth_header(authHeaderRaw)
        headers.update(
            {
                "service": h.Service,
                "Accept": "application/json",
                "User-Agent": "riverapi-python",
            }
        )

        # Currently we don't set a scope (it defaults to build)
        try:
            authResponse = requests.get(h.Realm, headers=headers).json()
        except:
            logger.exit("Failed to get token from %s" % h.Realm)

        # Request the token
        token = authResponse.get("token")
        if not token:
            return False

        # Set the token to the original request and retry
        self.headers.update({"Authorization": "Bearer %s" % token})
        return True

    def print_response(self, r):
        """
        Print the result of a response
        """
        response = r.json()
        logger.info("%s: %s" % (r.url, json.dumps(response, indent=4)))

    def info(self):
        """
        Get basic server information
        """
        return self.get("/")

    def do_request(
        self,
        typ,
        url,
        data=None,
        json=None,
        headers=None,
        return_json=True,
        stream=False,
    ):
        """
        Do a request (get, post, etc)
        """
        # If we have a cached token, use it!
        headers = headers or {}
        headers.update(self.headers)

        if not self.quiet:
            logger.info("%s %s" % (typ.upper(), url))

        # The first post when you upload the model defines the flavor (regression)
        if json:
            r = requests.request(
                typ, self.apiroot + url, json=json, headers=headers, stream=stream
            )
        else:
            r = requests.request(
                typ, self.apiroot + url, data=data, headers=headers, stream=stream
            )
        if not self.quiet and not stream and not return_json:
            self.print_response(r)
        return self.check_response(typ, r, return_json=return_json, stream=stream)

    def post(self, url, data=None, json=None, headers=None, return_json=True):
        """
        Perform a POST request
        """
        return self.do_request(
            "post", url, data=data, json=json, headers=headers, return_json=return_json
        )

    def delete(self, url, data=None, json=None, headers=None, return_json=True):
        """
        Perform a DELETE request
        """
        return self.do_request(
            "delete",
            url,
            data=data,
            json=json,
            headers=headers,
            return_json=return_json,
        )

    def get(
        self, url, data=None, json=None, headers=None, return_json=True, stream=False
    ):
        """
        Perform a GET request
        """
        return self.do_request(
            "get",
            url,
            data=data,
            json=json,
            headers=headers,
            return_json=return_json,
            stream=stream,
        )

    def upload_model(self, model, flavor):
        """
        Given a model / pipeline, upload to an online-ml server.

        model = preprocessing.StandardScaler() | linear_model.LinearRegression()
        """
        self.check_flavor(flavor)
        r = self.post("/model/%s/" % flavor, data=dill.dumps(model))
        model_name = r["name"]
        logger.info("Created model %s" % model_name)
        return model_name

    def label(self, label, identifier, model_name):
        """
        Given a label we know for a prediction after the fact (which we can
        look up with an identifier from the server), use the label endpoint
        to update the model metrics and call learn one. Note that the
        model_name is not technically required (it's stored with the cached
        entry) however we require providing it to validate the association.
        If you have a label at the time of running predict you can use it
        then and should not need this endpoint. Also note that ground_truth
        of a prediction is synonymous with label here.
        """
        return self.post(
            "/label/",
            json={"model": model_name, "identifier": identifier, "label": label},
        )

    def learn(self, model_name, x, y=None):
        """
        Train on some data. You are required to provide at least the model
        name known to the server and x (data).

        for x, y in datasets.TrumpApproval().take(100):
            cli.train(x, y)
        """
        return self.post(
            "/learn/", json={"model": model_name, "features": x, "ground_truth": y}
        )

    def delete_model(self, model_name):
        """
        Delete a model by name
        """
        return self.delete("/model/", data={"model": model_name})

    def get_model_json(self, model_name):
        """
        Get a json respresentation of a model.
        """
        return self.get("/model/%s/" % model_name)

    def download_model(self, model_name, dest=None):
        """
        Download a model to file (e.g., pickle)

        with open("muffled-pancake-9439.pkl", "rb") as fd:
            content=pickle.load(fd)
        """
        # Get the model (this is a download of the pickled model with dill)
        r = self.get("/model/download/%s/" % model_name, return_json=False)

        # Default to pickle in PWD
        dest = dest or "%s.pkl" % model_name

        # Save to dest file
        with open(dest, "wb") as f:
            for chunk in r:
                f.write(chunk)
        return dest

    def predict(self, model_name, x):
        """
        Make a prediction
        """
        return self.post("/predict/", json={"model": model_name, "features": x})

    def models(self):
        """
        Get a listing of known models
        """
        return self.get("/models/")

    def stats(self, model_name):
        """
        Get stats for a model name
        """
        return self.get("/stats/", json={"model": model_name})

    def metrics(self, model_name):
        """
        Get metrics for a model name
        """
        return self.get("/metrics/", json={"model": model_name})

    def stream(self, url):
        """
        General stream endpoint
        """
        with self.get(url, stream=True, return_json=False) as r:
            for line in r.iter_lines():
                if line:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    yield line

    def stream_metrics(self):
        """
        Stream metrics
        """
        return self.stream("/stream/metrics/")

    def stream_events(self):
        """
        Stream events
        """
        return self.stream("/stream/events/")
