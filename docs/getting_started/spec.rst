.. _spec:

==============
River Api Spec
==============

Introduction
============

The **River API Specification** defines an API protocol 
to standardize the requests and responses for clients and servers related to 
interacting with a `river <https://riverml.xyz>`_ online machine learning server. Any server
that implements this specification can be used, for example, with 
the `riverapi client <https://github.com/vsoch/riverapi>`_. In other words,
the spec facilitates creating, learning, predicting, and otherwise interacting with models.


Definitions
===========

The following terms are used commonly in this document, and a list of definitions is provided for reference:

- **Server**: a service that provides the endpoints defined in this spec
- **Client**: an application or tool that interacts with a Server.

Notational Conventions
======================

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in `RFC 2119 <http://tools.ietf.org/html/rfc2119>`_ (Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, March 1997).

Conformance
===========

Currently, we don't have any tools to test conformance, and the requirements are outlined here. 

Determining Support
-------------------

To check whether or not the server implements the river api spec, the client SHOULD 
perform a ``GET`` request to the ``/api/`` (service info) endpoint.
If the response is ``200 OK``, then the server implements the spec. 
For example, given a url prefix of ``http://127.0.0.0:5000`` the client would issue a ``GET``
request to:


.. code-block:: console

    http://127.0.0.1:8000/api/


And see :ref:`spec-service-info` for more details on this request and response.
**Note** this prefix can be changed by the implementing server, and if this is the case,
the service info endpoint should send a field with a ``prefix`` or ``baseurl`` to direct
the client elsewhere.

Endpoint Requirements
---------------------

Servers conforming to the river api spec must provide the following endpoints: 

The most basic requirements for a server include endpoints:
 
1. **Service Info** (``GET /api/``) endpoint with a 200 response
2. **Create New Model** (``POST /api/model/<flavor>/``) to create a new model
3. **Learn** (``POST /api/learn/``) to learn from new data
4. **Predict** (``POST /api/predict/``) to get a prediction

Extra (but not required) endpoints include:

5. **Create New Named Model** (``POST /api/model/<flavor>/<name>/``) to create a new model
6. **Metrics**: (``GET /api/metrics/``) to get metrics for a model
7. **Stats**: (``GET /api/stats/``) to get stats for a model 
8. **Stream Metrics**: (``GET /api/stream/metrics/``) to stream any updated metrics
9. **Stream Events**: (``GET /api/stream/events/``) to stream any updated events
10. **Model As Json**: (``GET /api/model/``) to get a model as json
11. **Download Model**: (``GET /api/model/download/``) to download a model (pickle)
12.  **Delete Model**: (``DELETE /api/model/``) to delete a model and all related assets 


Response Details
----------------

Errors
^^^^^^

For all error responses, the server can (OPTIONAL) return in the body a nested structure of errors,
each including a message and error code. For example:

.. code-block:: console

    {
        "errors": [
            {
                "code": "<error code>",
                "message": "<error message>",
                "detail": ...
            },
            ...
        ]
    }

A simpler means (also okay) would be to provide a response with a message.

.. code-block:: console

    {"message": "<error message>"}


Currently we don't have a namespace for errors, but this can be developed if/when needed.
For now, the code is a standard server error code provided by the returned request.


Timestamps
^^^^^^^^^^

For all fields that return a timestamp, we are tentatively going to use the stringified
version of a `datetime.now()`, which looks like this:


.. code-block:: console

    2020-12-15 11:43:24.811860



Endpoint Details
================

.. _spec-service-info:

Generic Responses
-----------------

For any endpoint, a generic response can be sent to indicate the following:

- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented, or not found
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request (usually your fault)

Since these are generic and it would be redundant to repeat them below, we mention them once here.

404
^^^

In the case of a 404 response, it means that the server does not implement the spec.
The client should stop, and then respond appropriately (e.g., giving an error message or warning to the user).

.. code-block:: python

   {"status": "not implemented", "version": "1.0.0"}


503
^^^

If the service exists but is not running, a 503 is returned. The client should respond in the same
way as the 404, except perhaps trying later.

.. code-block:: python

    {"status": "service not available", "version": "1.0.0"}


400
^^^

A bad request is typically missing or malformed data, and the message back should include
an error/message about what is wrong.

.. code-block:: python

    {"message": "features are required to use this endpoint."}



Service Info
------------

``GET /api/``

This particular Endpoint exists to check the status of a running service. The client
should issue a ``GET`` request to this endpoint without any data, and the response should be any of the following:

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success (indicates running)
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: not implemented, or not found

As the initial entrypoint, this endpoint also can communicate back to the client that the prefix or
baseurl has changed by providing those parameters. We could also return a 302 response with a Location
header, if others want to change the spec to support this. For each of the above, 
the minimal response returned should include in the body a status message
and a version, both strings:

.. code-block:: python

    {"status": "running", "version": "1.0.0"}


200
^^^

A 200 is a successful response, meaning that the endpoint was found, and is running.

.. code-block:: python

    {"status": "running", "version": "1.0.0"}



Model Upload
------------

``POST /api/model/<flavor>/``
``POST /api/model/<flavor>/<name>/``

A post to this endpoint indicates that we want to upload a model. A flavor is required.
If we provide a name, it should be used instead of a randomly generated one. The data of the post
should be a binary dump (e.g., pickle) of the river model object.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success (indicates running)
- `503 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503>`_: service not available
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request


201
^^^

A 201 response indicates that the model was created, and it's name should be returned.

.. code-block:: python

    {"name": "persnickety-taco"}


Learn
-----

``POST /api/learn/``


The learn endpoint expects a POST with:

 - **model**: the model name intending to present learning data to
 - **features**: a dictionary of features (x)
 - **ground_truth**: the ground truth (y) typically one value for binary or regression

- `201 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/201>`_: success
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request


Predict
-------

``POST /api/predict/``

The predict endpoint expects a POST with:

 - **model**: the model name intending to present learning data to
 - **features**: a dictionary of features (x)

Optionally you can provide:

 - **identifier**: an identifier to remember the prediction to possibly label later

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `201 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/201>`_: success and identifier created
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request


If the server configuration is set to always produce an identifier, if you don't provide one
you'll get one back anyway. If the server is set to not produce an identifier by default, you
can still provide one to use later.


Label
-----

``POST /api/label/``

Often you might want to apply a label (ground truth) to a previously done prediction.
Given that you've obtained an identifier for the prediction, you can use the learn endpoint, which expects:

 - **model**: the model name intending to be found with the identifier cache
 - **label**: the newly learned label or ground truth (y)
 - **identifier**: the identifier obtained during the prediction
 
Note that although the model name is technically not required, we require it so the
server can check that the identifier in question corresponds to the model. If you are generating
your own identifiers, for example, you might accidentally switch or confuse them between
models. So this is a sanity check.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `400 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400>`_: bad request

Note that this endpoint basically performs the final steps of the ``/learn`` endpoint,
except you are providing an identifier to get the prediction from the cache. If you have
the ground truth at the time of generating a prediction, you can provide it directly to that
endpoint. In both cases, the identifier will be deleted after it's used.

200 or 201
^^^^^^^^^^

If the prediction is successful, you'll either get a 200 (success and an identifier was not created) or 201 (success and identifier was created) response,
along with the prediction and model name back. Given an identifier was created, you'll see it!

.. code-block:: python

    {"model": "punky-taco", "prediction": 1.0, "identifier": "166e872a-7110-4ef7-ad68-0e624cca906a"}

Without an identifier (200 response) you won't get one back:

.. code-block:: python

    {"model": "punky-taco", "prediction": 1.0}

Note that the prediction can either return a single prediction (binary) or a dictionary 
of predictions depending on the model type.


Metrics
-------

``GET /api/metrics/``

Get metrics for a model. You should send the model name as "model" as the only GET params.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success

The metrics returned back should be a dictionary of key value pairs of metrics appropriate
for the model type.


Stats
-----

``GET /api/stats/``

Get stats for a model. You should send the model name as "model" as the only GET params.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success

The stats returned back should be a dictionary with keys "learn" and "predict" and then
sub-dictionaries with key value pairs of stats appropriate for the model type.


Stream Metrics and Events
-------------------------

``GET /api/stream/metrics/``
``GET /api/stream/events/``

Get a stream of updated metrics/events as they are updated. These endpoints can "hang" open
as long as you need, and you should press Control+C when you want to stop it.
It's intended to be run as a kind of small service.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success

Streamed metrics can have the format of:

.. code-block:: console

    label: <value>
    
where label should be a string identifier followed by a colon, and value ideally
is a dictionary that can be parsed further.

Model as Json
-------------

``GET /api/model/``

This GET request should include one GET parameter, "model" as the model name to retrieve.
A json representation of the model is returned, which typically tries to unwrap a model
object and turn into formats that can be serialized to json.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success


Download Model
--------------

``GET /api/model/download/``

A request to this endpoint with a GET parameter "model" as the model name should
return a response you can stream to file, and this is the pickled model.

- `200 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200>`_: success
- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: model not found

Delete Model
------------

``DELETE /api/model/``

A DELETE request to this endpoint with a GET parameter "model" as the model name
should delete the model, and all associated artifacts. Note that this cannot be undone.

- `204 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/204>`_: successful delete
- `404 <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404>`_: model not found


Authentication
==============

Although authentication is not officially part of the spec, we encourage the implementation
to provide it to secure a server. The typical flow is the following:

1. A particular set of endpoints are protected with authentication. They look for an Authentication header in the request.
2. If not found, a 403 response is returned with a ``Www-Authenticate`` header that includes a realm to ping with basic credentials.
3. basic credentials (e.g., username and token password) are base64 encoded in the format ``<username>:<password>`` and send with the Authorization header back to the endpoint specified as the realm.
4. The server decodes the credentials, verifies the account, and sends back a self-expiring jwt (json web token)
5. The client adds the token to an Authorization bearer token header and retries the request. It should succeed.

